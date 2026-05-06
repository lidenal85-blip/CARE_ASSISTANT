"""
engine/menu_engine.py — Двухуровневый движок меню

Уровень 1: JSON-кэш (быстро, без API)
Уровень 2: Gemini (медленно, пополняет кэш)

При каждом запросе:
  1. Ищем в JSON по хешу профиля
  2. Если нет → Gemini генерирует
  3. Сохраняем в JSON → в следующий раз мгновенно
"""
import json
import hashlib
from pathlib import Path
from datetime import date, timedelta
from services.gemini import ask, GeminiError

CONFIG_PATH = Path(__file__).parent.parent / "config" / "menus.json"

# ── Хеш профиля ──────────────────────────────────────

def profile_hash(profile: dict) -> str:
    """Уникальный ключ профиля: цель + вес + рост + активность + бюджет + любит/не любит"""
    key = (
        f"{profile.get('goal','')}|"
        f"{profile.get('weight',0):.0f}|"
        f"{profile.get('height',0):.0f}|"
        f"{profile.get('activity','')}|"
        f"{profile.get('budget','')}|"
        f"{sorted(profile.get('loved',[]))}|"
        f"{sorted(profile.get('hated',[]))}"
    )
    return hashlib.md5(key.encode()).hexdigest()[:12]

# ── Загрузка/сохранение JSON ────────────────────────

def load_cache() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_cache(data: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── Поиск в кэше ────────────────────────────────────

def find_in_cache(profile: dict) -> dict | None:
    """Ищет меню по хешу профиля"""
    h = profile_hash(profile)
    cache = load_cache()
    for item in cache["templates"]:
        if item.get("hash") == h:
            item["used"] = item.get("used", 0) + 1
            save_cache(cache)
            return item["menu"]
    return None

# ── Сохранение в кэш ────────────────────────────────

def save_to_cache(profile: dict, menu_data: dict):
    """Сохраняет сгенерированное меню в JSON"""
    h = profile_hash(profile)
    cache = load_cache()
    
    # Проверяем нет ли уже
    for item in cache["templates"]:
        if item.get("hash") == h:
            item["menu"] = menu_data
            item["updated"] = str(date.today())
            save_cache(cache)
            return
    
    cache["templates"].append({
        "hash": h,
        "profile": {
            "goal": profile.get("goal"),
            "weight": profile.get("weight"),
            "height": profile.get("height"),
            "activity": profile.get("activity"),
            "budget": profile.get("budget"),
        },
        "menu": menu_data,
        "used": 1,
        "created": str(date.today()),
        "updated": str(date.today()),
    })
    save_cache(cache)
    print(f"💾 Меню сохранено в JSON: {h}")

# ── Генерация через Gemini ──────────────────────────

MENU_SYSTEM = "Ты — диетолог. Составляешь меню на 7 дней."

MENU_PROMPT = """Составь меню на 7 дней (завтрак, обед, ужин, перекус).

Параметры:
- Цель: {goal}
- Вес: {weight} кг, Рост: {height} см
- Активность: {activity}
- Бюджет: {budget}
- Любит: {loved}
- Не любит: {hated}

Верни ТОЛЬКО JSON:
{{
  "meals": [
    {{"day": 1, "meal_type": "breakfast", "dish": "Овсянка с ягодами", "calories": 350, "protein": 12, "fat": 8, "carbs": 55}},
    ...
  ],
  "calculations": {{
    "bmr": 1450,
    "target_calories": 1550
  }}
}}
4 приёма в день. Только JSON."""

async def generate_via_gemini(profile: dict) -> dict | None:
    """Генерирует меню через Gemini API"""
    prompt = MENU_PROMPT.format(
        goal=profile.get("goal", "здоровье"),
        weight=profile.get("weight", 60),
        height=profile.get("height", 165),
        activity=profile.get("activity", "умеренная"),
        budget=profile.get("budget", "средний"),
        loved=", ".join(profile.get("loved", [])) or "без предпочтений",
        hated=", ".join(profile.get("hated", [])) or "без ограничений",
    )
    
    try:
        response = await ask(prompt, MENU_SYSTEM)
        clean = response.strip()
        if "```" in clean:
            clean = clean.split("```")[1].replace("json", "").strip()
        return json.loads(clean)
    except (GeminiError, json.JSONDecodeError) as e:
        print(f"Gemini error: {e}")
        return None

# ── Главный метод ───────────────────────────────────

async def get_or_create_menu(profile: dict) -> dict | None:
    """
    Двухуровневый доступ к меню:
    1. Ищем в JSON-кэше
    2. Если нет — генерируем через Gemini и сохраняем
    """
    # Уровень 1: кэш
    cached = find_in_cache(profile)
    if cached:
        print(f"🎯 JSON-кэш: {profile_hash(profile)}")
        return cached
    
    # Уровень 2: Gemini
    print(f"🤖 Gemini: {profile_hash(profile)}")
    menu = await generate_via_gemini(profile)
    
    if menu:
        save_to_cache(profile, menu)
    
    return menu

# ── Форматирование ──────────────────────────────────

def format_menu(data: dict) -> str:
    """Форматирует меню для отправки пользователю"""
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    text = "🍽 *Меню на неделю*\n\n"
    
    for day in range(1, 8):
        day_meals = [m for m in data.get("meals", []) if m.get("day") == day]
        if day_meals:
            cals = sum(m.get("calories", 0) for m in day_meals)
            text += f"*{days[day-1]}*: "
            text += " → ".join(m.get("dish", "?") for m in day_meals)
            text += f" (~{cals:.0f} ккал)\n"
    
    if data.get("calculations"):
        c = data["calculations"]
        text += f"\n📊 BMR: {c.get('bmr', '—')} ккал | Цель: {c.get('target_calories', '—')} ккал"
    
    return text

# ── Статистика ──────────────────────────────────────

def cache_stats() -> dict:
    cache = load_cache()
    return {
        "total": len(cache["templates"]),
        "by_goal": {},

}