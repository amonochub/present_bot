#!/bin/bash

# Скрипт для проверки и исправления проблем с зависимостями
# Использование: ./scripts/fix_dependencies.sh

set -e

echo "🔍 Проверка зависимостей..."

# Проверяем, что все необходимые зависимости присутствуют в requirements.txt
REQUIRED_DEPS=(
    "aiofiles>=23.2.1,<24.2"
    "pydantic-settings>=2.0.0"
    "aiogram>=3.0.0"
    "sqlalchemy>=2.0.0"
    "asyncpg>=0.29.0"
    "alembic==1.13.1"
    "redis>=5.0.0"
    "python-dotenv>=1.0.0"
    "pydantic>=2.7.2"
    "certifi>=2023.7.22"
    "PyYAML>=6.0"
)

echo "📋 Проверяем requirements.txt..."
for dep in "${REQUIRED_DEPS[@]}"; do
    if ! grep -q "$(echo $dep | cut -d'=' -f1)" requirements.txt; then
        echo "❌ Отсутствует: $dep"
        echo "$dep" >> requirements.txt
        echo "✅ Добавлено: $dep"
    else
        echo "✅ Найдено: $dep"
    fi
done

echo ""
echo "🔧 Пересборка Docker контейнеров..."
docker-compose build --no-cache

echo ""
echo "🚀 Запуск основных сервисов..."
docker-compose up -d bot postgres redis

echo ""
echo "✅ Проверка завершена!"
echo "📊 Статус сервисов:"
docker-compose ps

echo ""
echo "📝 Логи бота (последние 20 строк):"
docker-compose logs --tail=20 bot 