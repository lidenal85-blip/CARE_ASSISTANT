"""Prompt Firewall — защита от инъекций (Manifest 4.5.0 §2.2)"""
import re

class PromptFirewall:
    LAYER1_RULES = [
        (r"ignore\s+previous\s+instructions", "prompt injection: ignore previous"),
        (r"system\s*:\s*", "prompt injection: system override"),
        (r"you\s+are\s+now\s+", "prompt injection: role override"),
        (r"forget\s+all\s+previous", "prompt injection: memory wipe"),
        (r"режим\s+администратора", "prompt injection: admin mode"),
        (r"dan\s+mode|jailbreak|developer\s+mode", "jailbreak attempt"),
    ]
    
    def check(self, text: str) -> bool:
        """Возвращает True если безопасно"""
        for pattern, _ in self.LAYER1_RULES:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        return True
