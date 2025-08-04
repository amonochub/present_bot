#!/bin/bash

# Быстрый деплой School Bot на сервер
# Использование: ./scripts/deploy_to_server.sh

set -e

SERVER_IP="89.169.38.246"
SERVER_USER="root"
SERVER_PASS="e*xB9L%ZfPiu"

echo "🚀 Начинаем деплой на сервер $SERVER_IP..."

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Проверка наличия sshpass
if ! command -v sshpass &> /dev/null; then
    error "sshpass не установлен. Установите его:"
    echo "  macOS: brew install sshpass"
    echo "  Ubuntu: sudo apt install sshpass"
    exit 1
fi

# Проверка подключения к серверу
log "Проверка подключения к серверу..."
if ! sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'" 2>/dev/null; then
    error "Не удается подключиться к серверу. Проверьте IP и пароль."
    exit 1
fi

log "Подключение к серверу успешно!"

# Копирование файлов на сервер
log "Копирование файлов на сервер..."

# Создаем временный архив
TEMP_ARCHIVE="/tmp/school-bot-deploy.tar.gz"
tar -czf "$TEMP_ARCHIVE" \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    .

# Копируем архив на сервер
log "Загрузка файлов на сервер..."
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no "$TEMP_ARCHIVE" "$SERVER_USER@$SERVER_IP:/tmp/"

# Удаляем временный архив
rm "$TEMP_ARCHIVE"

# Выполняем настройку на сервере
log "Выполнение настройки на сервере..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e

echo "🔧 Настройка сервера..."

# Создаем директорию для проекта
mkdir -p /opt/school-bot

# Распаковываем архив
cd /opt/school-bot
tar -xzf /tmp/school-bot-deploy.tar.gz
rm /tmp/school-bot-deploy.tar.gz

# Делаем скрипты исполняемыми
chmod +x scripts/*.sh

# Создаем .env файл если его нет
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_token_here

# Database Configuration
POSTGRES_DB=schoolbot
POSTGRES_USER=schoolbot
POSTGRES_PASSWORD=secure_password_change_me

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Admin Configuration
ADMIN_IDS=your_admin_id_here

# Environment
ENVIRONMENT=prod
KEEP_DAYS=14

# Monitoring (optional)
GLITCHTIP_DSN=
ENVEOF
    echo "✅ Создан .env файл. Отредактируйте его перед запуском!"
fi

# Устанавливаем Docker если не установлен
if ! command -v docker &> /dev/null; then
    echo "📦 Установка Docker..."
    apt update
    apt install -y docker.io docker-compose
    systemctl start docker
    systemctl enable docker
fi

# Настраиваем firewall
echo "🔥 Настройка firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw allow 9000/tcp
ufw --force enable

# Создаем systemd сервис
echo "⚙️ Создание systemd сервиса..."
cat > /etc/systemd/system/schoolbot.service << 'SERVICEEOF'
[Unit]
Description=School Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/school-bot
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Включаем автозапуск
systemctl daemon-reload
systemctl enable schoolbot.service

echo "✅ Настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте /opt/school-bot/.env файл:"
echo "   - Укажите TELEGRAM_TOKEN"
echo "   - Укажите ADMIN_IDS"
echo "   - Измените пароль базы данных"
echo ""
echo "2. Запустите сервис:"
echo "   systemctl start schoolbot.service"
echo ""
echo "3. Проверьте статус:"
echo "   /opt/school-bot/scripts/monitor.sh"
EOF

log "Деплой завершен успешно! 🎉"

echo ""
echo "📋 Следующие шаги:"
echo "1. Подключитесь к серверу:"
echo "   ssh root@89.169.38.246"
echo ""
echo "2. Отредактируйте .env файл:"
echo "   nano /opt/school-bot/.env"
echo ""
echo "3. Запустите сервис:"
echo "   systemctl start schoolbot.service"
echo ""
echo "4. Проверьте статус:"
echo "   /opt/school-bot/scripts/monitor.sh"
echo ""
echo "🔗 Полезные ссылки:"
echo "   - Health check: http://89.169.38.246:8080/health"
echo "   - Мониторинг: /opt/school-bot/scripts/monitor.sh"
echo "   - Логи: docker-compose logs -f bot" 