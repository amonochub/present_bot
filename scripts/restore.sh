#!/bin/bash
set -euo pipefail

# Скрипт для восстановления из бэкапа
# Использование: ./scripts/restore.sh [backup_file]

BACKUP_FILE=${1:-}
BACKUP_DIR="./backups"

echo "🔄 Восстановление из бэкапа"

# Функция для выбора файла бэкапа
select_backup() {
    if [[ -z "$BACKUP_FILE" ]]; then
        echo "📁 Доступные бэкапы:"
        ls -la "$BACKUP_DIR"/*.sql 2>/dev/null || {
            echo "❌ Бэкапы не найдены в $BACKUP_DIR"
            exit 1
        }
        
        echo ""
        read -p "Введите имя файла бэкапа: " BACKUP_FILE
    fi
    
    if [[ ! -f "$BACKUP_FILE" ]]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    fi
    
    if [[ ! -f "$BACKUP_FILE" ]]; then
        echo "❌ Файл бэкапа не найден: $BACKUP_FILE"
        exit 1
    fi
    
    echo "✅ Выбран бэкап: $BACKUP_FILE"
    echo "Размер: $(du -h "$BACKUP_FILE" | cut -f1)"
}

# Функция для создания бэкапа текущего состояния
backup_current() {
    echo "📦 Создание бэкапа текущего состояния..."
    ./scripts/backup.sh
}

# Функция для проверки совместимости бэкапа
check_backup_compatibility() {
    echo "🔍 Проверка совместимости бэкапа..."
    
    # Проверяем, что это SQL файл
    if [[ ! "$BACKUP_FILE" =~ \.sql$ ]]; then
        echo "❌ Файл не является SQL бэкапом"
        exit 1
    fi
    
    # Проверяем размер файла
    file_size=$(stat -c%s "$BACKUP_FILE")
    if [[ $file_size -lt 1000 ]]; then
        echo "⚠️ Внимание: Файл бэкапа очень маленький ($file_size байт)"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Проверяем содержимое файла
    if ! head -n 5 "$BACKUP_FILE" | grep -q "PostgreSQL"; then
        echo "⚠️ Внимание: Файл не похож на PostgreSQL dump"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Функция для остановки сервисов
stop_services() {
    echo "🛑 Остановка сервисов..."
    docker-compose stop bot
}

# Функция для восстановления базы данных
restore_database() {
    echo "🗄️ Восстановление базы данных..."
    
    # Проверяем подключение к базе
    if ! docker-compose exec -T postgres pg_isready -U schoolbot > /dev/null 2>&1; then
        echo "❌ База данных недоступна"
        exit 1
    fi
    
    # Очищаем базу данных
    echo "🧹 Очистка базы данных..."
    docker-compose exec -T postgres psql -U schoolbot -d schoolbot -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    
    # Восстанавливаем из бэкапа
    echo "📥 Восстановление из файла: $BACKUP_FILE"
    docker-compose exec -T postgres psql -U schoolbot -d schoolbot < "$BACKUP_FILE"
    
    if [[ $? -eq 0 ]]; then
        echo "✅ База данных восстановлена успешно"
    else
        echo "❌ Ошибка при восстановлении базы данных"
        exit 1
    fi
}

# Функция для применения миграций
apply_migrations() {
    echo "🗄️ Применение миграций..."
    
    if docker-compose exec -T bot python manage.py migrate; then
        echo "✅ Миграции применены"
    else
        echo "❌ Ошибка при применении миграций"
        exit 1
    fi
}

# Функция для запуска сервисов
start_services() {
    echo "🚀 Запуск сервисов..."
    
    docker-compose start bot
    
    # Ждем запуска
    echo "⏳ Ожидание запуска бота..."
    sleep 15
    
    # Проверяем здоровье
    if curl -f http://localhost:8080/healthz > /dev/null 2>&1; then
        echo "✅ Бот запущен и работает"
    else
        echo "❌ Бот не отвечает"
        exit 1
    fi
}

# Функция для проверки данных
verify_data() {
    echo "✅ Проверка восстановленных данных..."
    
    # Проверяем количество пользователей
    user_count=$(docker-compose exec -T postgres psql -U schoolbot -d schoolbot -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
    echo "👥 Пользователей: $user_count"
    
    # Проверяем количество заявок
    ticket_count=$(docker-compose exec -T postgres psql -U schoolbot -d schoolbot -t -c "SELECT COUNT(*) FROM tickets;" | tr -d ' ')
    echo "📋 Заявок: $ticket_count"
    
    # Проверяем количество заметок
    note_count=$(docker-compose exec -T postgres psql -U schoolbot -d schoolbot -t -c "SELECT COUNT(*) FROM notes;" | tr -d ' ')
    echo "📝 Заметок: $note_count"
    
    if [[ $user_count -eq 0 ]]; then
        echo "⚠️ Внимание: База данных пуста"
    fi
}

# Функция для очистки кэша
clear_cache() {
    echo "🧹 Очистка кэша..."
    
    # Очищаем Redis
    docker-compose exec -T redis redis-cli FLUSHALL > /dev/null 2>&1 || true
    
    # Очищаем кэш GlitchTip
    docker-compose exec -T glitchtip find /var/lib/glitchtip -name "*.cache" -delete 2>/dev/null || true
    
    echo "✅ Кэш очищен"
}

# Основной процесс восстановления
main() {
    echo "📋 План восстановления:"
    echo "1. Выбор файла бэкапа"
    echo "2. Создание бэкапа текущего состояния"
    echo "3. Проверка совместимости"
    echo "4. Остановка сервисов"
    echo "5. Восстановление базы данных"
    echo "6. Применение миграций"
    echo "7. Запуск сервисов"
    echo "8. Проверка данных"
    echo "9. Очистка кэша"
    echo ""
    
    select_backup
    backup_current
    check_backup_compatibility
    stop_services
    restore_database
    apply_migrations
    start_services
    verify_data
    clear_cache
    
    echo "🎉 Восстановление завершено успешно!"
    echo ""
    echo "📊 Проверьте работу бота:"
    echo "- Health check: http://localhost:8080/healthz"
    echo "- Grafana: http://localhost:3000"
    echo "- Prometheus: http://localhost:9090"
}

# Запуск основного процесса
main "$@" 