"""
services/recipes.py — Spoonacular API (рецепты)
"""
import httpx
from app_config.settings import settings

async def find_recipes(ingredients: str, count: int = 3) -> list[dict]:
    """Ищет рецепты по ингредиентам."""
    if not settings.SPOONACULAR_KEY:
        return []
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.spoonacular.com/recipes/findByIngredients",
            params={
                "apiKey": settings.SPOONACULAR_KEY,
                "ingredients": ingredients,
                "number": count,
                "ranking": 1,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        return [
            {
                "title": r["title"],
                "image": r.get("image", ""),
                "used": [i["name"] for i in r.get("usedIngredients", [])],
                "missed": [i["name"] for i in r.get("missedIngredients", [])],
            }
            for r in data[:count]
        ]
