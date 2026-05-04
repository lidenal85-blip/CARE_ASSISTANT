"""
handlers/overlay.py — кнопка Оверлей → Mini App
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

router = Router()

@router.message(F.text == "⚙️ Оверлей")
async def open_overlay(message: Message):
    """Открывает Mini App с оверлеем."""
    await message.answer(
        "⚙️ *Оверлей Забота+*\n\n"
        "Нажми кнопку ниже чтобы открыть панель управления.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="🌸 Открыть Забота+",
                    web_app=WebAppInfo(url="https://your-app-url.ngrok-free.app/overlay")
                )
            ]]
        )
    )

@router.message(F.text == "📝 Отзыв")
async def feedback_button(message: Message):
    await message.answer(
        "📝 *Обратная связь*\n\n"
        "Напиши /feedback и твоё пожелание.\n"
        "Например: /feedback хочу рецепты с видео",
        parse_mode="Markdown"
    )
