#!/bin/sh
set -e

echo "🔄 Запуск миграций базы данных..."

# Ждем готовности базы данных
echo "⏳ Ожидание готовности PostgreSQL..."
until python -c "
import asyncio
import asyncpg
import os
import sys

async def check_db():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER', 'schoolbot'),
            password=os.getenv('DB_PASS', 'schoolbot'),
            database=os.getenv('DB_NAME', 'schoolbot')
        )
        await conn.close()
        return True
    except Exception as e:
        print(f'Ошибка подключения к БД: {e}')
        return False

if asyncio.run(check_db()):
    print('✅ База данных готова')
    sys.exit(0)
else:
    print('❌ База данных не готова')
    sys.exit(1)
"; do
    echo "⏳ Ожидание готовности PostgreSQL..."
    sleep 2
done

# Запускаем миграции
echo "🔄 Применение миграций..."
python manage.py migrate

# Заполняем демо-данными если база пустая
echo "🔄 Проверка демо-данных..."
python manage.py seed

echo "✅ Миграции завершены успешно"

# Запускаем основное приложение
exec "$@"
