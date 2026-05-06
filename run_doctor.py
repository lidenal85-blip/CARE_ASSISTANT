#!/usr/bin/env python3
"""run_doctor.py — только DoctorSystem, без Telegram API"""
import asyncio, os, sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "leviathan-core"))

from leviathan.doctor.doctor_system import DoctorSystem

async def main():
    doctor = DoctorSystem(ROOT)
    interval = int(os.getenv("DOCTOR_INTERVAL", "60"))
    print(f"🩺 Doctor v12 | интервал {interval}с")
    doctor.watch(interval=interval)

if __name__ == "__main__":
    asyncio.run(main())
