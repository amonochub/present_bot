#!/bin/bash
# Валидация переменных окружения для SchoolBot

set -e

echo "🔍 Проверка переменных окружения SchoolBot..."
echo "=============================================="

# Цветовая схема
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Счетчики ошибок и предупреждений
ERRORS=0
WARNINGS=0

# Функции для вывода
error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Проверка существования .env файла
if [[ ! -f .env ]]; then
    error "Файл .env не найден в текущей директории"
    echo ""
    info "Создайте .env файл на основе env.example:"
    info "cp env.example .env"
    info "nano .env"
    exit 1
fi

success "Файл .env найден"

# Загрузка переменных окружения
echo -e "\n📋 Загрузка переменных окружения..."
set -a  # Автоэкспорт всех переменных
source .env
set +a

# Массив обязательных переменных
declare -A REQUIRED_VARS=(
    ["TELEGRAM_TOKEN"]="Токен Telegram бота (получите у @BotFather)"
    ["DB_NAME"]="Имя базы данных PostgreSQL"
    ["DB_USER"]="Пользователь базы данных"
    ["DB_PASS"]="Пароль базы данных"
    ["ADMIN_IDS"]="ID администраторов (получите у @userinfobot)"
)

# Массив опциональных переменных с значениями по умолчанию
declare -A OPTIONAL_VARS=(
    ["DB_HOST"]="postgres"
    ["DB_PORT"]="5432"
    ["REDIS_DSN"]="redis://redis:6379/0"
    ["ENV"]="prod"
    ["KEEP_DAYS"]="14"
    ["GLITCHTIP_DSN"]=""
)

echo -e "\n🔍 Проверка обязательных переменных..."

# Проверка обязательных переменных
for var in "${!REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        error "$var не задана (${REQUIRED_VARS[$var]})"
    else
        success "$var: задана"
    fi
done

echo -e "\n🔍 Проверка опциональных переменных..."

# Проверка опциональных переменных
for var in "${!OPTIONAL_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        warn "$var не задана, используется значение по умолчанию: ${OPTIONAL_VARS[$var]}"
    else
        success "$var: ${!var}"
    fi
done

echo -e "\n🔐 Проверка безопасности переменных..."

