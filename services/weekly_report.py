"""
services/weekly_report.py — еженедельный отчёт
"""
from datetime import date, timedelta
from db.repository import UserRepo, WaterRepo, MoodRepo, ShoppingRepo

async def generate_weekly_report(telegram_id: int) -> str:
    """Генерирует текстовый отчёт за неделю."""
    user = await UserRepo.get_profile(telegram_id)
    if not user:
        return "Нет данных"
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    # Вода
    from db.connection import get_db
    conn = await get_db()
    
    # Считаем воду за неделю
    cursor = await conn.execute(
        "SELECT SUM(amount_ml) as total, COUNT(*) as count FROM water_intake "
        "WHERE user_id=? AND date(timestamp) BETWEEN ? AND ?",
        (user["id"], week_start.isoformat(), today.isoformat())
    )
    water = await cursor.fetchone()
    
    # Настроение
    cursor = await conn.execute(
        "SELECT AVG(score) as avg, COUNT(*) as count FROM mood_entries "
        "WHERE user_id=? AND date(timestamp) BETWEEN ? AND ?",
        (user["id"], week_start.isoformat(), today.isoformat())
    )
    mood = await cursor.fetchone()
    
    # Покупки
    cursor = await conn.execute(
        "SELECT COUNT(*) as total, SUM(CASE WHEN bought=1 THEN 1 ELSE 0 END) as bought "
        "FROM shopping_list WHERE user_id=? AND week_start=?",
        (user["id"], week_start.isoformat())
    )
    shopping = await cursor.fetchone()
    
    await conn.close()
    
    water_ml = water["total"] or 0
    mood_avg = mood["avg"] or 0
    
    text = f"📊 *Еженедельный отчёт*\n"
    text += f"📅 {week_start.day}.{week_start.month} — {today.day}.{today.month}\n\n"
    text += f"💧 Вода: {water_ml/1000:.1f} литров ({water_ml//250} стаканов)\n"
    text += f"😊 Настроение: {mood_avg:.1f}/10\n"
    text += f"🛒 Покупки: {shopping['bought'] or 0}/{shopping['total'] or 0} выполнено\n"
    
    return text
