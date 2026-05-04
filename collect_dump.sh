#!/bin/bash
OUTPUT=~/PROJECT_DUMP_zabota.md
echo "# 📊 Дамп проекта zabota_plus" > $OUTPUT
echo "_Собрано: $(date)_" >> $OUTPUT
echo "_Окружение: Termux on Android_" >> $OUTPUT
echo "" >> $OUTPUT

dump_file() {
    if [ -f "$1" ]; then
        echo "## 📄 $1" >> $OUTPUT
        echo '```' >> $OUTPUT
        cat "$1" >> $OUTPUT
        echo '```' >> $OUTPUT
        echo "" >> $OUTPUT
    fi
}

echo "## 📁 Структура" >> $OUTPUT
echo '```' >> $OUTPUT
find ~/zabota_plus/ -type f | sort >> $OUTPUT
echo '```' >> $OUTPUT

# Ключевые файлы
dump_file ~/zabota_plus/RULES.md
dump_file ~/zabota_plus/run_bot.py
dump_file ~/zabota_plus/.env
dump_file ~/zabota_plus/app_config/settings.py
dump_file ~/zabota_plus/db/connection.py

echo "✅ Дамп: $OUTPUT ($(wc -l < $OUTPUT) строк)"
