#!/bin/bash

# Скрипт для создания бэкапа базы данных
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/schoolbot_${TIMESTAMP}.sql"

# Создаем директорию для бэкапов если её нет
mkdir -p "$BACKUP_DIR"

echo "Создание бэкапа: $BACKUP_FILE"

# Создаем дамп базы данных
PGPASSWORD=schoolbot pg_dump -h localhost -U schoolbot -d schoolbot > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Бэкап создан успешно: $BACKUP_FILE"
    echo "Размер файла: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo "❌ Ошибка при создании бэкапа"
    exit 1
fi 