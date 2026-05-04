"""
handlers/onboarding.py — 18 шагов FSM онбординга
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from states.onboarding import Onboarding
from db.repository import UserRepo, GoalRepo
from keyboards.reply import MAIN_KB

router = Router()

# ── Клавиатуры ──────────────────────────────────────

def _kb(*buttons: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b) for b in buttons]],
        resize_keyboard=True, one_time_keyboard=True
    )

# ── Шаг 1: Имя ───────────────────────────────────────

@router.message(Onboarding.name)
async def step_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Сколько тебе лет? (просто число)")
    await state.set_state(Onboarding.age)

# ── Шаг 2: Возраст ───────────────────────────────────

@router.message(Onboarding.age)
async def step_age(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Пожалуйста, введи число 🥲")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Твой пол?", reply_markup=_kb("Женский", "Мужской"))
    await state.set_state(Onboarding.gender)

# ── Шаг 3: Пол ───────────────────────────────────────

@router.message(Onboarding.gender)
async def step_gender(message: Message, state: FSMContext):
    if message.text not in ("Женский", "Мужской"):
        await message.answer("Выбери кнопкой 👆")
        return
    await state.update_data(gender=message.text)
    await message.answer("Какой у тебя вес? (в кг, просто число)")
    await state.set_state(Onboarding.weight)

# ── Шаг 4: Вес ───────────────────────────────────────

@router.message(Onboarding.weight)
async def step_weight(message: Message, state: FSMContext):
    try:
        w = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи число (например 65 или 65.5)")
        return
    await state.update_data(weight=w)
    await message.answer("Какой рост? (в см)")
    await state.set_state(Onboarding.height)

# ── Шаг 5: Рост ──────────────────────────────────────

@router.message(Onboarding.height)
async def step_height(message: Message, state: FSMContext):
    try:
        h = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи число (например 170)")
        return
    await state.update_data(height=h)
    await message.answer(
        "Какой у тебя график работы?",
        reply_markup=_kb("5/2 Офис", "Удалёнка", "Сменный", "Учёба", "Не работаю")
    )
    await state.set_state(Onboarding.work)

# ── Шаг 6: Работа ────────────────────────────────────

@router.message(Onboarding.work)
async def step_work(message: Message, state: FSMContext):
    await state.update_data(work=message.text)
    await message.answer("Во сколько обычно встаёшь? (например 08:00)")
    await state.set_state(Onboarding.wake_up)

# ── Шаг 7: Подъём ────────────────────────────────────

@router.message(Onboarding.wake_up)
async def step_wake_up(message: Message, state: FSMContext):
    await state.update_data(wake_up=message.text.strip())
    await message.answer("Во сколько ложишься? (например 23:00)")
    await state.set_state(Onboarding.sleep_time)

# ── Шаг 8: Отбой ──────────────────────────────────────

@router.message(Onboarding.sleep_time)
async def step_sleep_time(message: Message, state: FSMContext):
    await state.update_data(sleep_time=message.text.strip())
    await message.answer(
        "Сколько часов спишь?",
        reply_markup=_kb("<6 часов", "7-8 часов", "9+ часов")
    )
    await state.set_state(Onboarding.sleep_hours)

# ── Шаг 9: Часы сна ──────────────────────────────────

@router.message(Onboarding.sleep_hours)
async def step_sleep_hours(message: Message, state: FSMContext):
    await state.update_data(sleep_hours=message.text)
    await message.answer(
        "Какой уровень стресса?",
        reply_markup=_kb("Низкий", "Средний", "Высокий")
    )
    await state.set_state(Onboarding.stress)

# ── Шаг 10: Стресс ───────────────────────────────────

@router.message(Onboarding.stress)
async def step_stress(message: Message, state: FSMContext):
    await state.update_data(stress=message.text)
    await message.answer(
        "Физическая активность?",
        reply_markup=_kb("Сидячая", "1-2 тренировки", "3+ тренировок")
    )
    await state.set_state(Onboarding.activity)

# ── Шаг 11: Активность ───────────────────────────────

@router.message(Onboarding.activity)
async def step_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.answer("Чем увлекаешься? Хобби, интересы? (можно несколько через запятую)")
    await state.set_state(Onboarding.hobby)

# ── Шаг 12: Хобби ────────────────────────────────────

@router.message(Onboarding.hobby)
async def step_hobby(message: Message, state: FSMContext):
    hobbies = [h.strip() for h in message.text.split(",") if h.strip()]
    await state.update_data(hobby=hobbies)
    await message.answer(
        "Есть ли регулярные дела по дому? Напиши в формате:\n"
        "стирка среда, уборка суббота\n"
        "Или напиши «нет» если нет"
    )
    await state.set_state(Onboarding.chores)

# ── Шаг 13: Бытовые дела ─────────────────────────────

@router.message(Onboarding.chores)
async def step_chores(message: Message, state: FSMContext):
    text = message.text.strip()
    chores = {}
    if text.lower() != "нет":
        for part in text.split(","):
            part = part.strip()
            if " " in part:
                chore, day = part.rsplit(" ", 1)
                chores[day.strip()] = chore.strip()
    await state.update_data(chores=chores)
    await message.answer("Есть ли аллергии или проблемы со здоровьем? Напиши кратко или «нет»")
    await state.set_state(Onboarding.health)

# ── Шаг 14: Здоровье ─────────────────────────────────

@router.message(Onboarding.health)
async def step_health(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(health=text if text.lower() != "нет" else "")
    await message.answer(
        "Напиши любимые продукты (через запятую) и нелюбимые (после слова «не люблю»):\n"
        "авокадо, курица, гречка, не люблю лук, сало"
    )
    await state.set_state(Onboarding.food_pref)

# ── Шаг 15: Еда ──────────────────────────────────────

@router.message(Onboarding.food_pref)
async def step_food(message: Message, state: FSMContext):
    text = message.text.lower()
    loved = []
    hated = []
    
    if "не люблю" in text:
        parts = text.split("не люблю", 1)
        loved = [f.strip() for f in parts[0].split(",") if f.strip()]
        hated = [f.strip() for f in parts[1].split(",") if f.strip()]
    else:
        loved = [f.strip() for f in text.split(",") if f.strip()]
    
    await state.update_data(loved_food=loved, hated_food=hated)
    await message.answer(
        "Какая главная цель?",
        reply_markup=_kb("Похудеть", "Набрать вес", "Здоровье", "Больше энергии", "Другое")
    )
    await state.set_state(Onboarding.goal)

# ── Шаг 16: Цель ─────────────────────────────────────

@router.message(Onboarding.goal)
async def step_goal(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)
    await message.answer(
        "Какой бюджет на еду?",
        reply_markup=_kb("Эконом", "Средний", "Премиум")
    )
    await state.set_state(Onboarding.budget)

# ── Шаг 17: Бюджет ───────────────────────────────────

@router.message(Onboarding.budget)
async def step_budget(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await message.answer(
        "Последний вопрос! Что тебя радует, а что бесит?\n"
        "Напиши в формате:\n"
        "радует: прогулки, музыка, кофе\n"
        "бесит: пробки, критика, жара"
    )
    await state.set_state(Onboarding.mood_triggers)

# ── Шаг 18: Триггеры ─────────────────────────────────

@router.message(Onboarding.mood_triggers)
async def step_mood_triggers(message: Message, state: FSMContext):
    text = message.text.lower()
    makes_happy = []
    makes_angry = []
    
    if "радует:" in text:
        parts = text.split("радует:", 1)[1]
        if "бесит:" in parts:
            happy_part, angry_part = parts.split("бесит:", 1)
            makes_happy = [h.strip() for h in happy_part.split(",") if h.strip()]
            makes_angry = [a.strip() for a in angry_part.split(",") if a.strip()]
        else:
            makes_happy = [h.strip() for h in parts.split(",") if h.strip()]
    
    await state.update_data(
        makes_happy=makes_happy,
        makes_angry=makes_angry
    )
    
    # ── СОХРАНЕНИЕ В БД ─────────────────────────────
    data = await state.get_data()
    
    # Создаём пользователя
    user_id = await UserRepo.create(message.from_user.id)
    
    # Обновляем профиль
    await UserRepo.update(user_id,
        name=data.get("name"),
        age=data.get("age"),
        gender=data.get("gender"),
        weight=data.get("weight"),
        height=data.get("height"),
        wake_up=data.get("wake_up"),
        sleep_time=data.get("sleep_time"),
        sleep_hours=data.get("sleep_hours"),
        stress=data.get("stress"),
        activity=data.get("activity"),
    )
    
    # Сохраняем цель
    await GoalRepo.add(user_id, data.get("goal", ""))
    
    # ── ФИНАЛЬНОЕ СООБЩЕНИЕ ─────────────────────────
    await message.answer(
        f"✨ *{data.get('name', 'Подруга')}, спасибо что рассказала о себе!*\n\n"
        "Я запомнила:\n"
        f"🎯 Цель: {data.get('goal', '—')}\n"
        f"⏰ Подъём: {data.get('wake_up', '—')}\n"
        f"🌙 Отбой: {data.get('sleep_time', '—')}\n"
        f"💪 Активность: {data.get('activity', '—')}\n\n"
        "Завтра утром я начну помогать! А пока — посмотри команды в /help",
        parse_mode="Markdown",
        reply_markup=_kb("/menu", "/plan", "/help")
    )
    
    await state.clear()
    
    # Показываем постоянную клавиатуру
    await message.answer(
        "Используй кнопки внизу ⬇️",
        reply_markup=MAIN_KB
    )