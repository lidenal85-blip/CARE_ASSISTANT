"""Knowledge Base for Doctor System — хранит ошибки и правила"""
import json
from pathlib import Path
from datetime import datetime

class KnowledgeBase:
    def __init__(self, path: str = None):
        self.path = Path(path or "data/doctor_knowledge.json")
        self.data = self._load()
    
    def _load(self):
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {"errors": {}, "rules": [], "stats": {"total": 0, "auto_fixed": 0, "gemini_fixed": 0}}
    
    def save(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2))
    
    def log_case(self, error_msg: str, file_name: str, line: int, fix: str):
        self.data["stats"]["total"] += 1
        self.save()
    
    def stats(self):
        return self.data["stats"]

    def log_patcher_fix(self, error_msg="", file_name="", lineno=0, strategy=""):
        self.data["stats"]["patcher_fixed"] = self.data["stats"].get("patcher_fixed", 0) + 1
        self.data["stats"]["total"] = self.data["stats"].get("total", 0) + 1
        self.save()
    
    def log_gemini_fix(self, error_msg="", file_name="", lineno=0, fix_sample=""):
        self.data["stats"]["gemini_fixed"] = self.data["stats"].get("gemini_fixed", 0) + 1
        self.data["stats"]["total"] = self.data["stats"].get("total", 0) + 1
        self.save()
