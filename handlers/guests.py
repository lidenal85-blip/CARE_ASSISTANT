"""
handlers/guests.py — меню для гостей
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from services.gemini import ask

router = Router()

GUEST_MENU_SYSTEM = "Ты — шеф-повар. Составляешь меню для гостей."

GUEST_MENU_PROMPT = """Придумай меню для гостей:
- Гостей: {guests} человек
- Повод: {occasion}
- Бюджет: {budget} ₽
- Время на готовку: {time} минут

Верни JSON:
{{
  "menu": ["закуска 1", "закуска 2", "горячее", "десерт", "напитки"],
  "shopping": ["продукт 1", "..."],
  "total_time": 90,
  "total_cost": 2500
}}
Только JSON."""

@router.message(Command("guests"))
async def cmd_guests(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "🎉 *Гости? Составлю меню!*\n\n"
            "Напиши: /guests 4 человека, день рождения, бюджет 3000₽",
            parse_mode="Markdown"
        )
        return
    
    response = await ask(
        GUEST_MENU_PROMPT.format(
            guests=4,
            occasion="день рождения",
            budget=3000,
            time=90
        ),
        GUEST_MENU_SYSTEM
    )
    
    await message.answer(f"🍽 *Меню для гостей*\n\n{response}", parse_mode="Markdown")
