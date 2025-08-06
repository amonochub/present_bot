#!/bin/bash
# Скрипт для инициализации БД в Docker-контейнере
set -e

echo "🔧 Инициализация базы данных SchoolBot..."

# Ждем готовности PostgreSQL
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  echo "⏳ Ожидание готовности PostgreSQL..."
  sleep 2
done

echo "✅ PostgreSQL готов!"

# Проверяем, существует ли база данных
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "📊 База данных $DB_NAME уже существует"
else
    echo "🗄️ Создание базы данных $DB_NAME..."
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
fi

# Выполняем SQL-скрипты
echo "🔧 Выполнение SQL-скриптов..."

# Основная схема
if [ -f "/app/sql/01_init_schema.sql" ]; then
    echo "📋 Применение схемы базы данных..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /app/sql/01_init_schema.sql
else
    echo "⚠️ Файл схемы не найден, используем Alembic..."
    alembic upgrade head
fi

# Демо-данные (только в dev/test режиме)
if [ "$ENV" = "dev" ] || [ "$ENV" = "test" ]; then
    if [ -f "/app/sql/02_demo_data.sql" ]; then
        echo "🎯 Загрузка демо-данных..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /app/sql/02_demo_data.sql
    fi
fi

echo "✅ Инициализация базы данных завершена!"
