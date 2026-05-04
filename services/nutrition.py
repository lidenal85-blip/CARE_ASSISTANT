"""
services/nutrition.py — Edamam Nutrition API
"""
import httpx
from app_config.settings import settings

async def analyze_food(query: str) -> dict:
    """Возвращает КБЖУ продукта через Edamam."""
    if not settings.EDAMAM_NUTR_ID:
        return {"error": "API не настроен"}
    
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
        
        return {
            "calories": data.get("calories", 0),
            "protein": data.get("totalNutrients", {}).get("PROCNT", {}).get("quantity", 0),
            "fat": data.get("totalNutrients", {}).get("FAT", {}).get("quantity", 0),
            "carbs": data.get("totalNutrients", {}).get("CHOCDF", {}).get("quantity", 0),
        }
