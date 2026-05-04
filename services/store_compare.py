"""
services/store_compare.py — сравнение цен в магазинах
"""
import httpx

# Примерные цены по магазинам Хабаровска
STORE_PRICES = {
    "Пятёрочка": 0.9,   # -10% от средней
    "Магнит": 0.95,      # -5%
    "Лента": 1.1,        # +10%
    "Самбери": 1.05,     # +5%
}

async def compare_prices(shopping_list: list[dict], region: str = "Хабаровск") -> dict:
    """Сравнивает стоимость корзины в разных магазинах."""
    
    from services.price_service import get_price_khabarovsk
    
    store_totals = {}
    for store, coeff in STORE_PRICES.items():
        total = 0
        for item in shopping_list:
            price_info = await get_price_khabarovsk(item["item"])
            total += price_info.get("price_khabarovsk", 200) * coeff
        store_totals[store] = round(total)
    
    best = min(store_totals, key=store_totals.get)
    savings = store_totals[max(store_totals, key=store_totals.get)] - store_totals[best]
    
    return {
        "stores": store_totals,
        "best": best,
        "best_price": store_totals[best],
        "savings": savings,
        "region": region
    }

def format_store_comparison(data: dict) -> str:
    """Форматирует сравнение в читаемый текст."""
    text = f"🏪 *Где дешевле купить?* ({data['region']})\n\n"
    
    for store, price in sorted(data["stores"].items(), key=lambda x: x[1]):
        marker = "⭐" if store == data["best"] else "  "
        text += f"{marker} {store}: {price:,}₽\n"
    
    text += f"\n💡 *Вывод:* {data['best']} — экономия {data['savings']:,}₽"
    return text
