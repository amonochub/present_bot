from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import AsyncGenerator

from app.config import settings

# Создание асинхронного движка
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)

# Создание фабрики сессий
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии базы данных"""
    async with AsyncSessionLocal() as session:
        yield session


async def get_session_with_rls(user_id: int, role: str) -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии с установкой параметров для RLS"""
    async with AsyncSessionLocal() as sess:
        await sess.execute(text("SET app.user_id=:uid, app.role=:r"),
                           {"uid": user_id, "r": role})
        yield sess 