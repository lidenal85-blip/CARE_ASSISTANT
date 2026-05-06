from pathlib import Path
"""
engine/smart_patcher.py — Умный патчер для Python-файлов
Основан на рекомендациях по архитектуре: AST-поиск, авто-отступы, атомарная запись.

Принципы:
  - Ищет по функции/классу/комментарию (не по хрупким номерам строк)
  - Автоматически определяет отступ (indent) маркера
  - Проверяет дубликат ПЕРЕД вставкой
  - Атомарная запись: .tmp → py_compile → replace
  - Идемпотентен: повторный запуск не дублирует код
"""

import os
import re
import py_compile
import ast  # <<< AST для структурного поиска (не строковый regex)


class SmartPatcher:
    """Универсальный патчер для Python-проекта"""
    
    def __init__(self, root_path="."):
        self.root = root_path
    
    # ── 1. Структурный поиск (AST) ─────────────────
    
    def find_function(self, file_path: str, func_name: str) -> dict | None:
        """
        Ищет функцию по ИМЕНИ через AST (не по комментарию).
        Возвращает: {"line": номер, "indent": отступ, "body_end": конец тела}
        """
        with open(file_path) as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                return {
                    "line": node.lineno,
                    "end_line": node.end_lineno,
                    "indent": self._get_indent(source, node.lineno),
                    "body_start": node.body[0].lineno,
                    "body_end": node.body[-1].end_lineno
                }
        return None
    
    def _get_indent(self, source: str, lineno: int) -> str:
        """Извлекает отступ строки"""
        line = source.split("\n")[lineno - 1]
        return line[:len(line) - len(line.lstrip())]
    
    # ── 2. Поиск по якорю (Anchor Tag) ──────────────
    
    def find_anchor(self, file_path: str, anchor: str) -> dict | None:
        """
        Ищет якорь в формате: # --- ANCHOR_NAME [v1] ---
        Находит начало и конец блока.
        """
        with open(file_path) as f:
            lines = f.readlines()
        
        start_tag = f"# --- {anchor}_START"
        end_tag = f"# --- {anchor}_END"
        
        start = end = None
        for i, line in enumerate(lines):
            if start_tag in line:
                start = i
            if end_tag in line and start is not None:
                end = i
                break
        
        if start is not None and end is not None:
            return {
                "start_line": start + 1,
                "end_line": end + 1,
                "indent": self._get_indent_from_lines(lines, start)
            }
        return None
    
    def _get_indent_from_lines(self, lines: list, idx: int) -> str:
        line = lines[idx]
        return line[:len(line) - len(line.lstrip())]
    
    # ── 3. Умная вставка с авто-отступами ──────────
    
    def patch(
        self,
        file_path: str,
        marker: str,
        new_code: str,
        search_type: str = "text",  # "text" | "function" | "anchor"
        position: str = "before",   # "before" | "after" | "replace"
    ) -> bool:
        """
        Универсальная вставка кода.
        
        search_type:
          - "text": ищет строку-маркер
          - "function": ищет функцию по имени
          - "anchor": ищет якорный блок
        
        position:
          - "before": перед маркером
          - "after": после маркера
          - "replace": заменить блок (только для anchor)
        """
        file_path = os.path.join(self.root, file_path)
        
        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            return False
        
        with open(file_path) as f:
            lines = f.readlines()
        
        full = "".join(lines)
        
        # 1. Проверка дубликата
        if new_code.strip() in full:
            print(f"⏭ Код уже есть в {file_path}")
            return True
        
        # 2. Поиск цели
        target_idx = None
        indent = ""
        
        if search_type == "function":
            func_info = self.find_function(file_path, marker)
            if func_info:
                target_idx = func_info["body_start"] - 1 if position == "before" else func_info["body_end"]
                indent = func_info["indent"] + "    "  # +4 пробела для тела функции
        
        elif search_type == "anchor":
            anchor_info = self.find_anchor(file_path, marker)
            if anchor_info:
                if position == "replace":
                    # Удаляем старый блок
                    del lines[anchor_info["start_line"] - 1:anchor_info["end_line"]]
                    target_idx = anchor_info["start_line"] - 1
                else:
                    target_idx = anchor_info["start_line"] - 1 if position == "before" else anchor_info["end_line"]
                indent = anchor_info["indent"]
        
        else:  # text search
            for i, line in enumerate(lines):
                if marker in line:
                    target_idx = i
                    indent = self._get_indent_from_lines(lines, i)
                    break
        
        if target_idx is None:
            print(f"❌ Маркер '{marker}' не найден в {file_path}")
            return False
        
        # 3. Подготовка кода с отступами
        prepared = []
        for patch_line in new_code.split("\n"):
            prepared.append(f"{indent}{patch_line}\n")
        
        # 4. Вставка
        if position == "after":
            target_idx += 1
        
        for line in reversed(prepared):
            lines.insert(target_idx, line)
        
        # 5. Атомарная запись
        return self._atomic_write(file_path, lines)
    
    def _atomic_write(self, file_path: str, lines: list) -> bool:
        """Пишет через .tmp → проверка синтаксиса → замена"""
        temp = file_path + ".tmp"
        try:
            with open(temp, "w") as f:
                f.writelines(lines)
            
            py_compile.compile(temp, doraise=True)
            os.replace(temp, file_path)
            print(f"✅ {file_path} — синтаксис OK")
            return True
        except py_compile.PyCompileError as e:
            print(f"❌ Ошибка синтаксиса: {e}")
            if os.path.exists(temp):
                os.remove(temp)
            return False


