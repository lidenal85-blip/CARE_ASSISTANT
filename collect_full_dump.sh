#!/bin/bash
OUTPUT=~/zabota_plus/FULL_DUMP.md
echo "# 📊 ПОЛНЫЙ ДАМП ПРОЕКТА ZABOTA_PLUS" > $OUTPUT
echo "_Собрано: $(date)_" >> $OUTPUT
echo "_Окружение: Termux on Android | Python 3.13 | aiogram 3.x_" >> $OUTPUT
echo "" >> $OUTPUT

echo "## 📁 СТРУКТУРА ПРОЕКТА" >> $OUTPUT
echo '```' >> $OUTPUT
find ~/zabota_plus/ -type f -not -path '*__pycache__*' -not -path '*.bak' -not -path '*backups*' -not -name '*.db' -not -name '*.log' -not -name '*.pid' | sort >> $OUTPUT
echo '```' >> $OUTPUT

echo "" >> $OUTPUT
echo "## 📁 СТРУКТУРА LEVIATHAN-CORE" >> $OUTPUT
echo '```' >> $OUTPUT
find ~/leviathan-core/ -type f -not -path '*__pycache__*' -not -path '*.egg-info*' | sort >> $OUTPUT
echo '```' >> $OUTPUT

dump_file() {
    if [ -f "$1" ]; then
        echo "" >> $OUTPUT
        echo "---" >> $OUTPUT
        echo "## 📄 $1" >> $OUTPUT
        echo '```python' >> $OUTPUT
        cat "$1" >> $OUTPUT
        echo '```' >> $OUTPUT
    fi
}

# Все файлы заботы
for f in $(find ~/zabota_plus/ -type f -name "*.py" -not -path '*__pycache__*' -not -path '*backups*' -not -path '*sandbox*' | sort); do
    dump_file "$f"
done

# Конфиги
dump_file ~/zabota_plus/.env.example
dump_file ~/zabota_plus/requirements.txt
dump_file ~/zabota_plus/pyproject.toml 2>/dev/null

# leviathan-core
for f in $(find ~/leviathan-core/ -type f -name "*.py" -not -path '*__pycache__*' -not -path '*.egg-info*' | sort); do
    dump_file "$f"
done
dump_file ~/leviathan-core/pyproject.toml

echo "" >> $OUTPUT
echo "## 📊 СТАТИСТИКА" >> $OUTPUT
echo "- Python файлов: $(find ~/zabota_plus/ -name '*.py' -not -path '*__pycache__*' | wc -l)" >> $OUTPUT
echo "- Строк кода: $(find ~/zabota_plus/ -name '*.py' -not -path '*__pycache__*' -exec cat {} + | wc -l)" >> $OUTPUT
echo "- Хендлеров: $(ls ~/zabota_plus/handlers/*.py 2>/dev/null | wc -l)" >> $OUTPUT
echo "- Сервисов: $(ls ~/zabota_plus/services/*.py 2>/dev/null | wc -l)" >> $OUTPUT

echo "✅ Дамп: $OUTPUT ($(wc -l < $OUTPUT) строк)"
