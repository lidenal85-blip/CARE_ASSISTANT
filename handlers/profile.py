"""handlers/profile.py — 👤 Профиль с геймификацией"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from db.repository import UserRepo
import json
from datetime import date, timedelta

router = Router()

@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await UserRepo.get_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return
    
    name = user.get("name", "Подруга")
    age = user.get("age", "—")
    weight = user.get("weight", "—")
    height = user.get("height", "—")
    goal = user.get("goals", [{}])[0].get("type", "—") if user.get("goals") else "—"
    activity = user.get("activity", "—")
    stress = user.get("stress", "—")
    region = user.get("region", "—")
    cooking = user.get("cooking_time", "—")
    kitchen = user.get("kitchen_equipment", "—")
    sleep_hours = user.get("sleep_hours", "—")
    
    # Расчёт BMR
    w = float(weight) if weight != "—" else 60
    h = float(height) if height != "—" else 165
    a = int(age) if age != "—" else 25
    g = user.get("gender", "Женский")
    bmr = 447.6 + (9.2 * w) + (3.1 * h) - (4.3 * a) if g == "Женский" else 88.36 + (13.4 * w) + (4.8 * h) - (5.7 * a)
    
    # Геймификация: считаем дни с момента регистрации
    from db.connection import get_db
    async with get_db() as conn:
        # Дней в системе
        cursor = await conn.execute("SELECT created_at FROM users WHERE telegram_id=?", (message.from_user.id,))
        row = await cursor.fetchone()
        days = 0
        if row and row["created_at"]:
            created = row["created_at"][:10]
            days = (date.today() - date.fromisoformat(created)).days
        
        # Стаканов воды сегодня
        cursor = await conn.execute(
            "SELECT COALESCE(SUM(amount_ml), 0) FROM water_intake WHERE user_id=? AND date(timestamp)=date('now','localtime')",
            (user["id"],)
        )
        water_ml = (await cursor.fetchone())[0]
        
        # Настроений за неделю
        cursor = await conn.execute(
            "SELECT AVG(score) FROM mood_entries WHERE user_id=? AND date(timestamp) >= date('now','-7 days')",
            (user["id"],)
        )
        avg_mood = (await cursor.fetchone())[0]
    
    water_glasses = water_ml // 250
    mood_str = f"{avg_mood:.1f}/10" if avg_mood else "—"
    
    # Красивое оформление
    text = (
        f"🌸 *{name}* | Профиль\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 *Основное*\n"
        f"  🎯 Цель: {goal}\n"
        f"  ⚖️ Вес: {weight} кг | Рост: {height} см\n"
        f"  🔥 BMR: {bmr:.0f} ккал/день\n"
        f"  🎂 Возраст: {age} лет\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📍 *Образ жизни*\n"
        f"  🏙 Город: {region}\n"
        f"  💪 Активность: {activity}\n"
        f"  😰 Стресс: {stress}\n"
        f"  😴 Сон: {sleep_hours}\n"
        f"  🍳 Готовка: {cooking}\n"
        f"  🛠 Кухня: {kitchen}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏆 *Достижения*\n"
        f"  📅 Дней с Заботой+: {days}\n"
        f"  💧 Воды сегодня: {water_glasses} ст. ({water_ml} мл)\n"
        f"  😊 Настроение за неделю: {mood_str}\n"
    )
    
    # Добавляем стрик если есть
    if days >= 7:
        text += f"  🔥 Стрик: {days // 7} недель подряд!\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить данные", callback_data="edit_profile")],
        [InlineKeyboardButton(text="📋 План на сегодня", callback_data="plan_today")],
        [InlineKeyboardButton(text="📊 Отчёт за неделю", callback_data="weekly_report")],
    ])
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
