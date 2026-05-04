"""Pydantic-схемы"""
from pydantic import BaseModel
from typing import Optional
from datetime import time

class UserProfile(BaseModel):
    telegram_id: int
    name: str
    age: int
    gender: str
    weight: float
    height: float
    wake_up: time
    sleep_time: time
    sleep_hours: str
    stress: str
    activity: str

class Meal(BaseModel):
    day: int
    meal_type: str
    dish: str
    calories: float
    protein: float = 0
    fat: float = 0
    carbs: float = 0

class WeeklyMenu(BaseModel):
    week_start: str
    meals: list[Meal]
