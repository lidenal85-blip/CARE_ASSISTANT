"""
memory/storage.py — Logging module for LEVIATHAN Core
Replacement for original memory.storage.log
"""
import threading
from datetime import datetime
from pathlib import Path
import os

_log_buffer: list[str] = []
_log_lock = threading.Lock()
_LOG_BUF_MAX = 50

def log(category: str, msg: str, detail: str = "", level: str = "INFO") -> None:
    """Логирует сообщение в консоль и буфер."""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {category}: {msg} {detail}".strip()
    print(f"  {line}")
    
    # Буферизация для API usage логов
    if category == "KEY_POOL" or "API" in category:
        with _log_lock:
            _log_buffer.append(line)
            if len(_log_buffer) >= _LOG_BUF_MAX:
                _flush_log()

def _flush_log() -> None:
    """Сброс буфера в файл."""
    try:
        log_dir = Path(os.getenv("LEVIATHAN_LOG_DIR", "/tmp/leviathan_logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "api_usage.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n".join(_log_buffer) + "\n")
        _log_buffer.clear()
    except OSError:
        pass
