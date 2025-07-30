#!/bin/bash

# Скрипт для инициализации Sentry
echo "🚀 Инициализация Sentry..."

# Проверяем, что контейнеры запущены
echo "📋 Проверка контейнеров..."
docker-compose ps

# Запускаем инициализацию Sentry
echo "🔧 Запуск инициализации Sentry..."
docker-compose run --rm sentry upgrade

echo "✅ Инициализация завершена!"
echo ""
echo "🌐 Sentry доступен по адресу: http://localhost:9000"
echo "📝 Создайте проект 'SchoolBot' (Platform: Python)"
echo "🔑 Скопируйте DSN и добавьте в .env файл:"
echo "   SENTRY_DSN=http://<public_key>@sentry:9000/1"
echo ""
echo "🧪 Для тестирования отправьте команду /crash боту" 