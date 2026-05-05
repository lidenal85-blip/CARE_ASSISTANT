#!/usr/bin/env python3
"""main.py — ТОЛЬКО БОТ."""
import asyncio, sys, os
from pathlib import Path
from dotenv import load_dotenv

ROOT = str(Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv(Path(ROOT) / ".env")

from aiogram import Bot, Dispatcher
from services.fsm_storage import SQLiteStorage
from app_config.settings import settings
from db.connection import init_db

# KeyPool v2 инициализируется автоматически при первом вызове get_pool()
from leviathan.core import get_pool

async def main():
    await init_db()
    
    # Форсируем инициализацию KeyPool
    pool = get_pool()
    print(f"🔑 {pool}")
    
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=SQLiteStorage())
    
    import importlib
from engine.onboarding_engine import router as onboarding_router
    handlers = [
        "profile","shopping_tracker","diet","notes",
        "recipes","feedback","hobby","economy","guests","share","message"
    ]
    
    dp.include_router(onboarding_router)
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
