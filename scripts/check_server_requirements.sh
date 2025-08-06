#!/bin/bash
# Проверка готовности сервера к развертыванию SchoolBot

set -e

echo "🔍 Проверка системных требований для SchoolBot..."
echo "=================================================="

# Цветовая схема для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для проверки успеха
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# Функция для предупреждений
warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Проверка ОС
echo -e "\n📋 Проверка операционной системы..."
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo -e "${GREEN}✅ ОС: $NAME $VERSION${NC}"
    
    # Проверка поддерживаемых ОС
    case "$ID" in
        ubuntu|debian|centos|rhel|fedora|alpine)
            echo -e "${GREEN}✅ Поддерживаемая ОС${NC}"
            ;;
        *)
            warn "Неизвестная ОС. Возможны проблемы совместимости"
            ;;
    esac
else
    echo -e "${RED}❌ Не удалось определить ОС${NC}"
    exit 1
fi

# 2. Проверка архитектуры
echo -e "\n🏗️ Проверка архитектуры процессора..."
ARCH=$(uname -m)
case "$ARCH" in
    x86_64|amd64)
        echo -e "${GREEN}✅ Архитектура: $ARCH (поддерживается)${NC}"
        ;;
    arm64|aarch64)
        echo -e "${GREEN}✅ Архитектура: $ARCH (поддерживается)${NC}"
        ;;
    *)
        echo -e "${RED}❌ Неподдерживаемая архитектура: $ARCH${NC}"
        exit 1
        ;;
esac

# 3. Проверка Docker
echo -e "\n🐳 Проверка Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    echo -e "${GREEN}✅ Docker установлен: $DOCKER_VERSION${NC}"
    
    # Проверка запуска Docker
    if docker info &> /dev/null; then
        echo -e "${GREEN}✅ Docker демон запущен${NC}"
    else
        echo -e "${RED}❌ Docker демон не запущен${NC}"
        echo "Попробуйте: sudo systemctl start docker"
        exit 1
    fi
    
    # Проверка прав пользователя
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✅ Права доступа к Docker в порядке${NC}"
    else
        warn "Пользователь не в группе docker. Добавьте: sudo usermod -aG docker \$USER"
    fi
else
    echo -e "${RED}❌ Docker не установлен${NC}"
    echo "Установите Docker: curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
    exit 1
fi

# 4. Проверка Docker Compose
echo -e "\n🔧 Проверка Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    echo -e "${GREEN}✅ Docker Compose (standalone): $COMPOSE_VERSION${NC}"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    echo -e "${GREEN}✅ Docker Compose (plugin): $COMPOSE_VERSION${NC}"
else
    echo -e "${RED}❌ Docker Compose не установлен${NC}"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 5. Проверка портов
echo -e "\n🌐 Проверка доступности портов..."
check_port() {
    local port=$1
    local service=$2
    
    if ss -tulpn 2>/dev/null | grep ":$port " > /dev/null; then
        echo -e "${RED}❌ Порт $port занят ($service)${NC}"
        echo "Процесс на порту $port:"
        ss -tulpn | grep ":$port " | head -1
        return 1
    else
        echo -e "${GREEN}✅ Порт $port свободен ($service)${NC}"
        return 0
    fi
}

check_port 5432 "PostgreSQL"
check_port 6379 "Redis"  
check_port 8080 "Health Check"

# 6. Проверка места на диске
echo -e "\n💾 Проверка дискового пространства..."
AVAILABLE_KB=$(df / | awk 'NR==2 {print $4}')
AVAILABLE_GB=$((AVAILABLE_KB / 1024 / 1024))

if [[ $AVAILABLE_KB -lt 5242880 ]]; then  # 5GB
    echo -e "${RED}❌ Недостаточно места на диске: ${AVAILABLE_GB}GB${NC}"
    echo "Требуется минимум 5GB свободного места"
    exit 1
else
    echo -e "${GREEN}✅ Достаточно места на диске: ${AVAILABLE_GB}GB${NC}"
fi

