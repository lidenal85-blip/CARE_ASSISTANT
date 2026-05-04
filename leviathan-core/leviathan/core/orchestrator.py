# ============================================
# core/key_pool.py
# DATE: 2026-04-01
# VERSION: 2.0.0
# SOURCE: Production KeyPool for LEVIATHAN
# ============================================
"""
KeyPool — Production-класс управления пулом API-ключей.

Алгоритм выбора ключа:
  Round-Robin среди доступных.
  Least-Error тайбрейкер: ключ с меньшим consecutive_429.

Cooldown:
  429 → Exponential Backoff: 60s × 2^N, max 3600s + jitter
  403 → 3600s
  5xx → 30s × 2^N, max 300s

Fallback: Gemini → Groq
"""
from __future__ import annotations

import math
import os
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..memory.storage import log

# ── Cooldown константы ────────────────────────────────────────────
COOLDOWN_429_BASE = 60.0
COOLDOWN_429_MAX  = 3600.0
COOLDOWN_429_JITTER = 0.10
COOLDOWN_403 = 3600.0
COOLDOWN_5XX_BASE = 30.0
COOLDOWN_5XX_MAX  = 300.0

# ── Exceptions ────────────────────────────────────────────────────
class KeyPoolExhaustedError(Exception):
    """Все ключи провайдера в cooldown."""
    pass

class AllExhaustedError(Exception):
    """Все ключи Gemini И Groq в cooldown."""
    pass

# ── KeyEntry ──────────────────────────────────────────────────────
@dataclass
class KeyEntry:
    key:              str
    index:            int
    provider:         str
    cooldown_until:   float = 0.0
    last_error:       Optional[int] = None
    calls_ok:         int = 0
    calls_err:        int = 0
    tokens_total:     int = 0
    consecutive_429:  int = 0
    consecutive_5xx:  int = 0
    last_used:        float = 0.0

    @property
    def available(self) -> bool:
        return bool(self.value) and time.time() >= self.cooldown_until

    @property
    def value(self) -> str:
        return self.key

    @property
    def cooldown_left(self) -> float:
        return max(0.0, self.cooldown_until - time.time())

    def on_success(self, tokens: int = 0) -> None:
        self.calls_ok += 1
        self.tokens_total += tokens
        self.last_used = time.time()
        self.last_error = None
        self.consecutive_429 = 0
        self.consecutive_5xx = 0

    def on_error(self, code: int) -> None:
        self.calls_err += 1
        self.last_error = code
        if code == 429:
            self.consecutive_429 += 1
            raw_wait = min(COOLDOWN_429_BASE * (2.0 ** (self.consecutive_429 - 1)), COOLDOWN_429_MAX)
            jitter = raw_wait * COOLDOWN_429_JITTER * (random.random() * 2 - 1)
            wait = max(1.0, raw_wait + jitter)
            self.cooldown_until = time.time() + wait
            log("KEY_POOL", f"{self.provider.upper()}_K{self.index}: 429 #{self.consecutive_429}", f"cooldown {wait:.0f}s", level="WARN")
        elif code == 403:
            self.cooldown_until = time.time() + COOLDOWN_403
            log("KEY_POOL", f"{self.provider.upper()}_K{self.index}: 403 (region/auth)", f"cooldown {COOLDOWN_403:.0f}s", level="WARN")
        elif code >= 500:
            self.consecutive_5xx += 1
            raw_wait = min(COOLDOWN_5XX_BASE * (2.0 ** (self.consecutive_5xx - 1)), COOLDOWN_5XX_MAX)
            self.cooldown_until = time.time() + raw_wait
            log("KEY_POOL", f"{self.provider.upper()}_K{self.index}: {code} (server error)", f"cooldown {raw_wait:.0f}s", level="WARN")

    def short(self) -> str:
        return self.key[:12] + "…" if len(self.key) > 12 else self.key

    def to_dict(self) -> dict:
        return {
            "index": self.index, "provider": self.provider,
            "short_key": self.short(), "available": self.available,
            "cooldown_sec": round(self.cooldown_left),
            "last_error": self.last_error, "calls_ok": self.calls_ok,
            "calls_err": self.calls_err, "tokens_total": self.tokens_total,
            "consecutive_429": self.consecutive_429,
        }

