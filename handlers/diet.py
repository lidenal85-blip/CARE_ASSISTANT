"""handlers/diet.py — 🥗 Диета через menu_engine"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo, ShoppingRepo
from engine.menu_engine import get_or_create_menu, format_menu, profile_hash
from services.gemini import GeminiError
from keyboards.reply import MAIN_KB
import json

router = Router()

@router.message(F.text == "🥗 Диета")
@router.message(Command("diet"))
async def cmd_diet(message: Message):
    user = await UserRepo.get_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала /start", reply_markup=MAIN_KB)
        return
    
    msg = await message.answer("🥗 *Составляю меню...*", parse_mode="Markdown")
    
    # Собираем профиль для хеша
    profile = {
        "goal": user.get("goals", [{}])[0].get("type", "здоровье") if user.get("goals") else "здоровье",
        "weight": user.get("weight", 60),
        "height": user.get("height", 165),
        "activity": user.get("activity", "умеренная"),
        "budget": (user.get("food_preferences", {}) or {}).get("budget", "средний"),
        "loved": json.loads((user.get("food_preferences", {}) or {}).get("loved", "[]") or "[]"),
        "hated": json.loads((user.get("food_preferences", {}) or {}).get("hated", "[]") or "[]"),
    }
    
    try:
        menu = await get_or_create_menu(profile)
        if menu:
            text = format_menu(menu)
            
            # Сохраняем список покупок для /buy
            from datetime import date, timedelta
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            # Извлекаем продукты из блюд через Gemini
            shopping_items = await extract_shopping_list(menu)
            if shopping_items:
                await ShoppingRepo.add_week(user["id"], week_start.isoformat(), shopping_items)
            await msg.edit_text(text, parse_mode="Markdown")
            await message.answer(
                f"🍽 *Меню готово!* В следующий раз соберу ещё быстрее 🌸"
                "В следующий раз — мгновенно!",
                parse_mode="Markdown", reply_markup=MAIN_KB)
        else:
            await msg.edit_text("❌ Не получилось. Попробуй позже.")
    except GeminiError:
        await msg.edit_text("😔 Сервер Google перегружен. Попробуй через минуту.")
    except Exception as e:
        await msg.edit_text("❌ Ошибка. Попробуй позже.")
        print(f"Diet error: {e}")
