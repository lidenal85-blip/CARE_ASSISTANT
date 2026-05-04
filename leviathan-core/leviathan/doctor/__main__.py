"""Точка входа: python -m leviathan.doctor [project_root]"""
import sys, os
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
load_dotenv(project_root / ".env")

from leviathan.doctor import DoctorSystem
d = DoctorSystem(project_root)
d.run_once()
