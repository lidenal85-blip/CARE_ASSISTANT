"""
DOCTOR SYSTEM v11 — автономный агент лечения Python-проектов
SmartPatcher (AST) + Gemini (LLM) = двухуровневое лечение
"""
import ast, sys, os, shutil, time, httpx
from pathlib import Path
from datetime import datetime
from .smart_patcher import SmartPatcher

G='\033[32m'; R='\033[31m'; Y='\033[33m'; C='\033[36m'; B='\033[1m'; X='\033[0m'

class DoctorSystem:
    def __init__(self, project_root: Path | str):
        self.ROOT = Path(project_root)
        self.LOG = self.ROOT / "data" / "doctor.log"
        self.LOG.parent.mkdir(parents=True, exist_ok=True)
        self.key = self._find_key()
        self.attempt = 0
        self.failed_files = {}
        self.patcher = SmartPatcher(str(self.ROOT))  # ← SmartPatcher!
    
    def _find_key(self):
        for i in range(1, 15):
            k = os.getenv(f"GEMINI_K{i}", "")
            if k and len(k) > 10:
                return k
        return None
    
    def log(self, msg, color=""):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  {color}[{ts}] {msg}{X}")
        with open(self.LOG, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    
    def scan_all(self):
        """Сканирует все .py файлы через AST"""
        errors = []
        for f in sorted(self.ROOT.rglob("*.py")):
            if any(x in str(f) for x in ['__pycache__', 'sandbox', 'backups', '.egg-info', 'leviathan-core']):
                continue
            try:
                ast.parse(f.read_text())
            except SyntaxError as e:
                errors.append({
                    "file": f,
                    "error": e,
                    "type": self._classify_error(e)
                })
        return errors
    
    def _classify_error(self, error: SyntaxError) -> str:
        """Классифицирует ошибку: patcher или gemini"""
        msg = error.msg.lower()
        # Ошибки которые патчер может исправить сам
        if any(x in msg for x in ['indentation', 'unexpected indent', 'expected an indented block']):
            return "indent"
        if any(x in msg for x in ['eof', 'unexpected eof', 'unterminated']):
            return "bracket"
        if any(x in msg for x in [':', 'missing', 'invalid syntax']):
            return "syntax_simple"
        # Сложные ошибки — только Gemini
        return "complex"
    
    # ── Уровень 1: SmartPatcher (AST, быстро, без API) ──
    
    def heal_with_patcher(self, filepath: Path, error: SyntaxError, error_type: str) -> bool:
        """Пробует исправить ошибку через AST-патчер"""
        self.log(f"🔧 Патчер: {filepath.name}:{error.lineno} ({error_type})...", C)
        
        try:
            rel_path = str(filepath.relative_to(self.ROOT))
            
            if error_type == "indent":
                # Исправляем отступы — берём соседнюю строку и выравниваем
                lines = filepath.read_text().split("\n")
                lineno = error.lineno - 1
                if lineno > 0:
                    # Берём отступ предыдущей строки
                    prev = lines[lineno - 1] if lineno > 0 else ""
                    prev_indent = len(prev) - len(prev.lstrip())
                    
                    # Текущая строка — добавляем правильный отступ
                    cur = lines[lineno].lstrip()
                    lines[lineno] = " " * prev_indent + cur
                    filepath.write_text("\n".join(lines))
                    
                    try:
                        ast.parse(filepath.read_text())
                        self.log(f"✅ Патчер исправил: {filepath.name}", G)
                        return True
                    except SyntaxError:
                        pass
            
            elif error_type == "bracket":
                # Ищем незакрытые скобки
                content = filepath.read_text()
                for char, close in [('(', ')'), ('[', ']'), ('{', '}')]:
                    if content.count(char) > content.count(close):
                        content += "\n" + close * (content.count(char) - content.count(close))
                        filepath.write_text(content)
                        try:
                            ast.parse(filepath.read_text())
                            self.log(f"✅ Патчер закрыл скобки: {filepath.name}", G)
                            return True
                        except SyntaxError:
                            pass
            
            elif error_type == "syntax_simple":
                # Удаляем проблемную строку (последнее средство)
                lines = filepath.read_text().split("\n")
                lineno = max(0, error.lineno - 1)
                lines[lineno] = f"# [DOCTOR] removed: {lines[lineno].strip()[:50]}"
                filepath.write_text("\n".join(lines))
                try:
                    ast.parse(filepath.read_text())
                    self.log(f"⚠ Патчер удалил строку: {filepath.name}:{error.lineno}", Y)
                    return True
                except SyntaxError:
                    pass
            
            return False
            
        except Exception as e:
            self.log(f"❌ Патчер ошибка: {e}", R)
            return False
    
    # ── Уровень 2: Gemini (LLM, медленно, тратит ключи) ──
    
    def heal_with_gemini(self, filepath: Path, error: SyntaxError) -> str | None:
        """Отправляет файл в Gemini для исправления"""
        content = filepath.read_text()
        prompt = f"""Fix the ONLY syntax error in this Python file.

FILE: {filepath.name}
ERROR at line {error.lineno}: {error.msg}

=== FULL FILE ===
{content}
=== END ===

Return the complete fixed file in ```python ... ``` block."""
        
        try:
            resp = httpx.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                params={"key": self.key},
                timeout=30,
            )
            if resp.status_code == 200:
                result = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                if "```" in result:
                    result = result.split("```")[1]
                    if result.startswith("python"): result = result[6:]
                    result = result.strip()
                if result and result != content:
                    return result
        except Exception as e:
            self.log(f"Gemini error: {e}", R)
        return None
    
    # ── Главный цикл лечения ─────────────────────────
    
    def heal_all(self, errors: list) -> int:
        """
        Двухуровневое лечение:
        1. SmartPatcher (AST) — быстро, без API
        2. Gemini (LLM) — только для сложных случаев
        """
        fixed = 0
        
        for e in errors:
            f = e["file"]
            f_str = str(f)
            self.failed_files[f_str] = self.failed_files.get(f_str, 0) + 1
            
            if self.failed_files[f_str] > 3:
                self.log(f"⛔ {f.name} — пропускаем (3 попытки)", R)
                continue
            
            err = e["error"]
            err_type = e["type"]
            
            # Бэкап
            bkp_dir = self.ROOT / "data" / "backups"
            bkp_dir.mkdir(parents=True, exist_ok=True)
            bkp = bkp_dir / f"{f.name}.{datetime.now():%Y%m%d_%H%M%S}.bak"
            shutil.copy2(f, bkp)
            
            # ── Уровень 1: Патчер ──
            if self.heal_with_patcher(f, err, err_type):
                fixed += 1
                continue
            
            # ── Уровень 2: Gemini ──
            self.log(f"🤖 Gemini: {f.name}:{err.lineno}...", Y)
            fixed_content = self.heal_with_gemini(f, err)
            
            if fixed_content:
                f.write_text(fixed_content)
                try:
                    ast.parse(fixed_content)
                    self.log(f"✅ Gemini исправил: {f.name}", G)
                    fixed += 1
                    continue
                except SyntaxError:
                    shutil.copy2(bkp, f)
                    self.log(f"❌ Gemini не помог: {f.name}", R)
            else:
                self.log(f"❌ Gemini недоступен: {f.name}", R)
        
        return fixed
    
    def run_once(self):
        self.attempt += 1
        self.log(f"🔄 ЦИКЛ #{self.attempt}", C)
        errors = self.scan_all()
        
        if not errors:
            self.log("✅ Ошибок нет", G)
            return True
        
        self.log(f"🐛 Найдено ошибок: {len(errors)}", Y)
        for e in errors:
            self.log(f"   {e['file'].name}:{e['error'].lineno}: {e['error'].msg} [{e['type']}]", R)
        
        fixed = self.heal_all(errors)
        self.log(f"💊 Вылечено: {fixed}/{len(errors)} (Патчер+Gemini)", G if fixed == len(errors) else Y)
        return fixed == len(errors)
    
    def watch(self, interval: int = 30):
        """Бесконечный цикл наблюдения"""
        self.log("👁 АВТОПИЛОТ v11 (Патчер+Gemini)", C)
        self.log(f"   Интервал: {interval}с", "")
        
        while True:
            try:
                errors = self.scan_all()
                if errors:
                    self.log(f"⚠ Ошибок: {len(errors)}", Y)
                    self.run_once()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.log("⏹ ОСТАНОВЛЕН", Y)
                break
            except Exception as e:
                self.log(f"💥 Сбой: {e}", R)
                time.sleep(10)