# 7. Проверка оперативной памяти
echo -e "\n🧠 Проверка оперативной памяти..."
if command -v free &> /dev/null; then
    TOTAL_RAM_MB=$(free -m | awk 'NR==2{print $2}')
    AVAILABLE_RAM_MB=$(free -m | awk 'NR==2{print $7}')
    
    if [[ $TOTAL_RAM_MB -lt 512 ]]; then
        echo -e "${RED}❌ Недостаточно RAM: ${TOTAL_RAM_MB}MB${NC}"
        echo "Рекомендуется минимум 1GB RAM"
        exit 1
    elif [[ $TOTAL_RAM_MB -lt 1024 ]]; then
        warn "Мало RAM: ${TOTAL_RAM_MB}MB. Рекомендуется 1GB+"
    else
        echo -e "${GREEN}✅ Достаточно RAM: ${TOTAL_RAM_MB}MB (доступно: ${AVAILABLE_RAM_MB}MB)${NC}"
    fi
else
    warn "Не удалось проверить объем RAM"
fi

# 8. Проверка сетевого подключения
echo -e "\n🌍 Проверка сетевого подключения..."
if ping -c 1 google.com &> /dev/null; then
    echo -e "${GREEN}✅ Интернет-соединение работает${NC}"
else
    echo -e "${RED}❌ Нет интернет-соединения${NC}"
    echo "Проверьте сетевые настройки"
    exit 1
fi

# 9. Проверка DNS
echo -e "\n🔍 Проверка DNS..."
if nslookup google.com &> /dev/null || dig google.com &> /dev/null; then
    echo -e "${GREEN}✅ DNS работает${NC}"
else
    warn "Проблемы с DNS. Проверьте настройки"
fi

# 10. Проверка curl/wget
echo -e "\n⬇️ Проверка инструментов загрузки..."
if command -v curl &> /dev/null; then
    echo -e "${GREEN}✅ curl установлен${NC}"
elif command -v wget &> /dev/null; then
    echo -e "${GREEN}✅ wget установлен${NC}"
else
    echo -e "${RED}❌ Нет curl или wget${NC}"
    echo "Установите curl: sudo apt update && sudo apt install curl"
    exit 1
fi

# 11. Проверка git
echo -e "\n📦 Проверка Git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    echo -e "${GREEN}✅ Git установлен: $GIT_VERSION${NC}"
else
    echo -e "${RED}❌ Git не установлен${NC}"
    echo "Установите Git: sudo apt update && sudo apt install git"
    exit 1
fi

# 12. Проверка системных лимитов
echo -e "\n⚙️ Проверка системных лимитов..."
MAX_FILES=$(ulimit -n)
if [[ $MAX_FILES -lt 1024 ]]; then
    warn "Низкий лимит открытых файлов: $MAX_FILES. Рекомендуется увеличить до 4096+"
else
    echo -e "${GREEN}✅ Лимит файлов достаточный: $MAX_FILES${NC}"
fi

# 13. Проверка временной зоны
echo -e "\n🕐 Проверка временной зоны..."
if command -v timedatectl &> /dev/null; then
    TIMEZONE=$(timedatectl show --property=Timezone --value)
    echo -e "${GREEN}✅ Временная зона: $TIMEZONE${NC}"
    
    if timedatectl status | grep -q "synchronized: yes"; then
        echo -e "${GREEN}✅ Время синхронизировано${NC}"
    else
        warn "Время не синхронизировано. Настройте NTP"
    fi
else
    warn "Не удалось проверить временную зону"
fi

# Итоговый отчет
echo -e "\n🎯 Проверка завершена!"
echo "=================================================="
echo -e "${GREEN}✅ Сервер готов к развертыванию SchoolBot${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Склонируйте репозиторий: git clone <repo-url>"
echo "2. Настройте .env файл"
echo "3. Запустите: docker compose up -d"
echo "4. Проверьте логи: docker compose logs -f"
echo ""
echo "Дополнительные рекомендации:"
echo "- Настройте firewall (ufw/iptables)"
echo "- Установите SSL сертификаты"
echo "- Настройте мониторинг"
echo "- Создайте план резервного копирования"

exit 0
