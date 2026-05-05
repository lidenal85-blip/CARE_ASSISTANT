#!/usr/bin/env python3
"""main.py — бот Забота+"""
import asyncio, sys, os
from pathlib import Path
from dotenv import load_dotenv

ROOT = str(Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv(Path(ROOT) / ".env")

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app_config.settings import settings
from db.connection import init_db
from leviathan.core import get_pool
from engine.onboarding_engine import router as onboarding_router

async def main():
    await init_db()
    pool = get_pool()
    print(f"🔑 {pool}")
    
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Движок онбординга
    dp.include_router(onboarding_router)
    
    # Остальные хендлеры
    import importlib
    handlers = [
        "start", "menu", "water", "mood", "plan",
        "profile", "shopping_tracker", "diet", "notes",
        "recipes", "feedback", "hobby", "economy", "guests", "share", "message"
    ]
    
    for mod_name in handlers:
        try:
            mod = importlib.import_module(f"handlers.{mod_name}")
            dp.include_router(mod.router)
        except Exception as e:
            print(f"⚠ {mod_name}: {e}")
    
    print(f"🚀 Забота+ | @{(await bot.get_me()).username}")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
