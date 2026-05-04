"""
DOCTOR SYSTEM v10 — автономный агент лечения Python-проектов
"""
import ast, sys, os, shutil, time, httpx, subprocess
from pathlib import Path
from datetime import datetime

G='\033[32m'; R='\033[31m'; Y='\033[33m'; C='\033[36m'; B='\033[1m'; X='\033[0m'

class DoctorSystem:
    def __init__(self, project_root: Path | str):
        self.ROOT = Path(project_root)
        self.LOG = self.ROOT / "data" / "doctor.log"
        self.PID_FILE = self.ROOT / "data" / "server.pid"
        self.LOG.parent.mkdir(parents=True, exist_ok=True)
        self.key = self._find_key()
        self.attempt = 0
        self.failed_files = {}
    
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
        errors = []
        for f in sorted(self.ROOT.rglob("*.py")):
            if '__pycache__' in str(f) or 'sandbox' in str(f) or 'backups' in str(f) or 'leviathan-core' in str(f):
                continue
            try:
                ast.parse(f.read_text())
            except SyntaxError as e:
                errors.append({"file": f, "error": e})
        return errors
    
    def heal_with_gemini(self, filepath, error):
        content = filepath.read_text()
        prompt = f"""Fix the ONLY syntax error in this Python file.

FILE: {filepath.name}
ERROR at line {error.lineno}: {error.msg}

=== FULL FILE ===
{content}
=== END ===

Return the complete fixed file in ```python ... ``` block. 
Fix ONLY the syntax error. Do NOT change logic."""
        
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
    
    def heal_all(self, errors):
        fixed = 0
        for e in errors:
            f = e["file"]
            f_str = str(f)
            self.failed_files[f_str] = self.failed_files.get(f_str, 0) + 1
            
            if self.failed_files[f_str] > 3:
                self.log(f"⛔ {f.name} — пропускаем (3 попытки)", R)
                continue
            
            err = e["error"]
            self.log(f"🔧 Лечу {f.name}:{err.lineno}...", Y)
            
            bkp_dir = self.ROOT / "data" / "backups"
            bkp_dir.mkdir(parents=True, exist_ok=True)
            bkp = bkp_dir / f"{f.name}.{datetime.now():%Y%m%d_%H%M%S}.bak"
            shutil.copy2(f, bkp)
            
            fixed_content = self.heal_with_gemini(f, err)
            if fixed_content:
                f.write_text(fixed_content)
                try:
                    ast.parse(fixed_content)
                    self.log(f"✅ ВЫЛЕЧЕНО: {f.name}", G)
                    fixed += 1
                    continue
                except SyntaxError:
                    shutil.copy2(bkp, f)
            
            lines = f.read_text().split("\n")
            lineno = max(0, err.lineno - 1)
            lines[lineno] = f"# [DOCTOR] removed: {lines[lineno].strip()[:50]}"
            f.write_text("\n".join(lines))
            try:
                ast.parse(f.read_text())
                self.log(f"⚠ Удалена строка {f.name}:{err.lineno}", Y)
                fixed += 1
            except SyntaxError:
                shutil.copy2(bkp, f)
                self.log(f"❌ Не вылечено: {f.name}", R)
        
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
            self.log(f"   {e['file'].name}:{e['error'].lineno}: {e['error'].msg}", R)
        
        fixed = self.heal_all(errors)
        self.log(f"💊 Вылечено: {fixed}/{len(errors)}", G if fixed == len(errors) else Y)
        return fixed == len(errors)
    
    def watch(self, interval: int = 30):
        """Бесконечный цикл наблюдения и auto-heal."""
        self.log("👁 АВТОПИЛОТ ЗАПУЩЕН", C)
        self.log(f"   Интервал проверки: {interval} сек", "")
        self.log("   Доктор сам найдёт, вылечит, перезапустит", "")
        
        while True:
            try:
                errors = self.scan_all()
                if errors:
                    self.log(f"⚠ Найдено ошибок: {len(errors)}", Y)
                    self.run_once()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.log("⏹ АВТОПИЛОТ ОСТАНОВЛЕН", Y)
                break
            except Exception as e:
                self.log(f"💥 Сбой: {e}", R)
                time.sleep(10)
