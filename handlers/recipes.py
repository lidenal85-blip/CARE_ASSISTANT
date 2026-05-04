"""
handlers/recipes.py — 🍳 Рецепты — поиск по ингредиентам
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from services.recipes import find_recipes

router = Router()

@router.message(Command("recipes"))
async def cmd_recipes(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "🍳 *Рецепты*\n\n"
            "Напиши что есть в холодильнике, и я найду рецепты.\n"
            "Например: /recipes курица помидоры сыр",
            parse_mode="Markdown"
        )
        return
    
    ingredients = parts[1].strip()
    await message.answer(f"🔍 Ищу рецепты с: {ingredients}...")
    
    recipes = await find_recipes(ingredients)
    
    if not recipes:
        await message.answer("❌ Не нашла рецептов. Попробуй другие ингредиенты.")
        return
    
    text = f"🍳 *Рецепты с {ingredients}*\n\n"
    for r in recipes:
        text += f"*{r['title']}*\n"
        text += f"✅ Есть: {', '.join(r['used'])}\n"
        text += f"📋 Нужно: {', '.join(r['missed'])}\n\n"
    
    await message.answer(text, parse_mode="Markdown")
