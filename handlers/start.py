"""handlers/start.py — /start через движок онбординга"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states.onboarding import Onboarding
from db.repository import UserRepo
from keyboards.reply import MAIN_KB

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await UserRepo.get_by_telegram(message.from_user.id)
    
    if user:
        await message.answer(
            f"👋 С возвращением, *{user.get('name', 'подруга')}*!\n"
            "Используй кнопки внизу или /help.",
            parse_mode="Markdown", reply_markup=MAIN_KB)
        return
    
    # Первый вопрос из JSON
    first = engine.config["basic"][0]
    await message.answer(first["ask"])
    await state.set_state(Onboarding.name)

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🌸 *Забота+*:\n\n"
        "🥗 Диета | 🍽 Меню | 💧 Вода\n"
        "😊 Настроение | 🛒 Покупки\n"
        "👤 Профиль | 📋 План\n\n"
        "/start /help",
        parse_mode="Markdown", reply_markup=MAIN_KB)
