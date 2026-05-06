#!/bin/bash
OUTPUT=~/DOCTOR_SYSTEM_DUMP.md
echo "# 📊 ПОЛНЫЙ ДАМП DOCTOR SYSTEM + SMARTPATCHER" > $OUTPUT
echo "_Собрано: $(date)_" >> $OUTPUT
echo "" >> $OUTPUT

echo "## 📁 СТРУКТУРА" >> $OUTPUT
echo '```' >> $OUTPUT
find ~/leviathan-core/leviathan/doctor/ -type f | sort >> $OUTPUT
find ~/zabota_plus/config/ -name "*patcher*" -o -name "*doctor*" | sort >> $OUTPUT
find ~/zabota_plus/engine/ -name "*doctor*" -o -name "*smart*" | sort >> $OUTPUT
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

# Core
dump ~/leviathan-core/leviathan/doctor/doctor_system.py
dump ~/leviathan-core/leviathan/doctor/smart_patcher.py
dump ~/leviathan-core/leviathan/doctor/knowledge_base.py
dump ~/leviathan-core/leviathan/doctor/__init__.py

# Configs
dump ~/zabota_plus/config/doctor.json
dump ~/zabota_plus/config/patcher_rules.json

# Monitor
dump ~/zabota_plus/engine/doctor_monitor.py

# Runner
dump ~/zabota_plus/run_doctor.py

echo "" >> $OUTPUT
echo "## 📊 СТАТИСТИКА" >> $OUTPUT
echo "- Файлов: $(find ~/leviathan-core/leviathan/doctor/ -name '*.py' | wc -l)" >> $OUTPUT
echo "- Строк кода: $(find ~/leviathan-core/leviathan/doctor/ -name '*.py' -exec cat {} + | wc -l)" >> $OUTPUT
echo "- JSON-правил: $(python3 -c 'import json; print(len(json.load(open("config/patcher_rules.json"))["rules"]))' 2>/dev/null)" >> $OUTPUT

echo "✅ Дамп: $OUTPUT ($(wc -l < $OUTPUT) строк)"
