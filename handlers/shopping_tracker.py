"""
handlers/shopping_tracker.py — отслеживание реальных покупок
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo, ShoppingRepo
from keyboards.reply import MAIN_KB
import json
from datetime import date, timedelta, datetime
from db.connection import get_db

router = Router()
_last_shopping_time = {}

@router.message(F.text == "🛒 Покупки")
@router.message(Command("buy"))
async def cmd_shopping(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Сначала /start", reply_markup=MAIN_KB)
        return
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    _last_shopping_time[message.from_user.id] = datetime.now()
    
    items = await ShoppingRepo.get_week(user["id"], week_start.isoformat())
    
    if not items:
        await message.answer(
            "🛒 Список покупок пуст. Сначала создай меню через 🥗 Диета.",
            reply_markup=MAIN_KB
        )
        return
    
    by_category = {}
    for item in items:
        cat = item.get("category", "прочее")
        by_category.setdefault(cat, []).append(item)
    
    text = f"🛒 *Список покупок* ({week_start.day}.{week_start.month})\n\n"
    
    for cat, cat_items in by_category.items():
        text += f"*{cat}*\n"
        for item in cat_items:
            bought_mark = "✅" if item.get("bought") else "☐"
            text += f"  {bought_mark} {item['item']}\n"
        text += "\n"
    
    text += (
        "💡 *Как отмечать:*\n"
        "• Напиши `+название` — отметить купленным\n"
        "• Напиши `+что угодно` — добавить в список\n"
        "• Напиши `−название` — убрать из списка\n\n"
        "*Примеры:*\n"
        "`+молоко` — отметить молоко\n"
        "`+колбаса докторская 300г` — добавить покупку\n"
        "`−бананы` — убрать бананы"
    )
    
    await message.answer(text, parse_mode="Markdown", reply_markup=MAIN_KB)


@router.message(F.text.startswith("+"))
async def add_item(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return
    
    item_text = message.text[1:].strip()
    if not item_text:
        await message.answer("Что добавить? Напиши `+название`")
        return
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    items = await ShoppingRepo.get_week(user["id"], week_start.isoformat())
    found = False
    
    for item in items:
        if item_text.lower() in item["item"].lower():
            async with get_db() as conn:
                await conn.execute(
                    "UPDATE shopping_list SET bought=1 WHERE id=?",
                    (item["id"],)
                )
                await conn.commit()
            await message.answer(f"✅ *{item['item']}* отмечен!", parse_mode="Markdown")
            found = True
            break
    
    if not found:
        async with get_db() as conn:
            await conn.execute(
                "INSERT INTO shopping_list (user_id, week_start, item, category, bought) VALUES (?,?,?,?,?)",
                (user["id"], week_start.isoformat(), item_text, "добавлено", 1)
            )
            await conn.commit()
        
        await message.answer(
            f"📝 *{item_text}* добавлен в список!\n"
            "Я запомню что ты это купила и учту в следующем меню 😊",
            parse_mode="Markdown"
        )


@router.message(F.text.startswith("−"))
async def remove_item(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return
    
    item_text = message.text[1:].strip()
    if not item_text:
        return
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    async with get_db() as conn:
        await conn.execute(
            "DELETE FROM shopping_list WHERE user_id=? AND week_start=? AND item LIKE ?",
            (user["id"], week_start.isoformat(), f"%{item_text}%")
        )
        await conn.commit()
    
    await message.answer(f"🗑 *{item_text}* убран из списка", parse_mode="Markdown")
