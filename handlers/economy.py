"""
handlers/economy.py — /economy — как сэкономить
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from services.gemini import ask

router = Router()

ECONOMY_SYSTEM = "Ты — финансовый консультант по питанию. Предлагаешь эконом-замены."

ECONOMY_PROMPT = """Проанализируй список покупок и предложи как сэкономить:

СПИСОК:
{items}

Предложи 3-5 замен которые сэкономят деньги без потери качества:
- лосось → минтай (экономия ~300₽)
- ...

Верни JSON:
{{
  "savings": [
    {{"original": "продукт", "replacement": "замена", "savings_rub": 300, "reason": "почему"}}
  ],
  "total_savings": 1200
}}
Только JSON."""

@router.message(Command("economy"))
async def cmd_economy(message: Message):
    from db.repository import UserRepo, ShoppingRepo
    from datetime import date, timedelta
    
    user = await UserRepo.get_by_telegram(message.from_user.id)
    if not user:
        return
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    items = await ShoppingRepo.get_week(user["id"], week_start.isoformat())
    
    if not items:
        await message.answer("Сначала создай список через 🥗 Диета")
        return
    
    items_text = "\n".join(f"- {i['item']}" for i in items)
    response = await ask(ECONOMY_PROMPT.format(items=items_text), ECONOMY_SYSTEM)
    
    await message.answer(f"💰 *Как сэкономить на этой неделе:*\n\n{response}", parse_mode="Markdown")