# ── Быстрые функции для частых операций ──────────────

def add_handler_after(file_path: str, func_name: str, new_code: str) -> bool:
    """Добавляет код ПОСЛЕ указанной функции"""
    p = SmartPatcher()
    return p.patch(file_path, func_name, new_code, search_type="function", position="after")

def replace_anchor_block(file_path: str, anchor: str, new_code: str) -> bool:
    """Заменяет блок между якорями"""
    p = SmartPatcher()
    return p.patch(file_path, anchor, new_code, search_type="anchor", position="replace")

def insert_before_marker(file_path: str, marker: str, new_code: str) -> bool:
    """Вставляет код перед текстовым маркером"""
    p = SmartPatcher()
    return p.patch(file_path, marker, new_code, search_type="text", position="before")

    def _resolve(self, file_path):
        p = Path(file_path) if Path(file_path).is_absolute() else self.root / file_path
        return p if p.exists() else None
    
    def fix_indent(self, file_path, lineno):
        path = self._resolve(file_path)
        if not path:
            return False
        lines = path.read_text().splitlines(keepends=True)
        idx = lineno - 1
        if idx <= 0 or idx >= len(lines):
            return False
        prev_indent = ""
        for i in range(idx - 1, -1, -1):
            stripped = lines[i].lstrip()
            if stripped:
                prev_indent = lines[i][:len(lines[i]) - len(stripped)]
                break
        current = lines[idx].lstrip()
        if not current.strip():
            return False
        new_line = prev_indent + current
        if new_line == lines[idx]:
            return False
        lines[idx] = new_line
        path.write_text("".join(lines))
        return True
    
    def fix_brackets(self, file_path):
        path = self._resolve(file_path)
        if not path:
            return False
        content = path.read_text()
        balance = {"(": 0, "[": 0, "{": 0}
        pairs = {"(": ")", "[": "]", "{": "}"}
        for ch in content:
            if ch in balance:
                balance[ch] += 1
            elif ch in (")", "]", "}"):
                opener = {")": "(", "]": "[", "}": "{"}[ch]
                balance[opener] = max(0, balance[opener] - 1)
        suffix = "".join(pairs[opener] * count for opener, count in balance.items())
        if not suffix:
            return False
        path.write_text(content + "\n" + suffix)
        return True
    
    def comment_broken_line(self, file_path, lineno):
        path = self._resolve(file_path)
        if not path:
            return False
        lines = path.read_text().splitlines(keepends=True)
        idx = lineno - 1
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx]
        stripped = line.lstrip()
        if stripped.startswith("#"):
            return False
        indent = line[:len(line) - len(stripped)]
        lines[idx] = f"{indent}# [DOCTOR] {stripped}"
        path.write_text("".join(lines))
        return True
