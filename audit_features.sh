#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  🩺 АУДИТ ФУНКЦИОНАЛА ZABOTA_PLUS v2.0
#  Проверка соответствия заложенным функциям
# ═══════════════════════════════════════════════════════════

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0; TOTAL=0

ZP=~/zabota_plus
REPORT="$ZP/data/audit_features_$(date +%Y%m%d_%H%M%S).txt"

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║     🩺 АУДИТ ФУНКЦИОНАЛА ZABOTA_PLUS v2.0           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

{
echo "═══════════════════════════════════════════════════════"
echo "  🩺 АУДИТ ФУНКЦИОНАЛА — $(date)"
echo "═══════════════════════════════════════════════════════"
echo ""
} > "$REPORT"

check() {
    local name="$1"; local result="$2"; local detail="$3"
    ((TOTAL++))
    if [ "$result" = "PASS" ]; then
        echo -e "  ${GREEN}✅ $name${NC}"
        echo "✅ $name — $detail" >> "$REPORT"
        ((PASS++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "  ${RED}🔴 $name${NC}"
        echo "🔴 $name — $detail" >> "$REPORT"
        ((FAIL++))
    else
        echo -e "  ${YELLOW}⚠️  $name${NC}"
        echo "⚠️  $name — $detail" >> "$REPORT"
        ((WARN++))
    fi
}

# ═══════════════════════════════════════════════════════════
# 1. АРХИТЕКТУРА (Data-driven Level 3)
# ═══════════════════════════════════════════════════════════
echo -e "${BOLD}[1] АРХИТЕКТУРА — Data-driven подход${NC}"
{
echo ""
echo "─── 1. АРХИТЕКТУРА ───"
echo ""
} >> "$REPORT"

[ -f "$ZP/config/onboarding.json" ] && check "config/onboarding.json" "PASS" "JSON-конфиг онбординга" || check "config/onboarding.json" "FAIL" "Файл не найден"
[ -f "$ZP/config/menus.json" ] && check "config/menus.json" "PASS" "JSON-кэш меню" || check "config/menus.json" "FAIL" "Файл не найден"
[ -f "$ZP/config/keyboards.json" ] && check "config/keyboards.json" "PASS" "JSON-конфиг клавиатур" || check "config/keyboards.json" "FAIL" "Файл не найден"
[ -f "$ZP/config/replies.json" ] && check "config/replies.json" "PASS" "JSON-конфиг ответов" || check "config/replies.json" "FAIL" "Файл не найден"

[ -f "$ZP/engine/onboarding_engine.py" ] && check "engine/onboarding_engine.py" "PASS" "Движок онбординга" || check "engine/onboarding_engine.py" "FAIL" "Файл не найден"
[ -f "$ZP/engine/menu_engine.py" ] && check "engine/menu_engine.py" "PASS" "Движок меню (JSON+Gemini)" || check "engine/menu_engine.py" "FAIL" "Файл не найден"
[ -f "$ZP/engine/smart_patcher.py" ] && check "engine/smart_patcher.py" "PASS" "AST-патчер" || check "engine/smart_patcher.py" "FAIL" "Файл не найден"

# Проверка что engine импортируется в main.py
grep -q "engine.onboarding_engine" "$ZP/main.py" && check "main.py импортирует engine" "PASS" "Движок подключён" || check "main.py импортирует engine" "FAIL" "Движок не подключён"

# ═══════════════════════════════════════════════════════════
# 2. ФУНКЦИОНАЛ БОТА
# ═══════════════════════════════════════════════════════════
echo -e "\n${BOLD}[2] ФУНКЦИОНАЛ БОТА${NC}"
{
echo ""
echo "─── 2. ФУНКЦИОНАЛ БОТА ───"
echo ""
} >> "$REPORT"

# Хендлеры
declare -A HANDLERS=(
    ["start"]="/start, /help, /reset"
    ["diet"]="🥗 Диета — персональный план"
    ["menu"]="🍽 Меню — меню на неделю"
    ["water"]="💧 Вода — трекер воды"
    ["mood"]="😊 Настроение — дневник"
    ["shopping_tracker"]="🛒 Покупки — список с ценами"
    ["notes"]="📝 Заметки"
    ["plan"]="📋 План — план на день"
    ["profile"]="👤 Профиль — данные пользователя"
    ["recipes"]="🍳 Рецепты — поиск по ингредиентам"
    ["feedback"]="📝 Отзыв — обратная связь"
    ["hobby"]="🎨 Хобби"
    ["economy"]="💰 Экономия"
    ["guests"]="🎉 Гости"
    ["share"]="📤 Поделиться списком"
    ["message"]="💬 Companion — эмпатические ответы"
)

for handler in "${!HANDLERS[@]}"; do
    if [ -f "$ZP/handlers/${handler}.py" ]; then
        check "handlers/${handler}.py" "PASS" "${HANDLERS[$handler]}"
    else
        check "handlers/${handler}.py" "WARN" "Файл не найден — функционал недоступен"
    fi
done

# ═══════════════════════════════════════════════════════════
# 3. БАЗА ДАННЫХ
# ═══════════════════════════════════════════════════════════
echo -e "\n${BOLD}[3] БАЗА ДАННЫХ${NC}"
{
echo ""
echo "─── 3. БАЗА ДАННЫХ ───"
echo ""
} >> "$REPORT"

[ -f "$ZP/db/connection.py" ] && check "db/connection.py" "PASS" "Контекстный менеджер" || check "db/connection.py" "FAIL" "Нет"
[ -f "$ZP/db/repository.py" ] && check "db/repository.py" "PASS" "CRUD с whitelist" || check "db/repository.py" "FAIL" "Нет"

# Проверка @asynccontextmanager
grep -q "asynccontextmanager" "$ZP/db/connection.py" && check "get_db() context manager" "PASS" "Контекстный менеджер" || check "get_db() context manager" "FAIL" "Нет @asynccontextmanager"

# Проверка ALLOWED_FIELDS
grep -q "ALLOWED_FIELDS" "$ZP/db/repository.py" && check "ALLOWED_FIELDS whitelist" "PASS" "Защита от SQL injection" || check "ALLOWED_FIELDS whitelist" "FAIL" "Нет whitelist"

# Таблицы
for table in "users" "goals" "chores" "shopping_list" "water_intake" "mood_entries" "notes" "meals" "hobbies" "food_preferences" "mood_triggers" "cached_menus"; do
    grep -q "CREATE TABLE IF NOT EXISTS $table" "$ZP/db/connection.py" && check "Таблица $table" "PASS" "Создаётся" || check "Таблица $table" "FAIL" "Не создаётся"
done

# Проверка cycle_tracking поля
grep -q "cycle_tracking" "$ZP/db/repository.py" && check "Поле cycle_tracking" "PASS" "Добавлено" || check "Поле cycle_tracking" "WARN" "Не добавлено"

# ═══════════════════════════════════════════════════════════
# 4. БЕЗОПАСНОСТЬ
# ═══════════════════════════════════════════════════════════
echo -e "\n${BOLD}[4] БЕЗОПАСНОСТЬ${NC}"
{
echo ""
echo "─── 4. БЕЗОПАСНОСТЬ ───"
echo ""
} >> "$REPORT"

[ -f "$ZP/leviathan-core/leviathan/core/security/firewall.py" ] && check "Prompt Firewall" "PASS" "Защита от инъекций" || check "Prompt Firewall" "FAIL" "Нет"
[ -f "$ZP/leviathan-core/leviathan/core/security/normalizer.py" ] && check "Input Normalizer" "PASS" "NFKC нормализация" || check "Input Normalizer" "FAIL" "Нет"
[ -f "$ZP/leviathan-core/leviathan/core/security/sanitizer.py" ] && check "Input Sanitizer" "PASS" "Санитайзер" || check "Input Sanitizer" "FAIL" "Нет"

grep -q "firewall.check\|_firewall.check" "$ZP/services/gemini.py" && check "Firewall в gemini.py" "PASS" "Проверка промтов" || check "Firewall в gemini.py" "FAIL" "Не проверяется"

# ═══════════════════════════════════════════════════════════
# 5. KEYPOOL
# ═══════════════════════════════════════════════════════════
echo -e "\n${BOLD}[5] KEYPOOL И API-КЛЮЧИ${NC}"
{
echo ""
echo "─── 5. KEYPOOL ───"
echo ""
} >> "$REPORT"

[ -f "$ZP/leviathan-core/leviathan/core/orchestrator.py" ] && check "KeyPool v2" "PASS" "Production-класс" || check "KeyPool v2" "FAIL" "Нет"

grep -q "Exponential Backoff\|COOLDOWN_429_BASE" "$ZP/leviathan-core/leviathan/core/orchestrator.py" && check "Exponential Backoff" "PASS" "429→60s×2^N" || check "Exponential Backoff" "WARN" "Нет"
grep -q "get_best\|fallback" "$ZP/leviathan-core/leviathan/core/orchestrator.py" && check "Gemini→Groq fallback" "PASS" "Авто-переключение" || check "Gemini→Groq fallback" "WARN" "Нет"

# Проверка количества загружаемых ключей
grep -q "GEMINI.*14\|_load_env.*GEMINI.*14\|max_n.*14" "$ZP/leviathan-core/leviathan/core/orchestrator.py" && check "14 Gemini ключей" "PASS" "Загружаются" || check "14 Gemini ключей" "WARN" "Проверь макс. кол-во"
grep -q "GROQ.*5\|_load_env.*GROQ.*5" "$ZP/leviathan-core/leviathan/core/orchestrator.py" && check "5 Groq ключей" "PASS" "Загружаются" || check "5 Groq ключей" "WARN" "Проверь макс. кол-во"

# ═══════════════════════════════════════════════════════════
# 6. ДЕПЛОЙ
# ═══════════════════════════════════════════════════════════
echo -e "\n${BOLD}[6] ДЕПЛОЙ И ИНФРАСТРУКТУРА${NC}"
{
echo ""
echo "─── 6. ДЕПЛОЙ ───"
echo ""
} >> "$REPORT"

[ -f "$ZP/Dockerfile" ] && check "Dockerfile" "PASS" "Контейнеризация" || check "Dockerfile" "FAIL" "Нет"
[ -f "$ZP/docker-compose.yml" ] && check "docker-compose.yml" "PASS" "Оркестрация" || check "docker-compose.yml" "WARN" "Нет"
[ -f "$ZP/.dockerignore" ] && check ".dockerignore" "PASS" "Исключения" || check ".dockerignore" "WARN" "Нет"
[ -f "$ZP/.gitignore" ] && check ".gitignore" "PASS" "Git исключения" || check ".gitignore" "WARN" "Нет"

grep -q "\.env" "$ZP/.gitignore" && check ".env в gitignore" "PASS" "Ключи не в репе" || check ".env в gitignore" "FAIL" "Ключи могут утечь"

# ═══════════════════════════════════════════════════════════
# 7. СИНТАКСИС ВСЕХ PY-ФАЙЛОВ
# ═══════════════════════════════════════════════════════════
echo -e "\n${BOLD}[7] СИНТАКСИЧЕСКАЯ ПРОВЕРКА${NC}"
{
echo ""
echo "─── 7. СИНТАКСИС ───"
echo ""
} >> "$REPORT"

for f in $(find "$ZP" -name "*.py" -not -path "*__pycache__*" -not -path "*backups*" -not -path "*sandbox*" -not -path "*.egg-info*"); do
    if python3 -m py_compile "$f" 2>/dev/null; then
        echo "  ✅ $(basename $(dirname "$f"))/$(basename "$f")" >> "$REPORT"
    else
        check "$(basename $(dirname "$f"))/$(basename "$f")" "FAIL" "Ошибка синтаксиса"
    fi
done

# ═══════════════════════════════════════════════════════════
# 8. JSON-ВАЛИДАЦИЯ
# ═══════════════════════════════════════════════════════════
echo -e "\n${BOLD}[8] JSON-КОНФИГИ (валидация)${NC}"
{
echo ""
echo "─── 8. JSON ───"
echo ""
} >> "$REPORT"

for f in "$ZP"/config/*.json; do
    fname=$(basename "$f")
    if python3 -m json.tool "$f" > /dev/null 2>&1; then
        check "$fname" "PASS" "Валидный JSON"
    else
        check "$fname" "FAIL" "Битый JSON"
    fi
done

# ═══════════════════════════════════════════════════════════
# ИТОГО
# ═══════════════════════════════════════════════════════════
PERCENT=$((PASS * 100 / TOTAL))
echo ""
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  РЕЗУЛЬТАТЫ АУДИТА ФУНКЦИОНАЛА${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "  Всего проверок: ${BOLD}$TOTAL${NC}"
echo -e "  ${GREEN}✅ PASS: $PASS${NC}"
echo -e "  ${RED}🔴 FAIL: $FAIL${NC}"
echo -e "  ${YELLOW}⚠️  WARN: $WARN${NC}"
echo -e "  ${CYAN}📊 Соответствие: ${PERCENT}%${NC}"
echo ""

{
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ИТОГО: PASS=$PASS FAIL=$FAIL WARN=$WARN | $PERCENT%"
echo "═══════════════════════════════════════════════════════"
} >> "$REPORT"

echo -e "Подробный отчёт: ${BOLD}$REPORT${NC}"
