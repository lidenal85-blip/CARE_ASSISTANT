"""SmartPatcher — AST-based Python code fixes"""
import ast, re
from pathlib import Path

class SmartPatcher:
    def __init__(self, root_path="."):
        self.root = Path(root_path)
        self.rules = {"rules": [], "known_fixes": {}}
    
    def find_function(self, file_path, func_name):
        path = self.root / file_path
        if not path.exists():
            return None
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                lines = source.split("\n")
                lineno = node.lineno
                line = lines[lineno-1] if lineno <= len(lines) else ""
                return {"line": lineno, "indent": line[:len(line)-len(line.lstrip())]}
        return None
    
    def fix_indent(self, file_path, lineno):
        path = self.root / file_path
        if not path.exists():
            return False
        lines = path.read_text().splitlines(keepends=True)
        idx = lineno - 1
        if idx <= 0 or idx >= len(lines):
            return False
        prev_indent = ""
        for i in range(idx-1, -1, -1):
            stripped = lines[i].lstrip()
            if stripped:
                prev_indent = lines[i][:len(lines[i])-len(stripped)]
                break
        current = lines[idx].lstrip()
        if not current.strip():
            return False
        lines[idx] = prev_indent + current
        path.write_text("".join(lines))
        return True
    
    def fix_brackets(self, file_path):
        path = self.root / file_path
        if not path.exists():
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
        suffix = "".join(pairs[o] * c for o, c in balance.items() if c > 0)
        if not suffix:
            return False
        path.write_text(content + "\n" + suffix)
        return True
    
    def comment_broken_line(self, file_path, lineno):
        path = self.root / file_path
        if not path.exists():
            return False
        lines = path.read_text().splitlines(keepends=True)
        idx = lineno - 1
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx]
        stripped = line.lstrip()
        if stripped.startswith("#"):
            return False
        indent = line[:len(line)-len(stripped)]
        lines[idx] = f"{indent}# [DOCTOR] {stripped}"
        path.write_text("".join(lines))
        return True
    
    def heal(self, filepath, error, error_type):
        content = filepath.read_text()
        lines = content.split("\n")
        lineno = error.lineno - 1
        
        if error_type in ("bracket", "syntax_simple", "complex"):
            if self.fix_brackets(str(filepath)):
                return True
            last = lines[-1].strip() if lines else ""
            if last and last[-1] in ('{', '(', '['):
                lines[-1] = last + {'{': '}', '(': ')', '[': ']'}[last[-1]]
                filepath.write_text("\n".join(lines))
                try:
                    ast.parse(filepath.read_text())
                    return True
                except SyntaxError:
                    pass
        
        if error_type == "indent":
            return self.fix_indent(str(filepath), error.lineno)
        
        if error_type == "syntax_simple":
            return self.comment_broken_line(str(filepath), error.lineno)
        
        return False
    
    def fix_missing_import(self, filepath, error_msg):
        match = re.search(r"name '(.*?)' is not defined", error_msg)
        if not match:
            return False
        name = match.group(1)
        known = self.rules.get("known_fixes", {}).get("imports", {})
        if name not in known:
            return False
        content = filepath.read_text()
        if known[name] in content:
            return False
        lines = content.split("\n")
        last_import = max((i for i, l in enumerate(lines) if l.startswith("from ") or l.startswith("import ")), default=0)
        lines.insert(last_import+1, known[name])
        filepath.write_text("\n".join(lines))
        return True
