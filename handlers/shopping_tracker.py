"""handlers/shopping_tracker.py — 🛒 Покупки с группировкой"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo, ShoppingRepo
from keyboards.reply import MAIN_KB
from datetime import date, timedelta

router = Router()

CATEGORY_EMOJI = {
    "мясо": "🥩", "рыба": "🐟", "овощи": "🥬", "фрукты": "🍎",
    "молочное": "🥛", "крупы": "🌾", "хлеб": "🍞", "яйца": "🥚",
    "напитки": "🧃", "бакалея": "🛍", "прочее": "📦",
    "breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍪"
}

@router.message(F.text == "🛒 Покупки")
@router.message(Command("buy"))
async def cmd_shopping(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Сначала /start", reply_markup=MAIN_KB)
        return
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    items = await ShoppingRepo.get_week(user["id"], week_start.isoformat())
    
    if not items:
        await message.answer(
            "🛒 *Список покупок пуст*\n\n"
            "Создай меню через 🥗 *Диета* — и я соберу список продуктов.",
            parse_mode="Markdown", reply_markup=MAIN_KB)
        return
    
    # Группируем по категориям
    grouped = {}
    for item in items:
        cat = item.get("category", "прочее").lower()
        grouped.setdefault(cat, []).append(item["item"])
    
    text = f"🛒 *Список покупок*\n{week_start.day}.{week_start.month} — {week_start.day+6}.{week_start.month}\n\n"
    
    for cat, products in grouped.items():
        emoji = CATEGORY_EMOJI.get(cat, "📌")
        text += f"{emoji} *{cat.title()}*\n"
        for p in products[:5]:
            text += f"  • {p}\n"
        if len(products) > 5:
            text += f"  ... и ещё {len(products)-5}\n"
        text += "\n"
    
    text += f"📋 *Всего:* {len(items)} продуктов\n"
    text += "💡 _Отмечай купленное: `+молоко`_"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=MAIN_KB)


@router.message(F.text.startswith("+"))
async def mark_bought(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return
    
    item_text = message.text[1:].strip()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    items = await ShoppingRepo.get_week(user["id"], week_start.isoformat())
    
    for item in items:
        if item_text.lower() in item["item"].lower():
            from db.connection import get_db
            async with get_db() as conn:
                await conn.execute("UPDATE shopping_list SET bought=1 WHERE id=?", (item["id"],))
                await conn.commit()
            await message.answer(f"✅ *{item['item']}* — куплено!", parse_mode="Markdown")
            return
    
    await message.answer(f"📝 *{item_text}* — добавила в список", parse_mode="Markdown")


@router.message(F.text.startswith("−"))
async def remove_item(message: Message):
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return
    
    item_text = message.text[1:].strip()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    from db.connection import get_db
    async with get_db() as conn:
        await conn.execute(
            "DELETE FROM shopping_list WHERE user_id=? AND week_start=? AND item LIKE ?",
            (user["id"], week_start.isoformat(), f"%{item_text}%"))
        await conn.commit()
    
    await message.answer(f"🗑 *{item_text}* убрала", parse_mode="Markdown")
