"""
handlers/start.py — /start, /help, /reset
"""
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
            f"👋 С возвращением, *{user['name']}*!\n\n"
            "Используй кнопки внизу или /help.",
            parse_mode="Markdown",
            reply_markup=MAIN_KB
        )
        return
    
    await message.answer(
        "🌸 Привет! Я — Забота+, твой персональный AI-ассистент.\n\n"
        "Я помогу тебе с питанием, напоминалками, планами и поддержкой.\n"
        "Давай познакомимся! Это займёт 3-5 минут.\n\n"
        "Как тебя зовут?"
    )
    await state.set_state(Onboarding.name)

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🌸 *Забота+* — что я умею:\n\n"
        "🍽 *Меню* — меню на неделю\n"
        "📋 *План* — план на сегодня\n"
        "💧 *Вода* — записать стакан\n"
        "😊 *Настроение* — записать\n"
        "🛒 *Покупки* — список покупок\n"
        "👤 *Профиль* — что я знаю\n\n"
        "Команды: /start /help /reset",
        parse_mode="Markdown",
        reply_markup=MAIN_KB
    )

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔄 Данные сброшены. Напиши /start чтобы начать заново.")
