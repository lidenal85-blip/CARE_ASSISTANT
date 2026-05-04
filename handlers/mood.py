from keyboards.reply import MAIN_KB
"""
handlers/mood.py — /mood — записать настроение
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo, MoodRepo

router = Router()

@router.message(Command("mood"))
async def cmd_mood(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используй: /mood 7 (от 1 до 10)\nМожно с комментарием: /mood 8 потому что солнце!")
        return
    
    args = parts[1].split(maxsplit=1)
    try:
        score = int(args[0])
        if score < 1 or score > 10:
            raise ValueError
    except ValueError:
        await message.answer("Оценка от 1 до 10. Например: /mood 7")
        return
    
    note = args[1] if len(args) > 1 else ""
    await MoodRepo.add(user["id"], score, note)
    
    emoji = "😍" if score >= 8 else "😊" if score >= 6 else "😐" if score >= 4 else "😔"
    await message.answer(f"{emoji} Настроение {score}/10 записано!")
