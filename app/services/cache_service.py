"""
Сервис кеширования для оптимизации производительности
"""

import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import redis.asyncio as redis
from aiocache import cached
from sqlalchemy import select

from app.config import settings
from app.db.note import Note
from app.db.session import AsyncSessionLocal
from app.db.task import Task
from app.db.ticket import Ticket
from app.db.user import User
from app.roles import UserRole

logger = logging.getLogger(__name__)

# Инициализация Redis клиента
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Настройки кеша
CACHE_TTL = 600  # 10 минут по умолчанию
USER_CACHE_TTL = 300  # 5 минут для пользователей
SCHEDULE_CACHE_TTL = 1800  # 30 минут для расписания
STATS_CACHE_TTL = 900  # 15 минут для статистики


class CacheService:
    """Сервис для работы с кешем"""

    @staticmethod
    async def get_user(tg_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя из кеша или БД"""
        cache_key = f"user:{tg_id}"

        # Пробуем получить из кеша
        cached_user = await redis_client.get(cache_key)
        if cached_user:
            return json.loads(cached_user)

        # Если нет в кеше, получаем из БД
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.tg_id == tg_id))
            user = result.scalar_one_or_none()

            if user:
                user_data = {
                    "id": user.id,
                    "tg_id": user.tg_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }

                # Сохраняем в кеш
                await redis_client.setex(cache_key, USER_CACHE_TTL, json.dumps(user_data))

                return user_data

        return None

    @staticmethod
    async def invalidate_user(tg_id: int) -> None:
        """Инвалидировать кеш пользователя"""
        cache_key = f"user:{tg_id}"
        await redis_client.delete(cache_key)

    @staticmethod
    @cached(ttl=SCHEDULE_CACHE_TTL)
    async def get_school_schedule(school_id: int) -> List[Dict[str, Any]]:
        """Получить расписание школы (кешируется)"""
        # Здесь будет логика получения расписания
        # Пока возвращаем заглушку
        return [
            {
                "id": 1,
                "day": "monday",
                "lessons": [
                    {"time": "09:00", "subject": "Математика", "teacher": "Иванова А.П."},
                    {"time": "10:00", "subject": "Русский язык", "teacher": "Петрова М.И."},
                ],
            }
        ]

    @staticmethod
    @cached(ttl=STATS_CACHE_TTL)
    async def get_system_stats() -> Dict[str, Any]:
        """Получить статистику системы (кешируется)"""
        async with AsyncSessionLocal() as session:
            # Подсчет пользователей по ролям
            users_by_role = {}
            for role in UserRole:
                result = await session.execute(select(User).where(User.role == role.value))
                users_by_role[role.value] = len(result.scalars().all())

            # Подсчет активных заявок
            result = await session.execute(select(Ticket).where(Ticket.status == "open"))
            open_tickets = len(result.scalars().all())

            # Подсчет активных задач
            result = await session.execute(select(Task).where(Task.status == "pending"))
            pending_tasks = len(result.scalars().all())

            return {
                "users_by_role": users_by_role,
                "open_tickets": open_tickets,
                "pending_tasks": pending_tasks,
                "cached_at": datetime.now().isoformat(),
            }

    @staticmethod
    async def get_user_notes(tg_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить заметки пользователя с кешированием"""
        cache_key = f"user_notes:{tg_id}:{limit}"

        # Пробуем получить из кеша
        cached_notes = await redis_client.get(cache_key)
        if cached_notes:
            return json.loads(cached_notes)

        # Если нет в кеше, получаем из БД
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Note)
                .where(Note.teacher_id == tg_id)
                .order_by(Note.created_at.desc())
                .limit(limit)
            )
            notes = result.scalars().all()

            notes_data = [
                {
                    "id": note.id,
                    "student_name": note.student_name,
                    "text": note.text,
                    "created_at": note.created_at.isoformat() if note.created_at else None,
                }
                for note in notes
            ]

            # Сохраняем в кеш на 5 минут
            await redis_client.setex(cache_key, 300, json.dumps(notes_data))

            return notes_data

    @staticmethod
    async def invalidate_user_notes(tg_id: int) -> None:
        """Инвалидировать кеш заметок пользователя"""
        pattern = f"user_notes:{tg_id}:*"
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)

    @staticmethod
    async def get_frequently_accessed_data() -> Dict[str, Any]:
        """Получить часто запрашиваемые данные"""
        cache_key = "frequent_data"

        # Пробуем получить из кеша
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        # Если нет в кеше, собираем данные
        async with AsyncSessionLocal() as session:
            # Справочники и константы
            data = {
                "roles": [role.value for role in UserRole],
                "task_priorities": ["low", "medium", "high", "urgent"],
                "ticket_statuses": ["open", "in_progress", "resolved", "closed"],
                "cached_at": datetime.now().isoformat(),
            }

            # Сохраняем в кеш на 1 час
            await redis_client.setex(cache_key, 3600, json.dumps(data))

            return data

    @staticmethod
    async def clear_all_caches() -> None:
        """Очистить все кеши"""
        await redis_client.flushdb()
        logger.info("Все кеши очищены")

    @staticmethod
    async def get_cache_stats() -> Dict[str, Any]:
        """Получить статистику кеша"""
        info = await redis_client.info()
        keys = await redis_client.dbsize()

        return {
            "total_keys": keys,
            "memory_usage": info.get("used_memory_human", "N/A"),
            "hit_rate": info.get("keyspace_hits", 0),
            "miss_rate": info.get("keyspace_misses", 0),
        }


# Глобальный экземпляр сервиса
cache_service = CacheService()


# Декораторы для удобного кеширования
def cache_result(ttl: int = CACHE_TTL):
    """Декоратор для кеширования результатов функций"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Создаем ключ кеша на основе аргументов
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Пробуем получить из кеша
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # Выполняем функцию
            result = await func(*args, **kwargs)

            # Сохраняем результат в кеш
            await redis_client.setex(cache_key, ttl, json.dumps(result))

            return result

        return wrapper

    return decorator


# Примеры использования кеширования в репозиториях
@cache_result(ttl=300)
async def get_user_by_tg_id_cached(tg_id: int) -> Optional[Dict[str, Any]]:
    """Получить пользователя с кешированием"""
    return await cache_service.get_user(tg_id)


@cache_result(ttl=900)
async def get_system_statistics_cached() -> Dict[str, Any]:
    """Получить статистику системы с кешированием"""
    return await cache_service.get_system_stats()
