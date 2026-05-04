from keyboards.reply import MAIN_KB
"""
handlers/hobby.py — /hobby — напомнить про хобби
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo
import json

router = Router()

@router.message(Command("hobby"))
async def cmd_hobby(message: Message):
    user = await UserRepo.get_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return
    
    hobbies = user.get("hobbies", [])
    if not hobbies:
        await message.answer("Ты не рассказала о своих хобби. Пройди /start чтобы заполнить профиль.")
        return
    
    text = "🎨 *Твои увлечения:*\n\n"
    for h in hobbies:
        text += f"• {h.get('name', '—')}\n"
    text += "\nВыдели сегодня 20 минут на то что нравится! 💫"
    
    await message.answer(text, parse_mode="Markdown")
