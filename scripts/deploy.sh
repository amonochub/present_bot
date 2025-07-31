#!/bin/bash
set -euo pipefail

# Скрипт для автоматического деплоя с zero-downtime
# Использование: ./scripts/deploy.sh [environment]

ENVIRONMENT=${1:-prod}
BACKUP_BEFORE_DEPLOY=${BACKUP_BEFORE_DEPLOY:-true}
RUN_TESTS=${RUN_TESTS:-true}
NOTIFY_TELEGRAM=${NOTIFY_TELEGRAM:-true}

echo "🚀 Начинаем деплой в окружение: $ENVIRONMENT"

# Функция для отправки уведомлений в Telegram
notify_telegram() {
    local message="$1"
    if [[ "$NOTIFY_TELEGRAM" == "true" && -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${TELEGRAM_CHAT_ID:-}" ]]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\":\"${TELEGRAM_CHAT_ID}\",\"text\":\"$message\",\"parse_mode\":\"HTML\"}" || true
    fi
}

# Функция для создания бэкапа
create_backup() {
    if [[ "$BACKUP_BEFORE_DEPLOY" == "true" ]]; then
        echo "📦 Создание бэкапа перед деплоем..."
        ./scripts/backup.sh
        notify_telegram "🔄 <b>Деплой начался</b>\nОкружение: $ENVIRONMENT\nБэкап создан"
    fi
}

# Функция для запуска тестов
run_tests() {
    if [[ "$RUN_TESTS" == "true" ]]; then
        echo "🧪 Запуск тестов..."
        if python3 -m pytest tests/ -v --tb=short; then
            echo "✅ Тесты прошли успешно"
        else
            echo "❌ Тесты не прошли, деплой отменен"
            notify_telegram "❌ <b>Деплой отменен</b>\nТесты не прошли"
            exit 1
        fi
    fi
}

# Функция для проверки здоровья сервисов
health_check() {
    echo "🏥 Проверка здоровья сервисов..."
    
    # Проверяем бота
    if curl -f http://localhost:8080/healthz > /dev/null 2>&1; then
        echo "✅ Бот работает"
    else
        echo "❌ Бот недоступен"
        return 1
    fi
    
    # Проверяем базу данных
    if docker-compose exec -T postgres pg_isready -U schoolbot > /dev/null 2>&1; then
        echo "✅ База данных работает"
    else
        echo "❌ База данных недоступна"
        return 1
    fi
    
    # Проверяем Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis работает"
    else
        echo "❌ Redis недоступен"
        return 1
    fi
}

# Функция для применения миграций
run_migrations() {
    echo "🗄️ Применение миграций..."
    if docker-compose exec -T bot python manage.py migrate; then
        echo "✅ Миграции применены"
    else
        echo "❌ Ошибка при применении миграций"
        notify_telegram "❌ <b>Ошибка деплоя</b>\nМиграции не применились"
        exit 1
    fi
}

# Функция для перезапуска сервисов
restart_services() {
    echo "🔄 Перезапуск сервисов..."
    
    # Graceful restart бота
    docker-compose restart bot
    
    # Ждем запуска
    sleep 10
    
    # Проверяем здоровье
    if health_check; then
        echo "✅ Все сервисы работают"
        notify_telegram "✅ <b>Деплой завершен</b>\nОкружение: $ENVIRONMENT\nВсе сервисы работают"
    else
        echo "❌ Проблемы с сервисами"
        notify_telegram "❌ <b>Проблемы после деплоя</b>\nПроверьте логи"
        exit 1
    fi
}

# Основной процесс деплоя
main() {
    echo "📋 План деплоя:"
    echo "1. Создание бэкапа"
    echo "2. Запуск тестов"
    echo "3. Применение миграций"
    echo "4. Перезапуск сервисов"
    echo "5. Проверка здоровья"
    echo ""
    
    # Создание бэкапа
    create_backup
    
    # Запуск тестов
    run_tests
    
    # Применение миграций
    run_migrations
    
    # Перезапуск сервисов
    restart_services
    
    echo "🎉 Деплой завершен успешно!"
}

# Запуск основного процесса
main "$@" 