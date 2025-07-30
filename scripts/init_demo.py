#!/usr/bin/env python3
"""
Скрипт для инициализации демо-пользователя в базе данных
"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL
from app.db.base import Base
from app.db.user import User


async def init_demo_user():
    """Создание демо-пользователя"""
    # Создаем движок
    engine = create_async_engine(DATABASE_URL)

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем сессию
    async_session = sessionmaker(
        engine, class_=asyncio.AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Проверяем, существует ли уже демо-пользователь
        result = await session.execute(
            "SELECT id FROM users WHERE login = 'demo01'"
        )
        existing_user = result.fetchone()

        if existing_user:
            print("✅ Демо-пользователь уже существует")
            # Сбрасываем состояние для повторного использования
            await session.execute(
                "UPDATE users SET used = FALSE, telegram_id = NULL WHERE login = 'demo01'"
            )
            await session.commit()
            print("🔄 Демо-пользователь сброшен для повторного использования")
        else:
            # Создаем демо-пользователя
            demo_user = User(
                login='demo01',
                password='demo',
                first_name='Демо',
                last_name='Пользователь',
                role='super',
                is_active=True,
                used=False,
                tg_id=None
            )
            session.add(demo_user)
            await session.commit()
            print("✅ Демо-пользователь создан")
            print("📋 Логин: demo01")
            print("🔑 Пароль: demo")

    await engine.dispose()


async def main():
    """Основная функция"""
    print("🔄 Инициализация демо-пользователя...")

    try:
        await init_demo_user()
        print("✅ Инициализация завершена успешно!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
