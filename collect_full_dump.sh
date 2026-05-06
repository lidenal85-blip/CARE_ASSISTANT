#!/bin/bash
OUTPUT=~/FULL_PROJECT_DUMP.md
echo "# 📊 ПОЛНЫЙ ДАМП ПРОЕКТА ZABOTA_PLUS + LEVIATHAN" > $OUTPUT
echo "_Собрано: $(date)_" >> $OUTPUT
echo "" >> $OUTPUT

echo "## 📁 СТРУКТУРА" >> $OUTPUT
echo '```' >> $OUTPUT
find ~/zabota_plus -type f -not -path "*__pycache__*" -not -path "*.bak" -not -name "*.db" -not -name "*.log" -not -name "*.pid" | sort >> $OUTPUT
find ~/leviathan-core -type f -not -path "*__pycache__*" -not -path "*.egg-info*" | sort >> $OUTPUT
echo '```' >> $OUTPUT

dump() {
    if [ -f "$1" ]; then
        echo "" >> $OUTPUT
        echo "---" >> $OUTPUT
        echo "## 📄 $1" >> $OUTPUT
        echo '```python' >> $OUTPUT
        cat "$1" >> $OUTPUT
        echo '```' >> $OUTPUT
    fi
}

# Основные файлы
dump ~/zabota_plus/main.py
dump ~/zabota_plus/run_doctor.py
dump ~/zabota_plus/Dockerfile
dump ~/zabota_plus/docker-compose.yml
dump ~/zabota_plus/requirements.txt

# Конфиги
dump ~/zabota_plus/config/onboarding.json
dump ~/zabota_plus/config/menus.json
dump ~/zabota_plus/config/keyboards.json
dump ~/zabota_plus/config/replies.json
dump ~/zabota_plus/config/doctor.json
dump ~/zabota_plus/config/patcher_rules.json

# Движки
dump ~/zabota_plus/engine/onboarding_engine.py
dump ~/zabota_plus/engine/menu_engine.py
dump ~/zabota_plus/engine/html_generator.py
dump ~/zabota_plus/engine/doctor_monitor.py

# Хендлеры
for f in ~/zabota_plus/handlers/*.py; do dump "$f"; done

# Сервисы
dump ~/zabota_plus/services/gemini.py
dump ~/zabota_plus/services/diet_planner.py
dump ~/zabota_plus/services/price_checker.py

# БД
dump ~/zabota_plus/db/connection.py
dump ~/zabota_plus/db/repository.py

# Leviathan Core
dump ~/leviathan-core/leviathan/core/orchestrator.py
dump ~/leviathan-core/leviathan/core/__init__.py
dump ~/leviathan-core/leviathan/doctor/doctor_system.py
dump ~/leviathan-core/leviathan/doctor/smart_patcher.py
dump ~/leviathan-core/leviathan/doctor/knowledge_base.py
dump ~/leviathan-core/leviathan/core/security/firewall.py
dump ~/leviathan-core/leviathan/core/security/normalizer.py
dump ~/leviathan-core/leviathan/memory/storage.py
dump ~/leviathan-core/pyproject.toml

echo "" >> $OUTPUT
echo "## 📊 СТАТИСТИКА" >> $OUTPUT
echo "- Python файлов: $(find ~/zabota_plus ~/leviathan-core -name '*.py' -not -path '*__pycache__*' | wc -l)" >> $OUTPUT
echo "- Строк кода: $(find ~/zabota_plus ~/leviathan-core -name '*.py' -not -path '*__pycache__*' -exec cat {} + | wc -l)" >> $OUTPUT
echo "- Хендлеров: $(ls ~/zabota_plus/handlers/*.py 2>/dev/null | wc -l)" >> $OUTPUT
echo "- Сервисов: $(ls ~/zabota_plus/services/*.py 2>/dev/null | wc -l)" >> $OUTPUT
echo "- JSON-правил патчера: $(python3 -c 'import json; print(len(json.load(open("config/patcher_rules.json"))["rules"]))' 2>/dev/null)" >> $OUTPUT
echo "- Gemini ключей: $(grep -c 'GEMINI_K' ~/zabota_plus/.env)" >> $OUTPUT

echo "✅ Дамп: $OUTPUT ($(wc -l < $OUTPUT) строк)"
