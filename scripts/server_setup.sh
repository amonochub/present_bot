#!/bin/bash

# Автоматизированная настройка сервера для School Bot
# Использование: ./scripts/server_setup.sh

set -e

echo "🚀 Начинаем настройку сервера..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Проверка root прав
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен от root"
   exit 1
fi

log "Обновление системы..."
apt update && apt upgrade -y

log "Установка необходимых пакетов..."
apt install -y docker.io docker-compose git curl wget ufw htop

log "Запуск и включение Docker..."
systemctl start docker
systemctl enable docker

log "Создание директории для проекта..."
mkdir -p /opt/school-bot
cd /opt/school-bot

log "Клонирование проекта..."
if [ ! -d ".git" ]; then
    # Если проект не клонирован, создаем базовую структуру
    mkdir -p app scripts migrations
    touch requirements.txt docker-compose.yml Dockerfile
    log "Создана базовая структура проекта"
else
    log "Проект уже существует"
fi

log "Создание .env файла..."
cat > .env << 'EOF'
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
EOF

log "Создание docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.9'

services:
  bot:
    build: .
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - DB_NAME=${POSTGRES_DB}
      - DB_USER=${POSTGRES_USER}
      - DB_PASS=${POSTGRES_PASSWORD}
      - DB_HOST=postgres
      - DB_PORT=5432
      - REDIS_DSN=${REDIS_URL}
      - ADMIN_IDS=${ADMIN_IDS}
      - ENV=${ENVIRONMENT}
      - KEEP_DAYS=${KEEP_DAYS}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    ports:
      - "8080:8080"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
EOF

log "Создание Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

FROM python:3.11-bookworm
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . /app
RUN chmod +x /app/scripts/*.sh
CMD ["python", "-m", "app.bot"]
EOF

log "Создание requirements.txt..."
cat > requirements.txt << 'EOF'
aiogram>=3.0.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic==1.13.1
redis>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.7.2
aiofiles>=23.2.1,<24.2
certifi>=2023.7.22
PyYAML>=6.0
EOF

log "Создание systemd сервиса..."
cat > /etc/systemd/system/schoolbot.service << 'EOF'
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
EOF

log "Настройка firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw --force enable

log "Включение автозапуска сервиса..."
systemctl daemon-reload
systemctl enable schoolbot.service

log "Создание скрипта мониторинга..."
cat > /opt/school-bot/scripts/monitor.sh << 'EOF'
#!/bin/bash
echo "=== School Bot Status ==="
docker-compose ps
echo ""
echo "=== Bot Logs (last 20 lines) ==="
docker-compose logs --tail=20 bot
echo ""
echo "=== System Resources ==="
df -h
free -h
EOF

chmod +x /opt/school-bot/scripts/monitor.sh

log "Создание скрипта обновления..."
cat > /opt/school-bot/scripts/update.sh << 'EOF'
#!/bin/bash
cd /opt/school-bot
git pull
docker-compose build --no-cache
docker-compose up -d
echo "Update completed!"
EOF

chmod +x /opt/school-bot/scripts/update.sh

log "Настройка завершена!"
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
echo ""
echo "4. Полезные команды:"
echo "   - Просмотр логов: docker-compose logs -f bot"
echo "   - Обновление: /opt/school-bot/scripts/update.sh"
echo "   - Остановка: systemctl stop schoolbot.service"
echo "   - Перезапуск: systemctl restart schoolbot.service"

log "Настройка сервера завершена успешно! 🎉" 