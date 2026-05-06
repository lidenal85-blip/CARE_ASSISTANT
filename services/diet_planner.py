"""
services/diet_planner.py — Индивидуальный план питания (полный цикл)
Собирает данные → считает КБЖУ → генерирует план → отдаёт PDF
"""
import json, httpx
from datetime import date, timedelta
from services.gemini import ask, _safe_food_prefs, _parse_gemini_json

DIET_SYSTEM = """Ты — профессиональный диетолог-нутрициолог с 10-летним опытом.
Составляешь ИНДИВИДУАЛЬНЫЙ план питания на основе полных данных о человеке.
Учитываешь: цели, вес, рост, активность, аллергии, предпочтения, бюджет, образ жизни.
Никаких общих рекомендаций — только персональный подход."""

DIET_PROMPT = """Составь персональный план питания.

=== ПОЛНЫЕ ДАННЫЕ ===
Имя: {name}
Возраст: {age}
Пол: {gender}
Вес: {weight} кг
Рост: {height} см
Цель: {goal}
Активность: {activity}
Стресс: {stress}
Сон: {sleep_hours}
Бюджет: {budget}
Любит: {loved}
Не любит: {hated}
Аллергии: {allergies}
Работа: {work}
Хобби: {hobbies}
Бытовые дела: {chores}

=== ЗАДАНИЕ ===
1. Рассчитай BMR (базальный метаболизм) и TDEE (дневной расход калорий)
2. Сделай расчёт под цель: дефицит/профицит/поддержание
3. Составь меню на 7 дней (завтрак, обед, ужин, перекус)
4. Дай список продуктов на неделю с категориями
5. Напиши 3 ключевых правила для этой цели
6. Предупреди о типичных ошибках

Верни JSON строго по схеме:
{{
  "calculations": {{
    "bmr": 1450,
    "tdee": 1850,
    "target_calories": 1550,
    "target_protein": 95,
    "target_fat": 45,
    "target_carbs": 170
  }},
  "rules": [
    "Правило 1: ...",
    "Правило 2: ...",
    "Правило 3: ..."
  ],
  "warnings": [
    "Ошибка 1: не пропускать завтрак потому что...",
    "Ошибка 2: ..."
  ],
  "week_start": "{week_start}",
  "meals": [
    {{"day": 1, "meal_type": "breakfast", "dish": "...", "calories": 350, "protein": 20, "fat": 10, "carbs": 40, "time": "08:00", "notes": "почему это блюдо"}},
    ...
  ],
  "shopping": [
    {{"item": "Куриная грудка", "category": "Мясо", "amount": "1 кг", "week_total": "на 4 дня"}},
    ...
  ]
}}

Только JSON. Калории должны совпадать с target. Это важно."""


async def create_individual_diet(telegram_id: int, user_profile: dict) -> dict | None:
    """Создаёт полный индивидуальный план питания."""
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    prompt = DIET_PROMPT.format(
        name=user_profile.get("name", "Подруга"),
        age=user_profile.get("age", "—"),
        gender=user_profile.get("gender", "—"),
        weight=user_profile.get("weight", "—"),
        height=user_profile.get("height", "—"),
        goal=user_profile.get("goals", [{}])[0].get("type", "поддержание") if user_profile.get("goals") else "поддержание",
        activity=user_profile.get("activity", "умеренная"),
        stress=user_profile.get("stress", "средний"),
        sleep_hours=user_profile.get("sleep_hours", "7-8"),
        _fp = _safe_food_prefs(user_profile)
        budget=_fp.get("budget", "средний"),
        loved=", ".join(json.loads(_fp.get("loved", "[]") or "[]")),
        hated=", ".join(json.loads(_fp.get("hated", "[]") or "[]")),
        allergies=user_profile.get("health_notes", "нет"),
        work=user_profile.get("work", "—"),
        hobbies=", ".join(h.get("name", "") for h in user_profile.get("hobbies", [])) if user_profile.get("hobbies") else "—",
        chores=", ".join(f"{c.get('name', '')} ({c.get('day_of_week', '')})" for c in user_profile.get("chores", [])) if user_profile.get("chores") else "—",
        week_start=week_start.isoformat()
    )
    
    response = await ask(prompt, DIET_SYSTEM)
    
    try:
        data = _parse_gemini_json(response)
        
        # Валидация
        assert data.get("calculations", {}).get("bmr", 0) > 0
        assert len(data.get("meals", [])) >= 20  # минимум 20 приёмов (7 дней × 3+)
        assert len(data.get("rules", [])) >= 3
        assert len(data.get("shopping", [])) >= 10
        
        return data
        
    except Exception as e:
        print(f"Diet planner error: {e}")
        return None



def sync_shopping_list(menu_data: dict) -> list:
    """Агрегирует ингредиенты из меню в список покупок"""
    ingredients = []
    for meal in menu_data.get("meals", []):
        dish = meal.get("dish", "")
        # Извлекаем продукты из названия блюда
        dish = dish.replace("→", ",").replace("с", ",").replace(" и ", ",")
        parts = [p.strip() for p in dish.split(",") if p.strip() and len(p.strip()) > 3]
        ingredients.extend(parts)
    # Убираем дубли и не-продукты
    stop_words = ("ккал", "запеченная", "тушеная", "большая", "порция", "горсть", "шт", "цельнозерновой")
    unique = list(set(i for i in ingredients if not i.lower().startswith(stop_words)))
    return [{"item": i[:50], "category": "прочее"} for i in unique[:30]]

def format_diet_message(data: dict) -> str:
    """Форматирует план питания в читаемое сообщение."""
    calc = data["calculations"]
    
    text = "🥗 *ТВОЙ ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ*\n\n"
    
    # Расчёты
    text += "📊 *Расчёты*\n"
    text += f"• Базовый метаболизм (BMR): {calc['bmr']} ккал\n"
    text += f"• Дневной расход (TDEE): {calc['tdee']} ккал\n"
    text += f"• Целевые калории: *{calc['target_calories']} ккал*\n"
    text += f"• Белки: {calc['target_protein']}г | Жиры: {calc['target_fat']}г | Углеводы: {calc['target_carbs']}г\n\n"
    
    # Правила
    text += "📋 *3 ключевых правила*\n"
    for i, rule in enumerate(data["rules"], 1):
        text += f"{i}. {rule}\n"
    
    # Предупреждения
    text += "\n⚠️ *Типичные ошибки*\n"
    for i, warning in enumerate(data["warnings"], 1):
        text += f"{i}. {warning}\n"
    
    # Меню (первые 3 дня)
    text += "\n🍽 *Меню (первые 3 дня)*\n"
    for day in range(1, 4):
        day_meals = [m for m in data["meals"] if m["day"] == day]
        days = ["Пн", "Вт", "Ср"]
        text += f"\n*{days[day-1]}* ({sum(m['calories'] for m in day_meals):.0f} ккал)\n"
        for meal in day_meals:
            text += f"  {meal['time']} — {meal['dish']} ({meal['calories']:.0f} ккал)\n"
    
    text += f"\n_Полный список на 7 дней и список продуктов — в следующем сообщении_"
    
    return text
