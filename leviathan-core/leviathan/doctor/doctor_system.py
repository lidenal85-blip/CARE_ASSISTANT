"""DOCTOR SYSTEM v12 — с нормализацией ошибок и авторолбэком"""
import ast, hashlib, json, os, re, shutil, time, httpx
from datetime import datetime
from pathlib import Path
from .smart_patcher import SmartPatcher
from .knowledge_base import KnowledgeBase

G='\033[32m'; R='\033[31m'; Y='\033[33m'; C='\033[36m'; X='\033[0m'

_DANGEROUS_PATTERNS = re.compile(r'(subprocess\.|os\.system|os\.popen|eval\(|exec\(|__import__)', re.IGNORECASE)

_NORMALIZE_MAP = [
    (re.compile(r"was never closed", re.I), "bracket_never_closed"),
    (re.compile(r"unexpected eof", re.I), "bracket_eof"),
    (re.compile(r"eof in multi.line", re.I), "bracket_eof"),
    (re.compile(r"unterminated", re.I), "bracket_eof"),
    (re.compile(r"indentation", re.I), "indent"),
    (re.compile(r"unexpected indent", re.I), "indent"),
    (re.compile(r"expected an indented block", re.I), "indent"),
    (re.compile(r"invalid syntax", re.I), "syntax_simple"),
    (re.compile(r"missing", re.I), "syntax_simple"),
]

def _normalize_error_msg(msg: str) -> str:
    for pattern, canonical in _NORMALIZE_MAP:
        if pattern.search(msg):
            return canonical
    return "complex"

class KeyPool:
    def __init__(self):
        self._keys = []
        self._blocked = {}
        self._idx = 0
        for i in range(1, 15):
            k = os.getenv(f"GEMINI_K{i}", "").strip()
            if k and len(k) > 10:
                self._keys.append(k)
    
    def next(self):
        now = time.time()
        for _ in range(len(self._keys)):
            key = self._keys[self._idx % len(self._keys)]
            self._idx += 1
            if self._blocked.get(key, 0) < now:
                return key
        return None
    
    def block(self, key, seconds=60):
        self._blocked[key] = time.time() + seconds
    
    def __bool__(self):
        return bool(self._keys)

