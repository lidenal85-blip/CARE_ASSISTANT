#!/bin/bash
OUTPUT=~/FULL_PROJECT_DUMP_V2.md
echo "# 📊 ДАМП ПРОЕКТА ZABOTA_PLUS + LEVIATHAN CORE v2" > $OUTPUT
echo "_Собрано: $(date)_" >> $OUTPUT
echo "" >> $OUTPUT

echo "## 📁 СТРУКТУРА" >> $OUTPUT
echo '```' >> $OUTPUT
find ~/zabota_plus -type f -not -path "*__pycache__*" -not -path "*.bak" -not -name "*.db" -not -name "*.log" -not -name "*.pid" -not -name "*.md" -not -path "*data/backups*" -not -path "*data/audit*" -not -name "*.sh" | sort >> $OUTPUT
find ~/leviathan-core -type f -not -path "*__pycache__*" -not -path "*.egg-info*" | sort >> $OUTPUT
echo '```' >> $OUTPUT

dump() {
    if [ -f "$1" ]; then
        echo "" >> $OUTPUT
        echo "---" >> $OUTPUT
        echo "## 📄 $(echo $1 | sed 's|/data/data/com.termux/files/home/||')" >> $OUTPUT
        echo '```python' >> $OUTPUT
        cat "$1" >> $OUTPUT
        echo '```' >> $OUTPUT
    fi
}

# ZABOTA — handlers
for f in ~/zabota_plus/handlers/*.py; do dump "$f"; done

# Engine
dump ~/zabota_plus/engine/onboarding_engine.py
dump ~/zabota_plus/engine/menu_engine.py
dump ~/zabota_plus/engine/html_generator.py
dump ~/zabota_plus/engine/doctor_monitor.py

# Services
dump ~/zabota_plus/services/gemini.py
dump ~/zabota_plus/services/diet_planner.py
dump ~/zabota_plus/services/price_checker.py
dump ~/zabota_plus/services/companion.py

# DB
dump ~/zabota_plus/db/connection.py
dump ~/zabota_plus/db/repository.py

# Configs
dump ~/zabota_plus/config/onboarding.json
dump ~/zabota_plus/config/menus.json
dump ~/zabota_plus/config/doctor.json
dump ~/zabota_plus/config/patcher_rules.json

# Core
dump ~/zabota_plus/main.py
dump ~/zabota_plus/run_doctor.py
dump ~/zabota_plus/start_all.sh
dump ~/zabota_plus/Dockerfile
dump ~/zabota_plus/requirements.txt

# LEVIATHAN
dump ~/leviathan-core/leviathan/core/orchestrator.py
dump ~/leviathan-core/leviathan/doctor/doctor_system.py
dump ~/leviathan-core/leviathan/doctor/smart_patcher.py
dump ~/leviathan-core/leviathan/doctor/knowledge_base.py
dump ~/leviathan-core/leviathan/core/security/firewall.py
dump ~/leviathan-core/leviathan/core/security/normalizer.py
dump ~/leviathan-core/leviathan/memory/storage.py

echo "✅ Дамп: $OUTPUT ($(wc -l < $OUTPUT) строк)"
