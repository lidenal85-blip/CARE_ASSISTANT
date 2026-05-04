"""
db/repository.py — CRUD-операции (все через async with get_db)
"""
import json
from .connection import get_db

class UserRepo:
    ALLOWED_FIELDS = {"name", "age", "gender", "weight", "height",
                       "wake_up", "sleep_time", "sleep_hours", "stress", "activity", "work"}
    
    @staticmethod
    async def create(telegram_id: int, **kwargs) -> int:
        async with get_db() as conn:
            cursor = await conn.execute(
                "INSERT INTO users (telegram_id) VALUES (?)",
                (telegram_id,)
            )
            await conn.commit()
            return cursor.lastrowid

    @staticmethod
    async def update(user_id: int, **kwargs):
        async with get_db() as conn:
            for key, value in kwargs.items():
                if key not in UserRepo.ALLOWED_FIELDS:
                    raise ValueError(f"Invalid field: {key}")
                await conn.execute(
                    f"UPDATE users SET {key}=? WHERE id=?",
                    (value, user_id)
                )
            await conn.commit()

    @staticmethod
    async def get_by_telegram(telegram_id: int) -> dict | None:
        async with get_db() as conn:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE telegram_id=?",
                (telegram_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def get_profile(telegram_id: int) -> dict | None:
        async with get_db() as conn:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE telegram_id=?",
                (telegram_id,)
            )
            user = await cursor.fetchone()
            if not user:
                return None
            
            user_id = user["id"]
            profile = dict(user)
            
            cursor = await conn.execute(
                "SELECT * FROM goals WHERE user_id=? AND status='active'",
                (user_id,)
            )
            profile["goals"] = [dict(r) for r in await cursor.fetchall()]
            
            cursor = await conn.execute(
                "SELECT * FROM hobbies WHERE user_id=? AND active=1",
                (user_id,)
            )
            profile["hobbies"] = [dict(r) for r in await cursor.fetchall()]
            
            cursor = await conn.execute(
                "SELECT * FROM chores WHERE user_id=?",
                (user_id,)
            )
            profile["chores"] = [dict(r) for r in await cursor.fetchall()]
            
            cursor = await conn.execute(
                "SELECT * FROM food_preferences WHERE user_id=?",
                (user_id,)
            )
            food = await cursor.fetchone()
            profile["food_preferences"] = dict(food) if food else {}
            
            return profile


class GoalRepo:
    @staticmethod
    async def add(user_id: int, goal_type: str, target: str = "", deadline: str = ""):
        async with get_db() as conn:
            await conn.execute(
                "INSERT INTO goals (user_id, type, target, deadline) VALUES (?,?,?,?)",
                (user_id, goal_type, target, deadline)
            )
            await conn.commit()


class MealRepo:
    @staticmethod
    async def save_week(user_id: int, week_start: str, meals: list[dict]):
        async with get_db() as conn:
            await conn.execute(
                "DELETE FROM meals WHERE user_id=? AND week_start=?",
                (user_id, week_start)
            )
            for m in meals:
                await conn.execute(
                    "INSERT INTO meals (user_id, week_start, day, meal_type, dish, calories, protein, fat, carbs) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (user_id, week_start, m["day"], m["meal_type"], m["dish"],
                     m.get("calories", 0), m.get("protein", 0), m.get("fat", 0), m.get("carbs", 0))
                )
            await conn.commit()


class WaterRepo:
    @staticmethod
    async def add(user_id: int, amount_ml: int = 250):
        async with get_db() as conn:
            await conn.execute(
                "INSERT INTO water_intake (user_id, amount_ml) VALUES (?,?)",
                (user_id, amount_ml)
            )
            await conn.commit()

    @staticmethod
    async def today_ml(user_id: int) -> int:
        async with get_db() as conn:
            cursor = await conn.execute(
                "SELECT COALESCE(SUM(amount_ml), 0) as total FROM water_intake "
                "WHERE user_id=? AND date(timestamp) = date('now', 'localtime')",
                (user_id,)
            )
            row = await cursor.fetchone()
            return row["total"] if row else 0


class MoodRepo:
    @staticmethod
    async def add(user_id: int, score: int, note: str = ""):
        async with get_db() as conn:
            await conn.execute(
                "INSERT INTO mood_entries (user_id, score, note) VALUES (?,?,?)",
                (user_id, score, note)
            )
            await conn.commit()


class ShoppingRepo:
    @staticmethod
    async def add_week(user_id: int, week_start: str, items: list[dict]):
        async with get_db() as conn:
            await conn.execute(
                "DELETE FROM shopping_list WHERE user_id=? AND week_start=?",
                (user_id, week_start)
            )
            for item in items:
                await conn.execute(
                    "INSERT INTO shopping_list (user_id, week_start, item, category) VALUES (?,?,?,?)",
                    (user_id, week_start, item["item"], item.get("category", ""))
                )
            await conn.commit()

    @staticmethod
    async def get_week(user_id: int, week_start: str) -> list[dict]:
        async with get_db() as conn:
            cursor = await conn.execute(
                "SELECT * FROM shopping_list WHERE user_id=? AND week_start=? ORDER BY category, item",
                (user_id, week_start)
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
