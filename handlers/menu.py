from keyboards.reply import MAIN_KB
"""
handlers/menu.py — /menu — меню на сегодня/неделю
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo, MealRepo
from services.gemini import ask
from app_config.prompts import MENU_PROMPT, MENU_SYSTEM
from datetime import date, timedelta
import json

router = Router()

@router.message(F.text == "🍽 Меню")
@router.message(Command("menu"))
async def cmd_menu(message: Message):
    user = await UserRepo.get_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала давай познакомимся! Напиши /start")
        return
    
    await message.answer("🍽 Составляю меню...")
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    prompt = MENU_PROMPT.format(
        days=7,
        goal=user.get("goals", [{}])[0].get("type", "здоровье") if user.get("goals") else "здоровье",
        weight=user.get("weight", 60),
        height=user.get("height", 165),
        activity=user.get("activity", "умеренная"),
        budget=(user.get("food_preferences", {}) or {}).get("budget", "средний"),
        loved=", ".join(json.loads((user.get("food_preferences", {}) or {}).get("loved", "[]") or "[]")),
        hated=", ".join(json.loads((user.get("food_preferences", {}) or {}).get("hated", "[]") or "[]")),
        allergies=user.get("health_notes", {}).get("allergies", "нет") if isinstance(user.get("health_notes"), dict) else "нет",
        week_start=week_start.isoformat()
    )
    
    response = await ask(prompt, MENU_SYSTEM)
    
    try:
        clean = response.strip()
        if "```" in clean:
            clean = clean.split("```")[1].replace("json", "").strip()
        data = json.loads(clean)
        
        await MealRepo.save_week(user["id"], week_start.isoformat(), data["meals"])
        
        # Показываем меню
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        text = f"🍽 *Меню на неделю* ({week_start.day}.{week_start.month})\n\n"
        
        for day in range(1, 8):
            day_meals = [m for m in data["meals"] if m["day"] == day]
            if day_meals:
                text += f"*{days[day-1]}*: "
                text += " → ".join(m["dish"] for m in day_meals)
                text += f" (~{sum(m['calories'] for m in day_meals):.0f} ккал)\n"
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception:
        await message.answer("❌ Не получилось составить меню. Попробуй позже.")