# Проверка Telegram токена
if [[ -n "$TELEGRAM_TOKEN" ]]; then
    if [[ "$TELEGRAM_TOKEN" == "your_telegram_token_here" ]]; then
        error "TELEGRAM_TOKEN содержит значение-заглушку"
    elif [[ ${#TELEGRAM_TOKEN} -lt 40 ]]; then
        error "TELEGRAM_TOKEN слишком короткий (${#TELEGRAM_TOKEN} символов, ожидается 45+)"
    elif [[ ! "$TELEGRAM_TOKEN" =~ ^[0-9]{8,12}:[a-zA-Z0-9_-]{35}$ ]]; then
        warn "TELEGRAM_TOKEN не соответствует ожидаемому формату"
    else
        success "TELEGRAM_TOKEN имеет корректный формат"
    fi
fi

# Проверка пароля базы данных
if [[ -n "$DB_PASS" ]]; then
    if [[ ${#DB_PASS} -lt 8 ]]; then
        warn "DB_PASS слишком простой (${#DB_PASS} символов, рекомендуется 12+)"
    elif [[ "$DB_PASS" =~ ^[a-z]+$ ]] || [[ "$DB_PASS" =~ ^[0-9]+$ ]]; then
        warn "DB_PASS содержит только цифры или только буквы"
    else
        success "DB_PASS достаточно сложный"
    fi
fi

# Проверка Admin IDs
if [[ -n "$ADMIN_IDS" ]]; then
    if [[ "$ADMIN_IDS" == "your_admin_id_here" ]]; then
        error "ADMIN_IDS содержит значение-заглушку"
    elif [[ ! "$ADMIN_IDS" =~ ^[0-9,\s]+$ ]]; then
        error "ADMIN_IDS содержит некорректные символы (только цифры и запятые)"
    else
        # Подсчет admin ID
        IFS=',' read -ra IDS <<< "$ADMIN_IDS"
        valid_ids=0
        for id in "${IDS[@]}"; do
            id=$(echo "$id" | tr -d ' ')  # Убираем пробелы
            if [[ "$id" =~ ^[0-9]{6,12}$ ]]; then
                ((valid_ids++))
            fi
        done
        
        if [[ $valid_ids -eq 0 ]]; then
            error "ADMIN_IDS не содержит корректных Telegram ID"
        else
            success "ADMIN_IDS содержит $valid_ids корректных ID"
        fi
    fi
fi

echo -e "\n🌐 Проверка сетевых настроек..."

# Проверка Redis DSN
if [[ -n "$REDIS_DSN" ]]; then
    if [[ "$REDIS_DSN" =~ ^redis://.*:[0-9]+/[0-9]+$ ]]; then
        success "REDIS_DSN имеет корректный формат"
    else
        warn "REDIS_DSN может иметь некорректный формат"
    fi
fi

# Проверка DB_PORT
if [[ -n "$DB_PORT" ]]; then
    if [[ "$DB_PORT" =~ ^[0-9]+$ ]] && [[ $DB_PORT -ge 1 ]] && [[ $DB_PORT -le 65535 ]]; then
        success "DB_PORT корректный ($DB_PORT)"
    else
        error "DB_PORT некорректный ($DB_PORT), должен быть 1-65535"
    fi
fi

echo -e "\n📊 Проверка конфигурации приложения..."

# Проверка KEEP_DAYS
if [[ -n "$KEEP_DAYS" ]]; then
    if [[ "$KEEP_DAYS" =~ ^[0-9]+$ ]] && [[ $KEEP_DAYS -ge 1 ]] && [[ $KEEP_DAYS -le 365 ]]; then
        success "KEEP_DAYS корректное значение ($KEEP_DAYS дней)"
    else
        warn "KEEP_DAYS должно быть от 1 до 365 дней"
    fi
fi

# Проверка ENV
if [[ -n "$ENV" ]]; then
    case "$ENV" in
        prod|staging|dev|test)
            success "ENV: $ENV (корректное окружение)"
            ;;
        *)
            warn "ENV: $ENV (рекомендуется: prod, staging, dev, test)"
            ;;
    esac
fi

# Проверка GlitchTip DSN (если задан)
if [[ -n "$GLITCHTIP_DSN" ]] && [[ "$GLITCHTIP_DSN" != "" ]]; then
    if [[ "$GLITCHTIP_DSN" =~ ^https?://.*@.*/.* ]]; then
        success "GLITCHTIP_DSN имеет корректный формат"
    else
        warn "GLITCHTIP_DSN может иметь некорректный формат"
    fi
fi

echo -e "\n🔧 Проверка совместимости с Docker Compose..."

# Проверка соответствия переменных docker-compose.yml
if [[ -f docker-compose.yml ]]; then
    success "docker-compose.yml найден"
    
    # Проверяем, что все переменные из .env используются в docker-compose.yml
    compose_vars=$(grep -oE '\$\{[^}]+\}' docker-compose.yml | sed 's/\${\([^}]*\)}/\1/' | sed 's/:-.*//' | sort -u)
    
    info "Переменные, используемые в docker-compose.yml:"
    for var in $compose_vars; do
        if [[ -n "${!var}" ]]; then
            echo -e "  ${GREEN}✅ $var${NC}"
        else
            echo -e "  ${YELLOW}⚠️  $var (не задана, будет использоваться значение по умолчанию)${NC}"
        fi
    done
else
    warn "docker-compose.yml не найден"
fi

echo -e "\n🛡️ Рекомендации по безопасности..."

# Генерация рекомендаций
if [[ ${#DB_PASS} -lt 12 ]]; then
    info "Сгенерируйте надежный пароль БД: openssl rand -base64 32"
fi

if [[ "$ENV" == "prod" ]] && [[ -z "$GLITCHTIP_DSN" ]]; then
    info "Рассмотрите возможность настройки мониторинга (GlitchTip/Sentry)"
fi

info "Проверьте, что .env файл добавлен в .gitignore"
info "Рассмотрите использование секретов Docker Swarm или Kubernetes в production"

# Итоговый отчет
echo -e "\n📊 Отчет о валидации:"
echo "======================"

if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    echo -e "${GREEN}🎉 Отлично! Все переменные настроены корректно${NC}"
elif [[ $ERRORS -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  Конфигурация в порядке, но есть $WARNINGS предупреждений${NC}"
else
    echo -e "${RED}❌ Найдено $ERRORS критических ошибок и $WARNINGS предупреждений${NC}"
fi

echo ""
echo "Статистика:"
echo "- Критические ошибки: $ERRORS"
echo "- Предупреждения: $WARNINGS"
echo "- Обязательные переменные: ${#REQUIRED_VARS[@]}"
echo "- Опциональные переменные: ${#OPTIONAL_VARS[@]}"

if [[ $ERRORS -gt 0 ]]; then
    echo ""
    echo -e "${RED}Исправьте критические ошибки перед развертыванием!${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}✅ Конфигурация готова к развертыванию${NC}"
    exit 0
fi
