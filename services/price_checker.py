"""
services/price_checker.py — Цены на продукты по регионам
API: Российские ритейлеры + агрегаторы цен
"""
import httpx
from datetime import datetime

# Средние цены по Хабаровску (руб/кг или руб/шт)
# Обновляется через API или вручную
KHABAROVSK_PRICES = {
    "куриная грудка": 420, "курица": 380, "филе куриное": 450,
    "говядина": 650, "свинина": 450, "фарш": 400,
    "лосось": 1200, "минтай": 300, "треска": 500,
    "яйца": 120, "яйцо": 12,  # за десяток
    "молоко": 90, "кефир": 85, "йогурт": 45, "творог": 350,
    "сыр": 800, "масло сливочное": 900,
    "гречка": 90, "рис": 100, "овсянка": 80, "макароны": 70,
    "картофель": 60, "морковь": 70, "лук": 55,
    "помидоры": 250, "огурцы": 200, "перец": 300,
    "капуста": 80, "брокколи": 350,
    "бананы": 150, "яблоки": 130, "апельсины": 180,
    "хлеб": 60, "батон": 55,
    "авокадо": 350, "орехи": 900, "мёд": 500,
    "оливковое масло": 900, "подсолнечное": 150,
}

async def get_prices_for_shopping_list(shopping_items: list[dict], region: str = "Хабаровск") -> dict:
    """
    Добавляет цены к списку покупок.
    
    Args:
        shopping_items: [{"item": "Куриная грудка", "amount": "1 кг"}, ...]
        region: "Хабаровск", "Москва", "Владивосток"
    
    Returns:
        {'items': [...с ценами...], 'total': 4500, 'region': 'Хабаровск'}
    """
    
    # Коэффициенты по регионам (к среднему по РФ)
    region_coeffs = {
        "Москва": 1.3,
        "Санкт-Петербург": 1.2,
        "Хабаровск": 1.5,        # Дальний Восток — дороже
        "Владивосток": 1.5,
        "Новосибирск": 1.1,
        "Краснодар": 0.9,
        "средний": 1.0,
    }
    
    coeff = region_coeffs.get(region, 1.0)
    
    priced_items = []
    total = 0
    
    for item in shopping_items:
        item_name = item.get("item", "").strip().lower()
        
        # Ищем цену в базе
        price = None
        for keyword, p in KHABAROVSK_PRICES.items():
            if keyword in item_name:
                price = p
                break
        
        if price is None:
            price = 200  # средняя цена если не нашли
        
        # Применяем коэффициент региона
        regional_price = round(price * coeff)
        
        # Парсим количество
        amount_str = item.get("amount", "1 кг")
        amount_num = 1.0
        if "кг" in amount_str:
            try:
                amount_num = float(amount_str.replace("кг", "").strip())
            except:
                amount_num = 1.0
        elif "шт" in amount_str or "десяток" in amount_str:
            try:
                amount_num = float(amount_str.replace("шт", "").replace("десяток", "").strip())
            except:
                amount_num = 1.0
        
        item_total = round(regional_price * amount_num)
        total += item_total
        
        priced_items.append({
            "item": item["item"],
            "amount": amount_str,
            "price_per_unit": regional_price,
            "total": item_total
        })
    
    return {
        "items": sorted(priced_items, key=lambda x: x["total"], reverse=True),
        "total": total,
        "region": region,
        "date": datetime.now().strftime("%d.%m.%Y"),
    }
