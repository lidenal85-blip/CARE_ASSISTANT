#!/usr/bin/env python3
"""
run_doctor.py — ОТДЕЛЬНЫЙ процесс доктора.
Запускается через: python run_doctor.py --watch
Не связан с main.py — никаких subprocess.Popen(["python", "main.py"])
"""
import sys, os
from pathlib import Path
from dotenv import load_dotenv

# Путь к корню проекта
ROOT = Path(__file__).parent
os.chdir(str(ROOT))
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from leviathan.doctor import DoctorSystem

d = DoctorSystem(str(ROOT))

if '--watch' in sys.argv:
    print("🩺 Доктор в режиме наблюдения (каждые 30 сек)...")
    d.watch()
else:
    print("🩺 Доктор: разовая проверка...")
    d.run_once()
    print("✅ Проверка завершена")
