#!/usr/bin/env python3
"""
DOCTOR SYSTEM v9 — ПОЛНЫЙ АВТОМАТ
Находит → Лечит → Перезапускает → Мониторит → Повторяет
Ты пьёшь кофе. Доктор работает.
"""
import ast, sys, os, shutil, time, httpx, subprocess, signal
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

G='\033[32m';R='\033[31m';Y='\033[33m';C='\033[36m';B='\033[1m';X='\033[0m'
LOG = ROOT / "data" / "doctor.log"
PID_FILE = ROOT / "data" / "server.pid"

def log(msg, color=""):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {color}[{ts}] {msg}{X}")
    with open(LOG, "a") as f: f.write(f"[{ts}] {msg}\n")

class DoctorSystem:
    def __init__(self):
        LOG.parent.mkdir(parents=True, exist_ok=True)
        self.key = self._find_key()
        self.server_process = None
        self.attempt = 0
    
    def _find_key(self):
        for i in range(1, 15):
            k = os.getenv(f"GEMINI_K{i}", "")
            if k and len(k) > 10: return k
        return None
    
    def scan_all(self):
        """Сканирует ВСЕ .py файлы в проекте."""
        errors = []
        for f in sorted(ROOT.rglob("*.py")):
            if '__pycache__' in str(f) or 'sandbox' in str(f) or 'backups' in str(f):
                continue
            try:
                ast.parse(f.read_text())
            except SyntaxError as e:
                errors.append({"file": f, "error": e})
        return errors
    
    def heal_with_gemini(self, filepath, error):
        """Gemini получает файл целиком и возвращает исправленный."""
        content = filepath.read_text()
        
        prompt = f"""Fix the ONLY syntax error in this Python file.

FILE: {filepath.name}
ERROR at line {error.lineno}: {error.msg}

=== FULL FILE ===
{content}
=== END ===

Return the complete fixed file in ```python ... ``` block. 
Fix ONLY the syntax error. Do NOT change logic, imports, or variable names."""
        
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
            log(f"Gemini error: {e}", R)
        return None
    
    def heal_all(self, errors):
        """Лечит все ошибки. Возвращает количество вылеченных."""
        fixed = 0
        for e in errors:
            f = e["file"]
            err = e["error"]
            log(f"🔧 Лечу {f.name}:{err.lineno}...", Y)
            
            # Бэкап
            bkp_dir = ROOT / "data" / "backups"
            bkp_dir.mkdir(parents=True, exist_ok=True)
            bkp = bkp_dir / f"{f.name}.{datetime.now():%Y%m%d_%H%M%S}.bak"
            shutil.copy2(f, bkp)
            
            # Gemini
            fixed_content = self.heal_with_gemini(f, err)
            if fixed_content:
                f.write_text(fixed_content)
                try:
                    ast.parse(fixed_content)
                    log(f"✅ ВЫЛЕЧЕНО: {f.name}", G)
                    fixed += 1
                    continue
                except SyntaxError:
                    shutil.copy2(bkp, f)  # откат
            
            # Если Gemini не помог — удаляем проблемную строку
            lines = f.read_text().split("\n")
            lineno = max(0, err.lineno - 1)
            lines[lineno] = f"# [DOCTOR] removed: {lines[lineno].strip()[:50]}"
            f.write_text("\n".join(lines))
            try:
                ast.parse(f.read_text())
                log(f"⚠ Удалена строка {f.name}:{err.lineno}", Y)
                fixed += 1
            except SyntaxError:
                shutil.copy2(bkp, f)
                log(f"❌ Не вылечено: {f.name}", R)
        
        return fixed
    
    def start_server(self):
        """Запускает main.py как фоновый процесс."""
        if self.server_process and self.server_process.poll() is None:
            return  # уже запущен
        
        log("🚀 ЗАПУСК СЕРВЕРА...", C)
        self.server_process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        time.sleep(2)
        
        if self.server_process.poll() is None:
            log("✅ СЕРВЕР РАБОТАЕТ", G)
            PID_FILE.write_text(str(self.server_process.pid))
        else:
            stderr = self.server_process.stderr.read().decode()
            log(f"❌ СЕРВЕР УПАЛ: {stderr[:200]}", R)
    
    def stop_server(self):
        """Останавливает сервер."""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
            self.server_process = None
            log("⏹ СЕРВЕР ОСТАНОВЛЕН", Y)
    
    def check_server_alive(self):
        """Проверяет жив ли сервер."""
        if self.server_process and self.server_process.poll() is not None:
            stderr = self.server_process.stderr.read().decode() if self.server_process.stderr else ""
            log(f"💀 СЕРВЕР УМЕР: {stderr[:150]}", R)
            return False
        return self.server_process is not None
    
    def run_once(self):
        """Один цикл: сканировать → лечить → перезапустить."""
        self.attempt += 1
        log(f"🔄 ЦИКЛ #{self.attempt}", C)
        
        errors = self.scan_all()
        
        if not errors:
            log("✅ Ошибок нет", G)
            if not self.check_server_alive():
                self.start_server()
            return True
        
        log(f"🐛 Найдено ошибок: {len(errors)}", Y)
        for e in errors:
            log(f"   {e['file'].name}:{e['error'].lineno}: {e['error'].msg}", R)
        
        # Останавливаем сервер перед лечением
        self.stop_server()
        
        # Лечим
        fixed = self.heal_all(errors)
        log(f"💊 Вылечено: {fixed}/{len(errors)}", G if fixed == len(errors) else Y)
        
        # Перезапускаем
        self.start_server()
        
        return fixed == len(errors)
    
    def watch(self):
        """Бесконечный цикл: проверка → лечение → перезапуск."""
        log("👁 АВТОПИЛОТ ЗАПУЩЕН", C)
        log("   Доктор сам найдёт, вылечит, перезапустит", "")
        log("   Пей кофе ☕", "")
        
        # Сразу запускаем сервер
        self.start_server()
        
        while True:
            try:
                time.sleep(30)
                
                # Проверяем жив ли сервер
                if not self.check_server_alive():
                    log("🔄 Сервер упал, запускаю...", Y)
                    self.run_once()
                else:
                    # Проверяем есть ли новые ошибки
                    errors = self.scan_all()
                    if errors:
                        log(f"⚠ Новые ошибки: {len(errors)}", Y)
                        self.run_once()
                    
            except KeyboardInterrupt:
                log("⏹ АВТОПИЛОТ ОСТАНОВЛЕН", Y)
                self.stop_server()
                break
            except Exception as e:
                log(f"💥 Сбой: {e}", R)
                time.sleep(10)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    
    d = DoctorSystem()
    
    if '--watch' in sys.argv:
        d.watch()
    else:
        d.run_once()
        # После разового лечения запускаем сервер если ещё не
        if not d.check_server_alive():
            d.start_server()
        log("☕ Пей кофе. Доктор закончил.", G)
