"""
services/companion.py — эмпатический агент (поддержка)
"""
from aiogram import Router
from services.gemini import ask
from app_config.prompts import COMPANION_PROMPT, COMPANION_SYSTEM
from db.repository import UserRepo
import json

router = Router()

# Детерминированные триггеры (без LLM)
TRIGGERS = {
    "грустн": "Обнимаю тебя мысленно 🤗 Всё наладится. Может, расскажешь что случилось?",
    "устал": "Ты много делаешь, это правда. Помни что отдых — это не лень, а забота о себе 💆‍♀️",
    "одинок": "Ты не одна. У тебя есть ты сама — и это уже сильный человек. И я всегда рядом 💕",
    "спасиб": "Всегда пожалуйста! Я здесь именно для этого 🌸",
}

async def companion_response(telegram_id: int, message: str) -> str | None:
    """Возвращает эмпатический ответ если сообщение содержит негатив."""
    
    msg_lower = message.lower()
    for trigger, response in TRIGGERS.items():
        if trigger in msg_lower:
            return response
    
    if len(message.split()) < 5:
        return None
    
    user = await UserRepo.get_profile(telegram_id)
    if not user:
        return None
    
    profile = f"""
Имя: {user.get('name', '—')}
Цели: {', '.join(g.get('type', '') for g in user.get('goals', [])) if user.get('goals') else '—'}
Стресс: {user.get('stress', '—')}
Хобби: {', '.join(h.get('name', '') for h in user.get('hobbies', [])) if user.get('hobbies') else '—'}
"""
    
    prompt = COMPANION_PROMPT.format(profile=profile, message=message)
    response = await ask(prompt, COMPANION_SYSTEM)
    
    if response and not response.startswith("["):
        return response.strip()
    
    return None
