#!/bin/bash
set -e

echo "🚀 Инициализация GlitchTip..."

# Ждем, пока GlitchTip запустится
echo "⏳ Ожидание запуска GlitchTip..."
sleep 30

# Применяем миграции
echo "📦 Применение миграций..."
docker-compose run --rm glitchtip ./manage.py migrate

# Создаем суперпользователя (если не существует)
echo "👤 Создание суперпользователя..."
docker-compose run --rm glitchtip ./manage.py createsuperuser --noinput || true

echo "✅ GlitchTip инициализирован!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Откройте http://localhost:9000"
echo "2. Войдите под суперпользователем"
echo "3. Создайте проект 'SchoolBot'"
echo "4. Скопируйте DSN из Settings → Client Keys"
echo "5. Добавьте GLITCHTIP_DSN в .env"
echo ""
echo "💡 DSN будет вида: http://PublicKey@glitchtip:8000/1" 