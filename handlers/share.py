"""
handlers/share.py — поделиться списком покупок
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from db.repository import UserRepo, ShoppingRepo
from datetime import date, timedelta

router = Router()

@router.message(Command("share"))
async def cmd_share(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    items = await ShoppingRepo.get_week(user["id"], week_start.isoformat())
    
    if not items:
        await message.answer("Список покупок пуст.")
        return
    
    text = f"🛒 *Список покупок {user.get('name', '')}* ({week_start.day}.{week_start.month})\n\n"
    for item in items:
        text += f"• {item['item']}\n"
    text += f"\n_Отправлено через Забота+_"
    
    await message.answer(
        "📤 Отправь это сообщение тому кто пойдёт в магазин:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="📤 Переслать список",
                switch_inline_query=f"🛒 Список покупок: {', '.join(i['item'] for i in items[:10])}"
            )
        ]])
    )
