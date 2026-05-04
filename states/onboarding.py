"""
states/onboarding.py — FSM 18 шагов онбординга
"""
from aiogram.fsm.state import State, StatesGroup

class Onboarding(StatesGroup):
    # Шаг 1: Имя
    name = State()
    # Шаг 2: Возраст
    age = State()
    # Шаг 3: Пол
    gender = State()
    # Шаг 4: Вес
    weight = State()
    # Шаг 5: Рост
    height = State()
    # Шаг 6: График работы
    work = State()
    # Шаг 7: Подъём
    wake_up = State()
    # Шаг 8: Отбой
    sleep_time = State()
    # Шаг 9: Часы сна
    sleep_hours = State()
    # Шаг 10: Уровень стресса
    stress = State()
    # Шаг 11: Активность
    activity = State()
    # Шаг 12: Хобби
    hobby = State()
    # Шаг 13: Бытовые дела
    chores = State()
    # Шаг 14: Здоровье
    health = State()
    # Шаг 15: Еда
    food_pref = State()
    # Шаг 16: Главная цель
    goal = State()
    # Шаг 17: Бюджет
    budget = State()
    # Шаг 18: Триггеры настроения
    mood_triggers = State()