# ── ProviderPool ──────────────────────────────────────────────────
class ProviderPool:
    def __init__(self, provider: str, keys: list[str]) -> None:
        self.provider = provider
        self._entries: list[KeyEntry] = [
            KeyEntry(key=k, index=i + 1, provider=provider)
            for i, k in enumerate(keys)
        ]
        self._cursor = 0
        self._lock = threading.Lock()
        log("KEY_POOL", f"{provider.upper()}: инициализировано {len(self._entries)} ключей", "")

    @property
    def total(self) -> int:
        return len(self._entries)

    @property
    def available_count(self) -> int:
        return sum(1 for e in self._entries if e.available)

    @property
    def next_available_in(self) -> float:
        if self.available_count > 0:
            return 0.0
        return min((e.cooldown_left for e in self._entries), default=0.0)

    def get_key(self) -> KeyEntry:
        with self._lock:
            if not self._entries:
                raise KeyPoolExhaustedError(f"{self.provider}: ключи не добавлены")
            n = len(self._entries)
            available = []
            for i in range(n):
                e = self._entries[(self._cursor + i) % n]
                if e.available:
                    available.append(e)
            if not available:
                min_wait = self.next_available_in
                raise KeyPoolExhaustedError(f"{self.provider}: все {n} ключей в cooldown. Ближайший через {min_wait:.0f}с")
            chosen = min(available, key=lambda e: (e.consecutive_429, e.last_used))
            self._cursor = (self._entries.index(chosen) + 1) % n
            return chosen

    def report(self, entry: KeyEntry, code: int, tokens: int = 0) -> None:
        if code == 200:
            entry.on_success(tokens=tokens)
        else:
            entry.on_error(code)

    def status(self) -> dict:
        return {
            "total": self.total, "available": self.available_count,
            "next_avail_in": round(self.next_available_in),
            "keys": [e.to_dict() for e in self._entries],
        }

# ── KeyPool (Singleton) ───────────────────────────────────────────
class KeyPool:
    _instance: "KeyPool | None" = None
    _class_lock = threading.Lock()

    def __new__(cls) -> "KeyPool":
        with cls._class_lock:
            if cls._instance is None:
                obj = object.__new__(cls)
                obj._gemini: ProviderPool | None = None
                obj._groq: ProviderPool | None = None
                obj._ready = False
                cls._instance = obj
        return cls._instance

    def _load_env(self, prefix: str, max_n: int) -> list[str]:
        keys = [v for i in range(1, max_n + 1) if (v := os.environ.get(f"{prefix}_K{i}", "").strip())]
        if not keys:
            csv = os.environ.get(f"{prefix}_API_KEYS", "")
            keys = [k.strip() for k in csv.split(",") if k.strip()]
        return keys

    def init(self) -> "KeyPool":
        if self._ready:
            return self
        self._gemini = ProviderPool("gemini", self._load_env("GEMINI", 14))
        self._groq = ProviderPool("groq", self._load_env("GROQ", 5))
        self._ready = True
        return self

    def get_best(self, prefer: str = "gemini") -> tuple[KeyEntry, str]:
        self.init()
        primary = self._gemini if prefer == "gemini" else self._groq
        secondary = self._groq if prefer == "gemini" else self._gemini
        sec_name = "groq" if prefer == "gemini" else "gemini"
        try:
            return primary.get_key(), prefer
        except KeyPoolExhaustedError:
            pass
        try:
            return secondary.get_key(), sec_name
        except KeyPoolExhaustedError as exc:
            min_wait = min(self._gemini.next_available_in, self._groq.next_available_in)
            raise AllExhaustedError(f"Все ключи в cooldown. Ближайший через {min_wait:.0f}с")

    def report(self, entry: KeyEntry, code: int, tokens: int = 0, latency: float = 0.0, model: str = "") -> None:
        self.init()
        pool = self._gemini if entry.provider == "gemini" else self._groq
        pool.report(entry, code, tokens)

    def status(self) -> dict:
        self.init()
        return {"gemini": self._gemini.status(), "groq": self._groq.status()}

    def __repr__(self) -> str:
        if not self._ready:
            return "KeyPool(not initialized)"
        g = self._gemini; r = self._groq
        return f"KeyPool(gemini={g.available_count}/{g.total}, groq={r.available_count}/{r.total})"

# ── Singleton accessor ────────────────────────────────────────────
_pool: Optional[KeyPool] = None

def get_pool() -> KeyPool:
    global _pool
    if _pool is None:
        _pool = KeyPool().init()
    return _pool
