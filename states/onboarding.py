"""states/onboarding.py — FSM 27 шагов онбординга"""
from aiogram.fsm.state import State, StatesGroup

class Onboarding(StatesGroup):
    name = State()              # 1
    age = State()               # 2
    gender = State()            # 3
    weight = State()            # 4
    height = State()            # 5
    body_type = State()         # 6
    eating_behavior = State()   # 7
    cooking_time = State()      # 8
    kitchen_equipment = State() # 9
    region = State()            # 10
    medical_conditions = State()# 11
    fitness_goal = State()      # 12
    takes_supplements = State() # 13
    cooking_for = State()       # 14
    work = State()              # 15
    wake_up = State()           # 16
    sleep_time = State()        # 17
    sleep_hours = State()       # 18
    stress = State()            # 19
    activity = State()          # 20
    hobby = State()             # 21
    chores = State()            # 22
    health = State()            # 23
    food_pref = State()         # 24
    goal = State()              # 25
    budget = State()            # 26
    mood_triggers = State()     # 27
    cycle_tracking = State()
