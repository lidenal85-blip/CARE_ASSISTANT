"""
services/price_service.py — реальные цены через Open Food Facts + Numbeo
"""
import httpx

async def get_price_openfoodfacts(product: str, region: str = "russia") -> dict | None:
    """Поиск цены через Open Food Facts Prices."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://prices.openfoodfacts.org/api/v2/products",
                params={
                    "search_terms": product,
                    "cc": "ru",
                    "size": 3
                },
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            items = data.get("products", [])
            
            if not items:
                return None
            
            # Берём среднюю цену из первых 3 результатов
            prices = []
            for item in items:
                price_data = item.get("price", {})
                if price_data.get("price"):
                    prices.append(float(price_data["price"]))
            
            if prices:
                return {
                    "product": product,
                    "avg_price": round(sum(prices) / len(prices), 2),
                    "currency": "₽",
                    "source": "Open Food Facts",
                    "samples": len(prices)
                }
    except:
        pass
    
    return None


async def get_price_khabarovsk(product: str) -> dict:
    """Возвращает цену продукта в Хабаровске."""
    # Сначала пробуем Open Food Facts
    result = await get_price_openfoodfacts(product)
    
    if result:
        # Коэффициент Хабаровска (Дальний Восток дороже)
        result["price_khabarovsk"] = round(result["avg_price"] * 1.5)
        result["region"] = "Хабаровск"
        return result
    
    # Fallback: статические цены из нашей базы
    from services.price_checker import KHABAROVSK_PRICES
    
    for keyword, price in KHABAROVSK_PRICES.items():
        if keyword in product.lower():
            return {
                "product": product,
                "avg_price": price,
                "price_khabarovsk": price,
                "currency": "₽",
                "source": "локальная база (Хабаровск)",
                "region": "Хабаровск",
                "samples": 1
            }
    
    # Совсем не нашли — средняя цена
    return {
        "product": product,
        "avg_price": 200,
        "price_khabarovsk": 300,
        "currency": "₽",
        "source": "оценочно",
        "region": "Хабаровск",
        "samples": 0
    }
