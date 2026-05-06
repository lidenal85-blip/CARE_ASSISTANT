"""
db/connection.py — асинхронное подключение к SQLite с контекстным менеджером
"""
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager

DB_PATH = Path(__file__).parent.parent / "data" / "zabota.db"

@asynccontextmanager
async def get_db():
    """Контекстный менеджер — автоматически закрывает соединение при выходе."""
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(str(DB_PATH)) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        yield conn

async def init_db():
    async with get_db() as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            name TEXT, age INTEGER, gender TEXT,
            weight REAL, height REAL,
            wake_up TEXT, sleep_time TEXT, sleep_hours TEXT,
            stress TEXT, activity TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            type TEXT, target TEXT, deadline TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS chores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            name TEXT, day_of_week INTEGER, time TEXT
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS shopping_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            week_start TEXT, item TEXT, category TEXT,
            bought INTEGER DEFAULT 0
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS water_intake (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            timestamp TEXT DEFAULT (datetime('now')),
            amount_ml INTEGER DEFAULT 250
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS mood_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            timestamp TEXT DEFAULT (datetime('now')),
            score INTEGER, note TEXT
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            text TEXT NOT NULL, done INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            type TEXT DEFAULT 'general'
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            week_start TEXT, day INTEGER, meal_type TEXT,
            dish TEXT, calories REAL, protein REAL,
            fat REAL, carbs REAL
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS hobbies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            name TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS food_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id),
            budget TEXT DEFAULT 'средний',
            loved TEXT DEFAULT '[]',
            hated TEXT DEFAULT '[]'
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS mood_triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id),
            makes_happy TEXT DEFAULT '[]',
            makes_angry TEXT DEFAULT '[]'
        )""")

        await conn.execute("""CREATE TABLE IF NOT EXISTS cached_menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_hash TEXT UNIQUE NOT NULL,
            menu_json TEXT NOT NULL,
            shopping_json TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            used_count INTEGER DEFAULT 1
        )""")
        await conn.commit()
