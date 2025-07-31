#!/usr/bin/env python3
"""
Скрипт для ожидания готовности базы данных при запуске контейнера
"""

import asyncio
import os
import sys
import time

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import DATABASE_URL


async def wait_for_database():
    """Ожидание готовности базы данных"""
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        try:
            # Создаем движок для проверки соединения
            engine = create_async_engine(DATABASE_URL)

            async with engine.begin() as conn:
                # Выполняем простой запрос для проверки соединения
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()

            await engine.dispose()
            print("✅ База данных готова!")
            return True

        except Exception as e:
            attempt += 1
            print(f"⏳ Попытка {attempt}/{max_attempts}: База данных недоступна ({e})")

            if attempt < max_attempts:
                time.sleep(2)
            else:
                print("❌ Не удалось подключиться к базе данных")
                return False

    return False


async def main():
    """Основная функция"""
    print("🔄 Ожидание готовности базы данных...")

    if await wait_for_database():
        print("🚀 Запуск бота...")
        # Импортируем и запускаем бота
        from app.bot import main as run_bot

        await run_bot()
    else:
        print("❌ Ошибка: база данных недоступна")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
