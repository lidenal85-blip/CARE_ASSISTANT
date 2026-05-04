from keyboards.reply import MAIN_KB
"""
handlers/check.py — /check [продукт] — КБЖУ через Edamam
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import httpx
from app_config.settings import settings

router = Router()

@router.message(Command("check"))
async def cmd_check(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используй: /check куриная грудка")
        return
    
    query = parts[1].strip()
    
    if not settings.EDAMAM_NUTR_ID:
        await message.answer("API Edamam не настроен.")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.edamam.com/api/nutrition-data",
                params={
                    "app_id": settings.EDAMAM_NUTR_ID,
                    "app_key": settings.EDAMAM_NUTR_KEY,
                    "ingr": query,
                },
                timeout=10,
            )
            data = resp.json()
            
            cal = data.get("calories", 0)
            protein = data.get("totalNutrients", {}).get("PROCNT", {}).get("quantity", 0)
            fat = data.get("totalNutrients", {}).get("FAT", {}).get("quantity", 0)
            carbs = data.get("totalNutrients", {}).get("CHOCDF", {}).get("quantity", 0)
            
            await message.answer(
                f"🔍 *{query}* (на 100г):\n"
                f"🔥 {cal:.0f} ккал\n"
                f"💪 {protein:.1f}г белка\n"
                f"🧈 {fat:.1f}г жиров\n"
                f"🍞 {carbs:.1f}г углеводов",
                parse_mode="Markdown"
            )
    except Exception:
        await message.answer("❌ Не получилось проверить. Попробуй другой продукт.")
