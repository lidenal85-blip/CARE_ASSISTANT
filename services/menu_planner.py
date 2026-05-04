"""
services/menu_planner.py — генерация меню (Gemini + валидация)
"""
import json
from datetime import date, timedelta
from services.gemini import ask
from app_config.prompts import MENU_PROMPT, MENU_SYSTEM
from db.repository import UserRepo, MealRepo

async def generate_weekly_menu(telegram_id: int) -> dict | None:
    """Генерирует меню на неделю и сохраняет в БД."""
    user = await UserRepo.get_profile(telegram_id)
    if not user:
        return None
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    prompt = MENU_PROMPT.format(
        days=7,
        goal=user.get("goals", [{}])[0].get("type", "здоровье") if user.get("goals") else "здоровье",
        weight=user.get("weight", 60),
        height=user.get("height", 165),
        activity=user.get("activity", "умеренная"),
        budget=(user.get("food_preferences", {}) or {}).get("budget", "средний"),
        loved=", ".join(user.get("food_preferences", {}).get("loved", "[]") or []),
        hated=", ".join(user.get("food_preferences", {}).get("hated", "[]") or []),
        allergies=user.get("health_notes", {}).get("allergies", "нет") if isinstance(user.get("health_notes"), dict) else "нет",
        week_start=week_start.isoformat()
    )
    
    response = await ask(prompt, MENU_SYSTEM)
    
    try:
        clean = response.strip()
        if "```" in clean:
            clean = clean.split("```")[1].replace("json", "").strip()
        data = json.loads(clean)
        
        # Валидация: проверяем что есть все поля
        for meal in data["meals"]:
            assert "day" in meal
            assert "meal_type" in meal
            assert "dish" in meal
            assert meal.get("calories", 0) > 0
        
        # Сохраняем
        await MealRepo.save_week(user["id"], week_start.isoformat(), data["meals"])
        return data
        
    except Exception:
        return None
