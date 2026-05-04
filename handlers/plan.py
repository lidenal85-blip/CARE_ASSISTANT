from keyboards.reply import MAIN_KB
"""
handlers/plan.py — /plan — план на сегодня
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo
import json
from datetime import date

router = Router()

@router.message(Command("plan"))
async def cmd_plan(message: Message):
    user = await UserRepo.get_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return
    
    today = date.today()
    weekday = today.weekday()  # 0=пн, 6=вс
    days_ru = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    
    text = f"📋 *План на {days_ru[weekday]}*\n\n"
    
    if user.get("wake_up"):
        text += f"⏰ Подъём: {user['wake_up']}\n"
    if user.get("sleep_time"):
        text += f"🌙 Отбой: {user['sleep_time']}\n\n"
    
    # Хобби
    if user.get("hobbies"):
        text += "🎨 *Хобби:*\n"
        for h in user["hobbies"]:
            text += f"  • {h.get('name', '—')}\n"
    
    # Дела по дому
    if user.get("chores"):
        day_map = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "вс"}
        for chore in user["chores"]:
            if chore.get("day_of_week") == weekday:
                text += f"\n🏠 {chore['name']}"
    
    await message.answer(text, parse_mode="Markdown")
