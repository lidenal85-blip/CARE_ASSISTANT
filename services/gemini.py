"""services/gemini.py — Gemini с авто-fallback на Groq"""
import httpx, time, asyncio
from leviathan.core import get_pool, AllExhaustedError, KeyPoolExhaustedError
from leviathan.core.security import InputNormalizer, PromptFirewall, InputSanitizer

_normalizer = InputNormalizer()
_sanitizer = InputSanitizer()
_firewall = PromptFirewall()


import re

def extract_json_from_gemini(raw_text: str):
    """Извлекает JSON даже если Gemini добавил Markdown или комментарии"""
    try:
        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)
        if match:
            import json
            return json.loads(match.group(0))
        return json.loads(raw_text)
    except Exception:
        return None

class GeminiError(Exception): pass

# URL для разных провайдеров
API_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
}

async def ask(prompt: str, system: str = "", retries: int = 3) -> str:
    if not _firewall.check(prompt):
        raise GeminiError("Промт заблокирован")
    
    pool = get_pool()
    prompt = _normalizer.normalize(prompt)
    
    for attempt in range(retries):
        # Пробуем Gemini, при исчерпании — Groq
        try:
            entry, provider = pool.get_best(prefer="gemini")
        except AllExhaustedError as e:
            raise GeminiError(f"Все ключи заняты: {e}")
        
        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if provider == "gemini":
                    resp = await client.post(
                        API_URLS["gemini"],
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "systemInstruction": {"parts": [{"text": system}]} if system else None,
                        },
                        headers={"x-goog-api-key": entry.value, "Content-Type": "application/json"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
                        pool.report(entry, code=200, tokens=tokens, latency=time.monotonic()-t0, model="gemini-2.5-flash")
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                
                elif provider == "groq":
                    messages = [{"role": "user", "content": prompt}]
                    if system:
                        messages.insert(0, {"role": "system", "content": system})
                    resp = await client.post(
                        API_URLS["groq"],
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": messages,
                        },
                        headers={
                            "Authorization": f"Bearer {entry.value}",
                            "Content-Type": "application/json",
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        tokens = data.get("usage", {}).get("total_tokens", 0)
                        pool.report(entry, code=200, tokens=tokens, latency=time.monotonic()-t0, model="llama-3.3-70b")
                        return data["choices"][0]["message"]["content"]
                
                # Ошибка — репортим и пробуем следующий ключ
                pool.report(entry, code=resp.status_code, latency=time.monotonic()-t0)
                
                if resp.status_code in (429, 500, 502, 503) and attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
                
                raise GeminiError(f"{provider}: {resp.status_code}")
                
        except GeminiError:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(1)
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(1)
                continue
            raise GeminiError(f"Сеть: {str(e)[:100]}")
    
    raise GeminiError("Все попытки исчерпаны")
