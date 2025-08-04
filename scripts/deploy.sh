#!/bin/bash
set -e

# Скрипт для автоматического деплоя на сервер
echo "🚀 Начинаем деплой на сервер..."

# Проверяем наличие переменных окружения
if [ -z "$SERVER_HOST" ]; then
    echo "❌ Ошибка: не установлена переменная SERVER_HOST"
    exit 1
fi

if [ -z "$SERVER_USER" ]; then
    echo "❌ Ошибка: не установлена переменная SERVER_USER"
    exit 1
fi

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 Подготовка к деплою...${NC}"

# Проверяем, что мы в git репозитории
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Ошибка: не найден git репозиторий${NC}"
    exit 1
fi

# Получаем текущую ветку
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${YELLOW}🌿 Текущая ветка: $CURRENT_BRANCH${NC}"

# Проверяем, что все изменения закоммичены
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ Ошибка: есть незакоммиченные изменения${NC}"
    echo "Пожалуйста, закоммитьте изменения перед деплоем"
    exit 1
fi

# Получаем последний коммит
LAST_COMMIT=$(git rev-parse HEAD)
echo -e "${YELLOW}📝 Последний коммит: $LAST_COMMIT${NC}"

# Создаем временную директорию для сборки
BUILD_DIR=$(mktemp -d)
echo -e "${GREEN}📁 Временная директория: $BUILD_DIR${NC}"

# Копируем файлы в временную директорию
echo -e "${GREEN}📋 Копирование файлов...${NC}"
rsync -av --exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.pytest_cache' --exclude='.mypy_cache' --exclude='.ruff_cache' \
    --exclude='node_modules' --exclude='.env' \
    ./ "$BUILD_DIR/"

# Переходим в временную директорию
cd "$BUILD_DIR"

# Создаем .env файл если его нет
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Создаем .env файл из примера...${NC}"
    cp env.example .env
fi

# Создаем .dockerignore если его нет
if [ ! -f .dockerignore ]; then
    echo -e "${YELLOW}📝 Создаем .dockerignore...${NC}"
    cat > .dockerignore << EOF
.git
.gitignore
README.md
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
node_modules/
tests/
*.log
EOF
fi

# Создаем архив для передачи
ARCHIVE_NAME="schoolbot-$(date +%Y%m%d-%H%M%S).tar.gz"
echo -e "${GREEN}📦 Создание архива: $ARCHIVE_NAME${NC}"
tar -czf "$ARCHIVE_NAME" .

# Передаем архив на сервер
echo -e "${GREEN}📤 Передача файлов на сервер...${NC}"
scp "$ARCHIVE_NAME" "$SERVER_USER@$SERVER_HOST:/tmp/"

# Подключаемся к серверу и разворачиваем
echo -e "${GREEN}🔧 Развертывание на сервере...${NC}"
ssh "$SERVER_USER@$SERVER_HOST" << EOF
set -e

echo "🔄 Начинаем развертывание на сервере..."

# Создаем директорию для бота если её нет
sudo mkdir -p /srv/bots/present-bot

# Переходим в директорию бота
cd /srv/bots/present-bot

# Останавливаем текущий бот
echo "🛑 Останавливаем текущий бот..."
docker-compose down || true

# Создаем бэкап текущей версии
echo "💾 Создаем бэкап..."
if [ -d "app" ]; then
    sudo tar -czf "backup-\$(date +%Y%m%d-%H%M%S).tar.gz" app/ scripts/ requirements.txt docker-compose.yml Dockerfile || true
fi

# Распаковываем новый архив
echo "📦 Распаковываем новый код..."
sudo tar -xzf /tmp/$ARCHIVE_NAME

# Устанавливаем правильные права
echo "🔐 Устанавливаем права доступа..."
sudo chown -R root:root .
sudo chmod +x scripts/*.sh

# Создаем общую сеть если её нет
echo "🌐 Проверяем сетевые настройки..."
docker network create shared-net || true

# Собираем и запускаем бота
echo "🔨 Собираем Docker образ..."
docker-compose build --no-cache

echo "🚀 Запускаем бота..."
docker-compose up -d

# Ждем запуска и проверяем статус
echo "⏳ Ожидание запуска..."
sleep 30

# Проверяем статус
if docker-compose ps | grep -q "Up"; then
    echo "✅ Бот успешно запущен!"
    
    # Показываем логи
    echo "📋 Последние логи:"
    docker-compose logs --tail=10 bot
    
    # Проверяем health check
    echo "🏥 Проверка здоровья:"
    curl -f http://localhost:8080/health || echo "⚠️  Health check не отвечает"
    
else
    echo "❌ Ошибка запуска бота"
    docker-compose logs bot
    exit 1
fi

# Очищаем временные файлы
rm -f /tmp/$ARCHIVE_NAME

echo "✅ Деплой завершен успешно!"
EOF

# Очищаем временную директорию
rm -rf "$BUILD_DIR"
rm -f "$ARCHIVE_NAME"

echo -e "${GREEN}✅ Деплой завершен успешно!${NC}"
echo -e "${YELLOW}🌐 Проверьте бота: http://$SERVER_HOST:8080/health${NC}"
