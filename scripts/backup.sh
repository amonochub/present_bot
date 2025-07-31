#!/bin/bash
set -euo pipefail

# Скрипт для создания бэкапа базы данных
# Использование: ./scripts/backup.sh [options]

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
COMPRESS=${COMPRESS:-true}
KEEP_DAYS=${KEEP_DAYS:-14}
NOTIFY_TELEGRAM=${NOTIFY_TELEGRAM:-false}

# Функция для отправки уведомлений в Telegram
notify_telegram() {
    local message="$1"
    if [[ "$NOTIFY_TELEGRAM" == "true" && -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${TELEGRAM_CHAT_ID:-}" ]]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\":\"${TELEGRAM_CHAT_ID}\",\"text\":\"$message\",\"parse_mode\":\"HTML\"}" || true
    fi
}

# Функция для создания директории бэкапов
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "📁 Создание директории для бэкапов: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

# Функция для проверки подключения к базе данных
check_database_connection() {
    echo "🔍 Проверка подключения к базе данных..."

    if ! docker-compose exec -T postgres pg_isready -U schoolbot > /dev/null 2>&1; then
        echo "❌ База данных недоступна"
        notify_telegram "❌ <b>Ошибка бэкапа</b>\nБаза данных недоступна"
        exit 1
    fi

    echo "✅ Подключение к базе данных установлено"
}

# Функция для создания бэкапа
create_backup() {
    local backup_name="schoolbot_${TIMESTAMP}"
    local backup_file="${BACKUP_DIR}/${backup_name}.sql"
    local compressed_file="${backup_file}.gz"

    echo "📦 Создание бэкапа: $backup_name"
    notify_telegram "🔄 <b>Создание бэкапа</b>\nНачинаем создание бэкапа..."

    # Создаем дамп базы данных
    echo "🗄️ Экспорт базы данных..."
    if docker-compose exec -T postgres pg_dump -U schoolbot -d schoolbot --verbose --no-password > "$backup_file"; then
        echo "✅ Бэкап создан успешно: $backup_file"

        # Сжимаем файл если включено
        if [[ "$COMPRESS" == "true" ]]; then
            echo "🗜️ Сжатие бэкапа..."
            gzip "$backup_file"
            backup_file="$compressed_file"
            echo "✅ Бэкап сжат: $backup_file"
        fi

        # Показываем информацию о файле
        local file_size=$(du -h "$backup_file" | cut -f1)
        local file_size_bytes=$(stat -c%s "$backup_file")
        echo "📊 Размер файла: $file_size ($file_size_bytes байт)"

        # Проверяем целостность
        if [[ "$COMPRESS" == "true" ]]; then
            echo "🔍 Проверка целостности сжатого файла..."
            if gzip -t "$backup_file"; then
                echo "✅ Целостность файла проверена"
            else
                echo "❌ Ошибка целостности файла"
                notify_telegram "❌ <b>Ошибка бэкапа</b>\nФайл поврежден"
                exit 1
            fi
        fi

        notify_telegram "✅ <b>Бэкап создан</b>\nФайл: $backup_name\nРазмер: $file_size"

    else
        echo "❌ Ошибка при создании бэкапа"
        notify_telegram "❌ <b>Ошибка бэкапа</b>\nНе удалось создать бэкап"
        exit 1
    fi
}

# Функция для очистки старых бэкапов
cleanup_old_backups() {
    echo "🧹 Очистка старых бэкапов (старше $KEEP_DAYS дней)..."

    local deleted_count=0
    local total_size_before=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")

    # Удаляем старые файлы
    if [[ "$COMPRESS" == "true" ]]; then
        deleted_count=$(find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +$KEEP_DAYS -delete -print | wc -l)
    else
        deleted_count=$(find "$BACKUP_DIR" -type f -name "*.sql" -mtime +$KEEP_DAYS -delete -print | wc -l)
    fi

    if [[ $deleted_count -gt 0 ]]; then
        local total_size_after=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")
        echo "🗑️ Удалено файлов: $deleted_count"
        echo "💾 Освобождено места: $total_size_before → $total_size_after"
    else
        echo "✅ Старые бэкапы не найдены"
    fi
}

# Функция для показа статистики
show_statistics() {
    echo "📊 Статистика бэкапов:"

    local total_files=0
    local total_size=0

    if [[ "$COMPRESS" == "true" ]]; then
        total_files=$(find "$BACKUP_DIR" -type f -name "*.sql.gz" | wc -l)
        total_size=$(find "$BACKUP_DIR" -type f -name "*.sql.gz" -exec du -cb {} + | tail -1 | cut -f1)
    else
        total_files=$(find "$BACKUP_DIR" -type f -name "*.sql" | wc -l)
        total_size=$(find "$BACKUP_DIR" -type f -name "*.sql" -exec du -cb {} + | tail -1 | cut -f1)
    fi

    echo "📁 Всего файлов: $total_files"
    echo "💾 Общий размер: $(numfmt --to=iec $total_size)"

    # Показываем последние 5 бэкапов
    echo "📋 Последние бэкапы:"
    if [[ "$COMPRESS" == "true" ]]; then
        find "$BACKUP_DIR" -type f -name "*.sql.gz" -printf "%T@ %p\n" | sort -nr | head -5 | while read timestamp file; do
            local date=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S')
            local size=$(du -h "$file" | cut -f1)
            echo "  📄 $(basename "$file") ($date, $size)"
        done
    else
        find "$BACKUP_DIR" -type f -name "*.sql" -printf "%T@ %p\n" | sort -nr | head -5 | while read timestamp file; do
            local date=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S')
            local size=$(du -h "$file" | cut -f1)
            echo "  📄 $(basename "$file") ($date, $size)"
        done
    fi
}

# Функция для проверки места на диске
check_disk_space() {
    echo "💾 Проверка свободного места..."

    local available_space=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    local required_space=1048576  # 1GB в байтах

    if [[ $available_space -lt $required_space ]]; then
        echo "⚠️ Внимание: Мало места на диске"
        echo "Доступно: $(numfmt --to=iec $available_space)"
        echo "Рекомендуется: $(numfmt --to=iec $required_space)"

        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✅ Достаточно места на диске"
    fi
}

# Функция для создания метаданных бэкапа
create_backup_metadata() {
    local backup_name="schoolbot_${TIMESTAMP}"
    local metadata_file="${BACKUP_DIR}/${backup_name}.meta"

    cat > "$metadata_file" << EOF
# Метаданные бэкапа SchoolBot
backup_date: $(date '+%Y-%m-%d %H:%M:%S')
backup_timestamp: $TIMESTAMP
database: schoolbot
version: $(docker-compose exec -T bot python -c "import app; print(app.__version__)" 2>/dev/null || echo "unknown")
compressed: $COMPRESS
created_by: backup.sh
hostname: $(hostname)

# Статистика базы данных
$(docker-compose exec -T postgres psql -U schoolbot -d schoolbot -t -c "
SELECT
    'users: ' || COUNT(*) as users_count
FROM users;
" 2>/dev/null || echo "users: unknown")

$(docker-compose exec -T postgres psql -U schoolbot -d schoolbot -t -c "
SELECT
    'tickets: ' || COUNT(*) as tickets_count
FROM tickets;
" 2>/dev/null || echo "tickets: unknown")

$(docker-compose exec -T postgres psql -U schoolbot -d schoolbot -t -c "
SELECT
    'notes: ' || COUNT(*) as notes_count
FROM notes;
" 2>/dev/null || echo "notes: unknown")
EOF

    echo "📝 Метаданные созданы: $metadata_file"
}

# Основной процесс
main() {
    echo "🚀 Начинаем создание бэкапа..."
    echo "📁 Директория: $BACKUP_DIR"
    echo "🗜️ Сжатие: $COMPRESS"
    echo "🗑️ Хранение: $KEEP_DAYS дней"
    echo ""

    create_backup_dir
    check_disk_space
    check_database_connection
    create_backup
    create_backup_metadata
    cleanup_old_backups
    show_statistics

    echo ""
    echo "🎉 Бэкап завершен успешно!"
    echo ""
    echo "📋 Полезные команды:"
    echo "- Восстановление: ./scripts/restore.sh"
    echo "- Список бэкапов: ls -la $BACKUP_DIR/"
    echo "- Размер бэкапов: du -sh $BACKUP_DIR/"
}

# Обработка аргументов командной строки
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --keep-days)
            KEEP_DAYS="$2"
            shift 2
            ;;
        --notify)
            NOTIFY_TELEGRAM=true
            shift
            ;;
        --help)
            echo "Использование: $0 [options]"
            echo "Options:"
            echo "  --no-compress    Не сжимать бэкап"
            echo "  --keep-days N    Хранить бэкапы N дней (по умолчанию: $KEEP_DAYS)"
            echo "  --notify         Отправлять уведомления в Telegram"
            echo "  --help           Показать эту справку"
            exit 0
            ;;
        *)
            echo "Неизвестный аргумент: $1"
            echo "Используйте --help для справки"
            exit 1
            ;;
    esac
done

# Запуск основного процесса
main "$@"
