from keyboards.reply import MAIN_KB
"""
handlers/water.py — /water — записать стакан воды
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo, WaterRepo

router = Router()

@router.message(Command("water"))
async def cmd_water(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return
    
    await WaterRepo.add(user["id"])
    total = await WaterRepo.today_ml(user["id"])
    glasses = total // 250
    
    await message.answer(f"💧 +250 мл! Сегодня: {total} мл ({glasses} ст.)")
