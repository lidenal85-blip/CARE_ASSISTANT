from keyboards.reply import MAIN_KB
"""
handlers/profile.py — /profile — что бот знает о пользователе
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo
import json

router = Router()

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await UserRepo.get_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return
    
    text = f"🌸 *{user.get('name', 'Подруга')}*\n\n"
    text += f"🎯 Цель: {user.get('goals', [{}])[0].get('type', '—') if user.get('goals') else '—'}\n"
    text += f"⚖️ Вес: {user.get('weight', '—')} кг | Рост: {user.get('height', '—')} см\n"
    text += f"⏰ {user.get('wake_up', '—')} → {user.get('sleep_time', '—')}\n"
    text += f"💪 Активность: {user.get('activity', '—')}\n"
    text += f"😰 Стресс: {user.get('stress', '—')}\n"
    
    await message.answer(text, parse_mode="Markdown")
