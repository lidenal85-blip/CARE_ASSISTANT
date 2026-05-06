"""
DOCTOR SYSTEM v11 — автономный агент лечения Python-проектов
SmartPatcher (AST) + Gemini (LLM) = двухуровневое лечение
"""
import ast, sys, os, shutil, time, httpx
from pathlib import Path
from datetime import datetime
from .smart_patcher import SmartPatcher
from leviathan.core import get_pool
from .knowledge_base import KnowledgeBase

G='\033[32m'; R='\033[31m'; Y='\033[33m'; C='\033[36m'; B='\033[1m'; X='\033[0m'

class DoctorSystem:
    def __init__(self, project_root: Path | str):
        self.ROOT = Path(project_root)
        self.LOG = self.ROOT / "data" / "doctor.log"
        self.LOG.parent.mkdir(parents=True, exist_ok=True)
        self.key = self._find_key()
        self.attempt = 0
        self.failed_files = {}
        self.patcher = SmartPatcher(str(self.ROOT))
        self.kb = KnowledgeBase()  # ← SmartPatcher!
    
    def _find_key(self):
        for i in range(1, 15):
            k = os.getenv(f"GEMINI_K{i}", "")
            if k and len(k) > 10:
                return k
        return None
    
    def log(self, msg, color=""):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  {color}[{ts}] {msg}{X}")
        with open(self.LOG, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    
    
    def check_runtime_errors(self):
        """Проверяет логи бота на рантайм-ошибки"""
        bot_log = self.ROOT / "data" / "bot.log"
        if not bot_log.exists():
            return []
        
        errors = []
        try:
            lines = bot_log.read_text().split("\n")
            for line in lines[-100:]:  # последние 100 строк
                if "ERROR" in line or "Traceback" in line:
                    errors.append(line.strip()[:200])
        except Exception:
            pass
        
        if errors:
            self.log(f"📋 Найдено {len(errors)} ошибок в логах бота", Y)
            for e in errors[-5:]:  # последние 5
                self.log(f"   {e}", R)
        
        return errors


    def scan_all(self):
        """Сканирует все .py файлы через AST"""
        errors = []
        for f in sorted(self.ROOT.rglob("*.py")):
            if any(x in str(f) for x in ['__pycache__', 'sandbox', 'backups', '.egg-info', 'leviathan-core']):
                continue
            try:
                ast.parse(f.read_text())
            except SyntaxError as e:
                errors.append({
                    "file": f,
                    "error": e,
                    "type": self._classify_error(e)
                })
        return errors
    
    def _classify_error(self, error: SyntaxError) -> str:
        """Классифицирует ошибку: patcher или gemini"""
        msg = error.msg.lower()
        # Ошибки которые патчер может исправить сам
        if any(x in msg for x in ['indentation', 'unexpected indent', 'expected an indented block']):
            return "indent"
        if any(x in msg for x in ['eof', 'unexpected eof', 'unterminated']):
            return "bracket"
        
        # Сложные ошибки — только Gemini
        return "complex"
    
    # ── Уровень 1: SmartPatcher (AST, быстро, без API) ──
    
    def heal_with_patcher(self, filepath: Path, error: SyntaxError, error_type: str) -> bool:
        """Пробует исправить ошибку через SmartPatcher"""
        self.log(f"🔧 Патчер: {filepath.name}:{error.lineno} ({error_type})...", C)
        return self.patcher.heal(filepath, error, error_type)
    def heal_with_gemini(self, filepath: Path, error: SyntaxError) -> str | None:
        """Отправляет файл в Gemini для исправления"""
        content = filepath.read_text()
        prompt = f"""Fix the ONLY syntax error in this Python file.
Return ONLY the corrected file inside ```python ... ``` block.
Do NOT add comments. Do NOT change working code. Fix ONLY line {error.lineno}.

FILE: {filepath.name}
ERROR at line {error.lineno}: {error.msg}

=== FULL FILE ===
{content}
=== END ===

Return the complete fixed file:"""
        
        try:
            pool = get_pool()
            entry, provider = pool.get_best(prefer="gemini")
            resp = httpx.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                params={"key": entry.value},
                timeout=30,
            )
            if resp.status_code == 200:
                pool.report(entry, code=200, model="gemini-2.5-flash")
                result = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                if "```" in result:
                    result = result.split("```")[1]
                    if result.startswith("python"): result = result[6:]
                    result = result.strip()
                if result and result != content:
                    return result
        except Exception as e:
            try: pool.report(entry, code=500, model="gemini-2.5-flash")
            except: pass
            self.log(f"Gemini error: {e}", R)
        return None
    
    # ── Главный цикл лечения ─────────────────────────
    
    def heal_all(self, errors: list) -> int:
        """
        Двухуровневое лечение:
        1. SmartPatcher (AST) — быстро, без API
        2. Gemini (LLM) — только для сложных случаев
        """
        fixed = 0
        
        for e in errors:
            f = e["file"]
            f_str = str(f)
            self.failed_files[f_str] = self.failed_files.get(f_str, 0) + 1
            
            if self.failed_files[f_str] > 3:
                self.log(f"⛔ {f.name} — пропускаем (3 попытки)", R)
                continue
            
            err = e["error"]
            err_type = e["type"]
            
            # Бэкап
            bkp_dir = self.ROOT / "data" / "backups"
            bkp_dir.mkdir(parents=True, exist_ok=True)
            bkp = bkp_dir / f"{f.name}.{datetime.now():%Y%m%d_%H%M%S}.bak"
            shutil.copy2(f, bkp)
            
            # ── Уровень 1: Патчер ──
            if self.heal_with_patcher(f, err, err_type):
                fixed += 1
                continue
            
            # ── Уровень 2: Gemini ──
            self.log(f"🤖 Gemini: {f.name}:{err.lineno}...", Y)
            fixed_content = self.heal_with_gemini(f, err)
            
            if fixed_content:
                f.write_text(fixed_content)
                try:
                    ast.parse(fixed_content)
                    self.log(f"✅ Gemini исправил: {f.name}", G)
                    self.kb.log_case(err.msg, f.name, err.lineno, fixed_content[:200])
                    fixed += 1
                    continue
                except SyntaxError:
                    shutil.copy2(bkp, f)
                    self.log(f"❌ Gemini не помог: {f.name}", R)
            else:
                self.log(f"❌ Gemini недоступен: {f.name}", R)
        
        return fixed
    
    
    def learn_from_gemini(self, error_msg: str, fix_strategy: str):
        """Сохраняет успешное исправление от Gemini в JSON-правила"""
        import json
        config_path = self.ROOT / "config" / "patcher_rules.json"
        if not config_path.exists():
            return
        
        rules = json.loads(config_path.read_text())
        existing = rules.get("rules", [])
        
        # Проверяем — может такое правило уже есть
        for rule in existing:
            if rule.get("error_pattern") and rule["error_pattern"] in error_msg:
                return  # уже знаем как чинить
        
        # Извлекаем ключевой паттерн из ошибки
        # Примеры: "TypeError: can't multiply..." → "can't multiply sequence by non-int"
        #          "SyntaxError: '(' was never closed" → "was never closed"
        import re
        pattern = error_msg[:100]
        # Ищем наиболее специфичную часть ошибки
        match = re.search(r"'(.*?)'", error_msg)  # текст в кавычках
        if match:
            pattern = match.group(0)  # вместе с кавычками
        elif ':' in error_msg:
            pattern = error_msg.split(':')[-1].strip()[:80]
        
        # Создаём новое правило
        new_rule = {
            "name": f"gemini_learned_{len(existing)+1}",
            "error_pattern": pattern,
            "error_type": "runtime" if "Error" in error_msg else "syntax" if "SyntaxError" in error_msg else "complex",
            "priority": len(existing) + 1,
            "action": "gemini_suggested",
            "description": f"Gemini fix: {fix_strategy[:100]}",
            "learned_at": str(__import__('datetime').datetime.now().isoformat()),
            "times_seen": 1
        }
        
        existing.append(new_rule)
        config_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2))
        self.log(f"🎓 Новое правило от Gemini: {new_rule['name']}", G)

    def run_once(self):
        self.attempt += 1
        self.log(f"🔄 ЦИКЛ #{self.attempt}", C)
        errors = self.scan_all()
        
        if not errors:
            self.log("✅ Ошибок нет", G)
            return True
        
        self.log(f"🐛 Найдено ошибок: {len(errors)}", Y)
        for e in errors:
            self.log(f"   {e['file'].name}:{e['error'].lineno}: {e['error'].msg} [{e['type']}]", R)
        
        fixed = self.heal_all(errors)
        self.log(f"💊 Вылечено: {fixed}/{len(errors)} (Патчер+Gemini)", G if fixed == len(errors) else Y)
        return fixed == len(errors)
    
    def watch(self, interval: int = 30):
        """Бесконечный цикл наблюдения"""
        self.log("👁 АВТОПИЛОТ v11 (Патчер+Gemini)", C)
        self.log(f"   Интервал: {interval}с", "")
        
        while True:
            try:
                errors = self.scan_all()
                runtime = self.check_runtime_errors()
                if errors or runtime:
                    self.log(f"⚠ Ошибок: {len(errors)}", Y)
                    self.run_once()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.log("⏹ ОСТАНОВЛЕН", Y)
                break
            except Exception as e:
                self.log(f"💥 Сбой: {e}", R)
                time.sleep(10)
