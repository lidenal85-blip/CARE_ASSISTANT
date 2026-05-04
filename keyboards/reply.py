from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def mk_kb(*buttons: str, row_width: int = 2) -> ReplyKeyboardMarkup:
    rows = []
    for i in range(0, len(buttons), row_width):
        rows.append([KeyboardButton(text=b) for b in buttons[i:i+row_width]])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🥗 Диета"), KeyboardButton(text="🍽 Меню")],
        [KeyboardButton(text="🍳 Рецепты"), KeyboardButton(text="💧 Вода")],
        [KeyboardButton(text="😊 Настроение"), KeyboardButton(text="🛒 Покупки")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📋 План"), KeyboardButton(text="📝 Отзыв")],
    ],
    resize_keyboard=True
)

GENDER_KB = mk_kb("Женский", "Мужской")
WORK_KB = mk_kb("5/2 Офис", "Удалёнка", "Сменный", "Учёба", "Не работаю")
SLEEP_KB = mk_kb("<6 часов", "7-8 часов", "9+ часов")
STRESS_KB = mk_kb("Низкий", "Средний", "Высокий")
ACTIVITY_KB = mk_kb("Сидячая", "1-2 тренировки", "3+ тренировок")
GOAL_KB = mk_kb("Похудеть", "Набрать вес", "Здоровье", "Больше энергии")
BUDGET_KB = mk_kb("Эконом", "Средний", "Премиум")
