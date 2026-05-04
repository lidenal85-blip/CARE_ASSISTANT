"""
handlers/feedback.py — /feedback — сбор пожеланий и отчёт для разработчика
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from services.gemini import ask

router = Router()

FEEDBACK_SYSTEM = """Ты — AI-аналитик. Пользователь оставляет отзыв или пожелание по улучшению бота.
Твоя задача — структурировать это и отправить разработчику.

Формат отчёта:
💬 ОТЗЫВ ПОЛЬЗОВАТЕЛЯ
[оригинальный текст]

🔍 АНАЛИЗ
[что пользователь на самом деле хочет]

💡 РЕКОМЕНДАЦИЯ
[конкретное предложение для разработчика]

⚡ ПРИОРИТЕТ
[high / medium / low]"""

@router.message(Command("feedback"))
async def cmd_feedback(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "📝 *Обратная связь*\n\n"
            "Напиши что хочешь улучшить или добавить.\n"
            "Например: /feedback хочу чтобы бот присылал рецепты с видео",
            parse_mode="Markdown"
        )
        return
    
    feedback_text = parts[1].strip()
    await message.answer("📊 Анализирую и отправляю разработчику...")
    
    report = await ask(
        f"Пользователь написал: {feedback_text}",
        FEEDBACK_SYSTEM
    )
    
    # Отправляем отчёт разработчику (тебе)
    developer_id = 1290089595  # Твой Telegram ID
    
    await message.bot.send_message(
        developer_id,
        f"📨 *Новый отзыв от пользователя*\n\n{report}",
        parse_mode="Markdown"
    )
    
    await message.answer(
        "✅ *Спасибо!* Твой отзыв отправлен разработчику.\n"
        "Каждое пожелание делает бота лучше 🌸",
        parse_mode="Markdown"
    )
