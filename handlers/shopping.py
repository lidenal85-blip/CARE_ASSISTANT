from keyboards.reply import MAIN_KB
"""
handlers/shopping.py — /buy — список покупок
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo, ShoppingRepo
from datetime import date, timedelta

router = Router()

async def cmd_shopping(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    items = await ShoppingRepo.get_week(user["id"], week_start.isoformat())
    
    if not items:
        await message.answer("🛒 Список покупок пуст. Сначала создай меню через /menu")
        return
    
    by_category = {}
    for item in items:
        cat = item.get("category", "прочее")
        by_category.setdefault(cat, []).append(item["item"])
    
    text = f"🛒 *Список покупок* ({week_start.day}.{week_start.month})\n\n"
    for cat, items in by_category.items():
        text += f"*{cat}*: {', '.join(items)}\n"
    
    await message.answer(text, parse_mode="Markdown")
