"""engine/onboarding_engine.py — Data-driven движок онбординга"""
import json
from pathlib import Path
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from states.onboarding import Onboarding
from db.repository import UserRepo, GoalRepo

class OnboardingEngine:
    def __init__(self, config_path: str = "config/onboarding.json"):
        self.config = json.loads(Path(config_path).read_text())
        self.router = Router()
        self._state_map = {}  # state_name → state_object
        self._build_handlers()
    
    def _kb(self, *buttons: str) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=b) for b in buttons]],
            resize_keyboard=True, one_time_keyboard=True)
    
    def _kb_skip(self, *buttons: str) -> ReplyKeyboardMarkup:
        rows = [[KeyboardButton(text=b) for b in buttons]]
        rows.append([KeyboardButton(text="Пропустить ➡️")])
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)
    
    def _build_handlers(self):
        """Создаёт обработчики для всех шагов из JSON"""
        all_steps = self.config["basic"] + self.config["extended"]
        
        for i, step in enumerate(all_steps):
            state = getattr(Onboarding, step["id"], None)
            if state is None:
                print(f"⚠ Нет состояния FSM для {step['id']}")
                continue
            
            self._state_map[step["id"]] = state
            next_step = all_steps[i + 1] if i + 1 < len(all_steps) else None
            self._register_step(state, step, next_step, is_last=(i == len(all_steps) - 1))
        
        # Кнопка расширенного профиля
        @self.router.message(F.text == "👤 Профиль")
        async def start_extended(message: Message, state: FSMContext):
            await state.clear()
            first = self.config["extended"][0]
            await message.answer(
                "📋 *Расширенный профиль*\nЭто улучшит меню и рекомендации.\nМожно пропускать вопросы кнопкой «Пропустить ➡️»",
                parse_mode="Markdown",
                reply_markup=self._kb_skip(*first.get("options", [])))
            await state.set_state(self._state_map[first["id"]])
    
    def _register_step(self, state, config: dict, next_step: dict | None, is_last: bool):
        """Регистрирует один шаг онбординга"""
        step_id = config["id"]
        step_type = config.get("type", "text")
        options = config.get("options", [])
        can_skip = config.get("skip", False)
        validate = config.get("validate")
        
        @self.router.message(state)
        async def handler(message: Message, state: FSMContext, 
                          _id=step_id, _next=next_step, _last=is_last,
                          _type=step_type, _opts=options, _skip=can_skip, _val=validate):
            
            # Пропуск
            if _skip and message.text == "Пропустить ➡️":
                pass  # не сохраняем
            else:
                # Валидация
                if _val == "int" and not message.text.strip().lstrip("-").isdigit():
                    await message.answer("Введи число 🥲")
                    return
                if _val == "float":
                    try:
                        float(message.text.strip().replace(",", "."))
                    except ValueError:
                        await message.answer("Введи число (например 65)")
                        return
                
                await state.update_data(**{_id: message.text.strip()})
            
            # Последний шаг?
            if _last:
                await self._finish_basic(message, state)
                return
            
            # Следующий шаг
            if _next:
                ask = _next.get("ask", "Дальше...")
                if _next.get("type") == "buttons":
                    kb = self._kb_skip(*_next.get("options", [])) if _next.get("skip") else self._kb(*_next.get("options", []))
                else:
                    kb = self._kb_skip() if _next.get("skip") else None
                
                await message.answer(ask, reply_markup=kb)
                await state.set_state(self._state_map[_next["id"]])
    
    async def _finish_basic(self, message: Message, state: FSMContext):
        """Завершение базовой анкеты"""
        data = await state.get_data()
        from keyboards.reply import MAIN_KB
        
        existing = await UserRepo.get_by_telegram(message.from_user.id)
        if existing:
            user_id = existing["id"]
        else:
            user_id = await UserRepo.create(message.from_user.id)
        await UserRepo.update(user_id,
            name=data.get("name"), age=data.get("age"),
            gender=data.get("gender"), weight=data.get("weight"),
            height=data.get("height"))
        await GoalRepo.add(user_id, data.get("goal", ""))
        
        # Рассчитываем BMR
        w, h, a = float(data.get("weight", 60)), float(data.get("height", 165)), float(data.get("age", 25))
        if data.get("gender") == "Женский":
            bmr = 447.6 + (9.2 * w) + (3.1 * h) - (4.3 * a)
        else:
            bmr = 88.36 + (13.4 * w) + (4.8 * h) - (5.7 * a)
        
        await message.answer(
            f"✨ *{data.get('name', 'Подруга')}, готово!*\n\n"
            f"🎯 Цель: {data.get('goal', '—')}\n"
            f"⚖️ Вес: {w} кг | Рост: {h} см\n"
            f"🔥 Базовый метаболизм: *{bmr:.0f} ккал/день*\n\n"
            "Используй кнопки внизу ⬇️\n"
            "💡 *Хочешь точнее меню?*\n"
            "Заполни расширенный профиль — кнопка «👤 Профиль»",
            parse_mode="Markdown", reply_markup=MAIN_KB)
        await state.clear()


# Синглтон
engine = OnboardingEngine()
router = engine.router
