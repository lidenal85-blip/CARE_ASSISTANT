"""Input Normalizer — NFKC + фильтрация"""
import unicodedata
import re

class InputNormalizer:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
    
    def normalize(self, text: str) -> str:
        if not text:
            return ""
        
        # NFKC — унификация символов
        text = unicodedata.normalize('NFKC', text)
        
        # Удаление непечатных символов
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Схлопывание пробелов
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