class DoctorSystem:
    EXCLUDE = ('__pycache__', 'sandbox', 'backups', '.egg-info', 'leviathan-core')
    
    def __init__(self, project_root):
        self.ROOT = Path(project_root)
        self.LOG = self.ROOT / "data" / "doctor.log"
        self.LOG.parent.mkdir(parents=True, exist_ok=True)
        self.attempt = 0
        self.failed_files = {}
        self.patcher = SmartPatcher(str(self.ROOT))
        self.kb = KnowledgeBase(self.ROOT / "data" / "doctor_knowledge.json")
        self.keys = KeyPool()
    
    def log(self, msg, color=""):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  {color}[{ts}] {msg}{X}")
        with open(self.LOG, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    
    def _classify_error(self, error):
        canonical = _normalize_error_msg(error.msg)
        return "bracket" if canonical.startswith("bracket") else canonical
    
    def scan_all(self):
        errors = []
        for f in sorted(self.ROOT.rglob("*.py")):
            if any(x in str(f) for x in self.EXCLUDE):
                continue
            try:
                ast.parse(f.read_text())
            except SyntaxError as e:
                errors.append({"file": f, "error": e, "type": self._classify_error(e)})
        return errors
    
    def _backup(self, filepath):
        bkp_dir = self.ROOT / "data" / "backups"
        bkp_dir.mkdir(parents=True, exist_ok=True)
        bkp = bkp_dir / f"{filepath.name}.{datetime.now():%Y%m%d_%H%M%S}.bak"
        shutil.copy2(filepath, bkp)
        return bkp
    
    def _rollback(self, filepath, bkp):
        shutil.copy2(bkp, filepath)
        self.log(f"⏪ Откат: {filepath.name}", Y)
    
    def heal_with_patcher(self, filepath, error, error_type):
        self.log(f"🔧 Патчер: {filepath.name}:{error.lineno} [{error_type}]", C)
        bkp = self._backup(filepath)
        try:
            if error_type == "indent":
                if not self.patcher.fix_indent(str(filepath), error.lineno):
                    return False
            elif error_type == "bracket":
                if not self.patcher.fix_brackets(str(filepath)):
                    return False
            elif error_type == "syntax_simple":
                if not self.patcher.comment_broken_line(str(filepath), error.lineno):
                    return False
            else:
                return False
            
            try:
                ast.parse(filepath.read_text())
                self.log(f"✅ Патчер: {filepath.name}", G)
                self.kb.log_patcher_fix(error.msg, filepath.name, error.lineno, error_type)
                return True
            except SyntaxError:
                self._rollback(filepath, bkp)
                return False
        except Exception as e:
            self._rollback(filepath, bkp)
            self.log(f"❌ Патчер: {e}", R)
            return False
    
    def heal_with_gemini(self, filepath, error):
        if not self.keys:
            return None
        content = filepath.read_text()
        prompt = f"Fix ONLY syntax error at line {error.lineno}: {error.msg}\n\n=== FILE ===\n{content}\n=== END ===\nReturn fixed file in ```python ... ```"
        
        for _ in range(3):
            key = self.keys.next()
            if not key:
                break
            try:
                resp = httpx.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    params={"key": key}, timeout=30)
                if resp.status_code == 429:
                    self.keys.block(key, 60)
                    continue
                if resp.status_code != 200:
                    continue
                raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                if "```" in raw:
                    for part in raw.split("```")[1::2]:
                        part = part.replace("python", "", 1).strip()
                        if part and part != content and not _DANGEROUS_PATTERNS.search(part):
                            return part
            except Exception as e:
                self.log(f"Gemini: {e}", R)
        return None
    
    def heal_all(self, errors):
        fixed = 0
        for e in errors:
            f = e["file"]
            key = str(f)
            self.failed_files[key] = self.failed_files.get(key, 0) + 1
            if self.failed_files[key] > 3:
                self.log(f"⛔ {f.name} — пропуск", R)
                continue
            
            if self.heal_with_patcher(f, e["error"], e["type"]):
                fixed += 1
                continue
            
            self.log(f"🤖 Gemini: {f.name}:{e['error'].lineno}...", Y)
            bkp = self._backup(f)
            fixed_content = self.heal_with_gemini(f, e["error"])
            if fixed_content:
                f.write_text(fixed_content)
                try:
                    ast.parse(fixed_content)
                    self.log(f"✅ Gemini: {f.name}", G)
                    self.kb.log_gemini_fix(e["error"].msg, f.name, e["error"].lineno, fixed_content[:300])
                    fixed += 1
                except SyntaxError:
                    self._rollback(f, bkp)
                    self.log(f"❌ Gemini: невалидный ответ", R)
        return fixed
    
    def run_once(self):
        self.attempt += 1
        self.log(f"🔄 ЦИКЛ #{self.attempt}", C)
        errors = self.scan_all()
        if not errors:
            self.log("✅ Ошибок нет", G)
            return True
        self.log(f"🐛 Найдено: {len(errors)}", Y)
        fixed = self.heal_all(errors)
        self.log(f"💊 Вылечено: {fixed}/{len(errors)}", G if fixed == len(errors) else Y)
        return fixed == len(errors)
    
    def watch(self, interval=60):
        self.log(f"👁 АВТОПИЛОТ v12 | интервал {interval}с", C)
        while True:
            try:
                if self.scan_all():
                    self.run_once()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.log("⏹ ОСТАНОВЛЕН", Y)
                break
            except Exception as e:
                self.log(f"💥 {e}", R)
                time.sleep(10)
