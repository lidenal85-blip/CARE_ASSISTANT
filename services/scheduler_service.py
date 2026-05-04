"""
services/scheduler_service.py — напоминалки по расписанию
"""
import asyncio
from datetime import datetime, time
from db.repository import UserRepo, WaterRepo

async def scheduler_loop(bot, user_id: int):
    """Бесконечный цикл проверки расписания для пользователя."""
    
    last_water = None
    last_morning = None
    last_evening = None
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        weekday = now.weekday()  # 0=пн
        
        user = await UserRepo.get_by_telegram(user_id)
        if not user:
            await asyncio.sleep(60)
            continue
        
        # ── Вода (каждые 2 часа) ─────────────────
        if user.get("wake_up"):
            wake_h = int(user["wake_up"].split(":")[0])
            hours_since_wake = now.hour - wake_h
            if hours_since_wake >= 0 and hours_since_wake % 2 == 0 and last_water != now.hour:
                last_water = now.hour
                await bot.send_message(
                    user["telegram_id"],
                    f"💧 Выпей стакан воды! Сегодня уже {await WaterRepo.today_ml(user['id'])} мл"
                )
        
        # ── Утро (wake_up + 5 мин) ───────────────
        if user.get("wake_up") and last_morning != now.date():
            if current_time == user["wake_up"]:
                last_morning = now.date()
                await bot.send_message(
                    user["telegram_id"],
                    f"☀️ Доброе утро, {user.get('name', 'солнышко')}!\n"
                    f"Сегодня {['пн','вт','ср','чт','пт','сб','вс'][weekday]}.\n"
                    f"Используй /plan чтобы посмотреть план на день."
                )
        
        # ── Вечер (sleep_time - 1 час) ───────────
        if user.get("sleep_time") and last_evening != now.date():
            sleep_h, sleep_m = map(int, user["sleep_time"].split(":"))
            evening_h = sleep_h - 1
            if now.hour == evening_h and now.minute >= sleep_m:
                last_evening = now.date()
                await bot.send_message(
                    user["telegram_id"],
                    f"🌙 День почти закончен. Как настроение? /mood\n"
                    f"Пора сворачиваться и готовиться ко сну."
                )
        
        await asyncio.sleep(60)  # проверка каждую минуту
