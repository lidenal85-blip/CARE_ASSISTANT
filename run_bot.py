#!/usr/bin/env python3
"""ТОЛЬКО БОТ. Доктор — отдельно."""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, "/storage/emulated/0/Documents/LEVIATHAN_refactored")

from aiogram import Bot, Dispatcher
from aiogram_sqlite_storage.sqlitestore import SQLStorage
from app_config.settings import settings
from db.connection import init_db
from core.orchestrator import KeyPool
from services.gemini import init_pool

async def main():
    await init_db()
    
    gemini_pool = KeyPool("GEMINI", "GEMINI")
    init_pool(gemini_pool)
    
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=SQLStorage("data/fsm.db"))
    
    import importlib
    for mod_name in [
        "start","onboarding","menu","water","mood","plan",
        "profile","shopping_tracker","diet","notes",
        "recipes","feedback","hobby","economy","guests","share","message"
    ]:
        try:
            mod = importlib.import_module(f"handlers.{mod_name}")
            dp.include_router(mod.router)
        except Exception as e:
            print(f"⚠ {mod_name}: {e}")
    
    print(f"🚀 @{(await bot.get_me()).username}")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
