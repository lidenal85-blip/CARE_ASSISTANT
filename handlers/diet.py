"""
handlers/diet.py — 🥗 Индивидуальная диета
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db.repository import UserRepo, MealRepo
from services.diet_planner import create_individual_diet, format_diet_message
from services.price_checker import get_prices_for_shopping_list
from services.gemini import GeminiError
from keyboards.reply import MAIN_KB

router = Router()

@router.message(F.text == "🥗 Диета")
@router.message(Command("diet"))
async def cmd_diet(message: Message):
    user = await UserRepo.get_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала /start", reply_markup=MAIN_KB)
        return
    
    # Сразу отвечаем что начали
    msg = await message.answer("🥗 *Составляю меню...*", parse_mode="Markdown")
    
    try:
        data = await create_individual_diet(message.from_user.id, user)
        
        if not data:
            await msg.edit_text("❌ Не получилось. Попробуй позже.")
            return
        
        from datetime import date, timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        await MealRepo.save_week(user["id"], week_start.isoformat(), data["meals"])
        
        text = format_diet_message(data)
        await msg.edit_text(text, parse_mode="Markdown")
        
        region = "Хабаровск"
        priced = await get_prices_for_shopping_list(data["shopping"], region)
        
        shop_text = f"🛒 *Список покупок* ({priced['region']}, {priced['date']})\n\n"
        shop_text += "```\n"
        shop_text += "Продукт          Кол-во   Цена    Сумма\n"
        shop_text += "─" * 42 + "\n"
        
        for item in priced["items"]:
            name = item["item"][:15].ljust(15)
            amount = item["amount"][:7].ljust(7)
            price = str(item["price_per_unit"]).rjust(5)
            total = str(item["total"]).rjust(6)
            shop_text += f"{name} {amount} {price}₽ {total}₽\n"
        
        shop_text += "─" * 42 + "\n"
        shop_text += f"{'ИТОГО':>34} {priced['total']}₽\n"
        shop_text += "```\n"
        shop_text += f"📍 Цены актуальны для {priced['region']}"
        
        await message.answer(shop_text, parse_mode="Markdown", reply_markup=MAIN_KB)
        
    except GeminiError:
        await msg.edit_text("😔 Сервер Google перегружен. Попробуй через минуту.")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка. Попробуй позже.")
        print(f"Diet error: {e}")
