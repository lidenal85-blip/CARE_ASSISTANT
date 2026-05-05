"""
engine/doctor_monitor.py — Автономный сторож бота 24/7

Поведение:
- Каждые 3 часа: «Бот жив ✅» (если без ошибок)
- При ошибке: мгновенное сообщение с анализом от Gemini
- Кнопки: Исправить / Откатить / Логи / Редеплоить
- Все ошибки → база знаний → обучение патчера
"""
import asyncio, httpx, os, json, re, hashlib
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════════════════════
class DoctorMonitor:
    def __init__(self, bot_token: str, admin_id: int):
        self.token = bot_token
        self.admin = admin_id
        self.api = f"https://api.telegram.org/bot{bot_token}"
        self.last_report = None           # время последнего «бот жив»
        self.error_counts = {}            # хеш ошибки → количество
        self.kb_path = Path("data/doctor_knowledge.json")
        self.kb = self._load_kb()
    
    # ── База знаний патчера ─────────────────────────
    def _load_kb(self) -> dict:
        if self.kb_path.exists():
            return json.loads(self.kb_path.read_text())
        return {"errors": {}, "rules": [], "stats": {"total": 0, "auto_fixed": 0, "gemini_fixed": 0}}
    
    def _save_kb(self):
        self.kb_path.write_text(json.dumps(self.kb, ensure_ascii=False, indent=2))
    
    def _error_hash(self, error_msg: str) -> str:
        return hashlib.md5(error_msg.encode()).hexdigest()[:10]
    
    def learn_from_error(self, error: dict, fix: str = None):
        """Сохраняет ошибку в базу знаний. При 3+ → правило для патчера."""
        h = self._error_hash(str(error.get("lines", [])[:3]))
        
        if h not in self.kb["errors"]:
            self.kb["errors"][h] = {
                "pattern": error.get("error_type", "unknown"),
                "sample": str(error.get("lines", [])[:5]),
                "count": 0,
                "fix": fix,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
            }
        
        self.kb["errors"][h]["count"] += 1
        self.kb["errors"][h]["last_seen"] = datetime.now().isoformat()
        self.kb["stats"]["total"] += 1
        
        # Обучение патчера: 3+ одинаковых → правило
        if self.kb["errors"][h]["count"] >= 3 and fix:
            rule = {
                "pattern": self.kb["errors"][h]["pattern"],
                "fix_strategy": fix[:300],
                "based_on": h,
                "promoted_at": datetime.now().isoformat(),
            }
            if not any(r["based_on"] == h for r in self.kb["rules"]):
                self.kb["rules"].append(rule)
                self.kb["stats"]["gemini_fixed"] += 1
        
        self._save_kb()
    
    # ── Telegram-сообщения ──────────────────────────
    async def _send(self, text: str, keyboard: dict = None):
        data = {"chat_id": self.admin, "text": text, "parse_mode": "Markdown"}
        if keyboard:
            data["reply_markup"] = keyboard
        async with httpx.AsyncClient() as c:
            await c.post(f"{self.api}/sendMessage", json=data)
    
    def _keyboard(self, error_hash: str = None):
        kb = {"inline_keyboard": [
            [
                {"text": "🔧 Исправить", "callback_data": f"fix_{error_hash}" if error_hash else "fix"},
                {"text": "⏪ Откатить", "callback_data": f"rollback_{error_hash}" if error_hash else "rollback"},
            ],
            [
                {"text": "📋 Логи", "url": "https://railway.com/project/56c99c9a-b43b-46f9-a493-362ff5dc05b0/service/b234abea-e8a3-404e-a904-6570b6aae400/logs"},
                {"text": "🔄 Редеплоить", "callback_data": "redeploy"},
            ]
        ]}
        return kb
    
    # ── Проверка здоровья ───────────────────────────
    async def check_health(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self.api}/getMe")
                if r.status_code == 200 and r.json().get("ok"):
                    return {"alive": True, "bot": r.json()["result"]["username"]}
        except:
            pass
        return {"alive": False}
    
    # ── Анализ через Gemini ─────────────────────────
    async def analyze_with_gemini(self, error: dict) -> str:
        from services.gemini import ask
        prompt = f"""Ты — senior Python-разработчик. Проанализируй ошибку и дай конкретное исправление.

ОШИБКА:
{' '.join(error.get('lines', [])[:30])}

Формат ответа (строго):
ФАЙЛ: путь/к/файлу.py
ПРИЧИНА: кратко
ИСПРАВЛЕНИЕ: конкретный код
ДИФФ: было → стало"""
        try:
            return await ask(prompt, "Ты — эксперт по Python/aiogram. Отвечай строго по формату.")
        except:
            return "Gemini временно недоступен"
    
    # ── Главный цикл ────────────────────────────────
    async def run_cycle(self):
        health = await self.check_health()
        now = datetime.now()
        
        if not health["alive"]:
            await self._send(
                f"🚨 *БОТ УПАЛ!*\nВремя: {now:%H:%M:%S}",
                self._keyboard()
            )
            return
        
        # «Бот жив» раз в 3 часа
        if not self.last_report or (now - self.last_report) > timedelta(hours=3):
            self.last_report = now
            errors_today = sum(1 for e in self.kb["errors"].values() if e["last_seen"] > (now - timedelta(days=1)).isoformat())
            rules_count = len(self.kb["rules"])
            
            await self._send(
                f"🟢 *Бот жив* | @{health['bot']}\n\n"
                f"📊 Статистика:\n"
                f"• Ошибок сегодня: {errors_today}\n"
                f"• Правил в базе: {rules_count}\n"
                f"• Всего ошибок: {self.kb['stats']['total']}\n"
                f"• Автоисправлено: {self.kb['stats']['auto_fixed']}\n\n"
                f"_Следующий отчёт в {((now + timedelta(hours=3)).strftime('%H:%M'))}_"
            )
    
    async def report_error(self, error: dict):
        """Сообщает об ошибке + анализ Gemini + сохраняет в базу"""
        analysis = await self.analyze_with_gemini(error)
        self.learn_from_error(error, analysis)
        
        error_type = error.get("error_type", "Неизвестная")
        h = self._error_hash(str(error.get("lines", [])[:3]))
        
        await self._send(
            f"🔴 *Ошибка: {error_type}*\n\n"
            f"```\n{' '.join(error.get('lines', [])[:10])}\n```\n\n"
            f"🧠 *Анализ Gemini:*\n{analysis[:500]}\n\n"
            f"📚 Похожих ошибок: {self.kb['errors'].get(h, {}).get('count', 1)}",
            self._keyboard(h)
        )

async def main():
    token = os.getenv("BOT_TOKEN", "")
    admin_id = 0  # ← ЗАМЕНИ НА СВОЙ TELEGRAM ID!!!  # ← замени на свой Telegram ID
    
    if not token:
        print("❌ BOT_TOKEN не установлен")
        return
    
    monitor = DoctorMonitor(token, admin_id)
    await monitor._send("🩺 *Доктор на связи*\nМониторю бота 24/7.\nОшибки → мгновенно.\nСтатус → раз в 3 часа.")
    
    while True:
        try:
            await monitor.run_cycle()
        except Exception as e:
            print(f"[Doctor] Ошибка цикла: {e}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
