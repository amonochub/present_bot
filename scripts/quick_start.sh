#!/bin/bash
set -e

echo "🚀 Быстрый запуск Present-bot на сервере..."

# Проверяем подключение к серверу
if [ -z "$SERVER_HOST" ]; then
    export SERVER_HOST=89.169.38.246
fi

if [ -z "$SERVER_USER" ]; then
    export SERVER_USER=root
fi

echo "📡 Подключаемся к серверу $SERVER_HOST..."

# Подключаемся к серверу и выполняем быстрый запуск
ssh "$SERVER_USER@$SERVER_HOST" << 'EOF'
set -e

echo "🔄 Быстрый запуск Present-bot..."

# Переходим в директорию бота
cd /srv/bots/present-bot

# Останавливаем текущий бот
echo "🛑 Останавливаем текущий бот..."
docker-compose down || true

# Создаем простой .env файл если его нет
if [ ! -f .env ]; then
    echo "📝 Создаем .env файл..."
    cat > .env << 'ENV_EOF'
TELEGRAM_TOKEN=your_telegram_token_here
DB_NAME=schoolbot
DB_USER=schoolbot
DB_PASS=schoolbot
DB_HOST=postgres
DB_PORT=5432
REDIS_DSN=redis://redis:6379/0
ENV=prod
ADMIN_IDS=your_admin_id_here
GLITCHTIP_DSN=
KEEP_DAYS=14
ENV_EOF
    echo "⚠️  ВНИМАНИЕ: Замените TELEGRAM_TOKEN и ADMIN_IDS в .env файле!"
fi

# Создаем общую сеть если её нет
echo "🌐 Проверяем сетевые настройки..."
docker network create shared-net || true

# Запускаем бота
echo "🚀 Запускаем бота..."
docker-compose up -d

# Ждем запуска
echo "⏳ Ожидание запуска..."
sleep 30

# Проверяем статус
echo "📊 Проверяем статус..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Бот успешно запущен!"
    
    echo "📋 Последние логи:"
    docker-compose logs --tail=10 bot
    
    echo "🏥 Проверка здоровья:"
    if curl -f http://localhost:8080/health; then
        echo "✅ Health check отвечает"
    else
        echo "⚠️  Health check не отвечает"
    fi
    
else
    echo "❌ Ошибка запуска бота"
    docker-compose logs bot
    exit 1
fi

echo "✅ Быстрый запуск завершен!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте .env файл с вашим TELEGRAM_TOKEN"
echo "2. Перезапустите бота: docker-compose restart bot"
echo "3. Проверьте логи: docker-compose logs -f bot"
EOF

echo "✅ Скрипт быстрого запуска выполнен!"
echo ""
echo "🌐 Проверьте бота:"
echo "   Health check: http://$SERVER_HOST:8080/health"
echo "   Grafana: http://$SERVER_HOST:3000"
echo "   Prometheus: http://$SERVER_HOST:9090" 