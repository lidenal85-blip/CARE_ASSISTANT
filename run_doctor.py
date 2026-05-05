#!/usr/bin/env python3
"""
run_doctor.py — Доктор Leviathan v11
Лечит код (AST + Gemini) + мониторит логи + шлёт отчёты в Telegram
"""
import sys, os, asyncio
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
os.chdir(str(ROOT))
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from leviathan.doctor import DoctorSystem
from engine.doctor_monitor import DoctorMonitor

async def main():
    token = os.getenv("BOT_TOKEN", "")
    admin_id = 7709651193
    
    # Монитор — отчёты в Telegram
    if token:
        monitor = DoctorMonitor(token, admin_id)
        asyncio.create_task(monitor_loop(monitor))
        print("📡 Монитор: отчёты в Telegram")
    
    # Доктор — лечение кода
    doctor = DoctorSystem(str(ROOT))
    
    if '--watch' in sys.argv:
        print("🩺 Доктор: наблюдение каждые 60 сек")
        doctor.watch(interval=60)
    else:
        doctor.run_once()
        print("✅ Проверка завершена")

async def monitor_loop(monitor):
    await asyncio.sleep(5)  # ждём запуска бота
    while True:
        try:
            await monitor.run_cycle()
        except Exception as e:
            print(f"[Monitor] {e}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
