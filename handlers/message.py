"""
handlers/message.py — обработка свободных сообщений через companion
"""
from aiogram import Router, F
from aiogram.types import Message
from services.companion import companion_response

router = Router()

@router.message(F.text & ~F.text.startswith("/") & ~F.text.startswith("+") & ~F.text.startswith("−"))
async def handle_free_text(message: Message):
    response = await companion_response(message.from_user.id, message.text)
    if response:
        await message.answer(response)
    # Если ответа нет — молча игнорируем, не спамим
