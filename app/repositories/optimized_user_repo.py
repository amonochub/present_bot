"""
Оптимизированный репозиторий пользователей с кешированием и профилированием
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, update

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.roles import UserRole
from app.services.cache_service import cache_result, cache_service
from app.services.performance_monitor import db_profiler, monitor_performance

logger = logging.getLogger(__name__)


class OptimizedUserRepository:
    """Оптимизированный репозиторий пользователей с кешированием"""

    @staticmethod
    @monitor_performance("get_user_by_tg_id")
    async def get_user_by_tg_id(tg_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID с кешированием"""
        # Сначала пробуем получить из кеша
        cached_user = await cache_service.get_user(tg_id)
        if cached_user:
            return cached_user

        # Если нет в кеше, получаем из БД
        async with db_profiler.profile_query(
            "get_user_by_tg_id", "SELECT * FROM users WHERE tg_id = ?"
        ):
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
                    await cache_service.invalidate_user(tg_id)
                    return user_data

        return None

    @staticmethod
    @monitor_performance("get_users_by_role")
    @cache_result(ttl=300)  # Кешируем на 5 минут
    async def get_users_by_role(role: UserRole, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить пользователей по роли с кешированием"""
        async with db_profiler.profile_query(
            "get_users_by_role", "SELECT * FROM users WHERE role = ? LIMIT ?"
        ):
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User)
                    .where(User.role == role.value)
                    .where(User.is_active.is_(True))
                    .limit(limit)
                )
                users = result.scalars().all()

                return [
                    {
                        "id": user.id,
                        "tg_id": user.tg_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "is_active": user.is_active,
                    }
                    for user in users
                ]

    @staticmethod
    @monitor_performance("get_active_users_count")
    @cache_result(ttl=600)  # Кешируем на 10 минут
    async def get_active_users_count() -> Dict[str, int]:
        """Получить количество активных пользователей по ролям"""
        async with db_profiler.profile_query(
            "get_active_users_count",
            "SELECT role, COUNT(*) FROM users WHERE is_active = true GROUP BY role",
        ):
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User.role, User.id).where(User.is_active.is_(True))
                )
                users = result.all()

                counts = {}
                for role in UserRole:
                    counts[role.value] = len([u for u in users if u[0] == role.value])

                return counts

    @staticmethod
    @monitor_performance("create_user")
    async def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать пользователя с инвалидацией кеша"""
        async with db_profiler.profile_query("create_user", "INSERT INTO users"):
            async with AsyncSessionLocal() as session:
                user = User(**user_data)
                session.add(user)
                await session.commit()
                await session.refresh(user)

                # Инвалидируем кеш
                if user.tg_id:
                    await cache_service.invalidate_user(int(user.tg_id))

                return {
                    "id": user.id,
                    "tg_id": user.tg_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_active": user.is_active,
                }

    @staticmethod
    @monitor_performance("update_user")
    async def update_user(tg_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновить пользователя с инвалидацией кеша"""
        async with db_profiler.profile_query("update_user", f"UPDATE users WHERE tg_id = {tg_id}"):
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    update(User).where(User.tg_id == tg_id).values(**update_data).returning(User)
                )
                user = result.scalar_one_or_none()

                if user:
                    await session.commit()

                    # Инвалидируем кеш
                    await cache_service.invalidate_user(tg_id)

                    return {
                        "id": user.id,
                        "tg_id": user.tg_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "is_active": user.is_active,
                    }

        return None

    @staticmethod
    @monitor_performance("delete_user")
    async def delete_user(tg_id: int) -> bool:
        """Удалить пользователя с инвалидацией кеша"""
        async with db_profiler.profile_query(
            "delete_user", "DELETE FROM users WHERE tg_id = ?"
        ):
            async with AsyncSessionLocal() as session:
                result = await session.execute(delete(User).where(User.tg_id == tg_id))
                await session.commit()

                # Инвалидируем кеш
                await cache_service.invalidate_user(tg_id)

                return result.rowcount > 0

    @staticmethod
    @monitor_performance("search_users")
    async def search_users(
        query: str, role: Optional[UserRole] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Поиск пользователей с оптимизированными запросами"""
        search_query = (
            "SELECT * FROM users WHERE "
            "(username ILIKE ? OR first_name ILIKE ? OR last_name ILIKE ?)"
        )

        async with db_profiler.profile_query("search_users", search_query):
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.is_active.is_(True))

                # Добавляем поиск по тексту
                stmt = stmt.where(
                    (User.username.ilike(f"%{query}%"))
                    | (User.first_name.ilike(f"%{query}%"))
                    | (User.last_name.ilike(f"%{query}%"))
                )

                # Фильтр по роли
                if role:
                    stmt = stmt.where(User.role == role.value)

                stmt = stmt.limit(limit)

                result = await session.execute(stmt)
                users = result.scalars().all()

                return [
                    {
                        "id": user.id,
                        "tg_id": user.tg_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "is_active": user.is_active,
                    }
                    for user in users
                ]

    @staticmethod
    @monitor_performance("get_user_statistics")
    @cache_result(ttl=900)  # Кешируем на 15 минут
    async def get_user_statistics() -> Dict[str, Any]:
        """Получить статистику пользователей"""
        async with db_profiler.profile_query(
            "get_user_statistics",
            "SELECT COUNT(*), role, is_active FROM users GROUP BY role, is_active",
        ):
            async with AsyncSessionLocal() as session:
                # Общая статистика
                total_result = await session.execute(select(User.id))
                total_users = len(total_result.scalars().all())

                # Активные пользователи
                active_result = await session.execute(
                    select(User.id).where(User.is_active.is_(True))
                )
                active_users = len(active_result.scalars().all())

                # Статистика по ролям
                role_stats = {}
                for role in UserRole:
                    result = await session.execute(select(User.id).where(User.role == role.value))
                    role_stats[role.value] = len(result.scalars().all())

                # Новые пользователи за последние 7 дней
                from datetime import datetime, timedelta

                week_ago = datetime.now() - timedelta(days=7)

                new_users_result = await session.execute(
                    select(User.id).where(User.created_at >= week_ago)
                )
                new_users = len(new_users_result.scalars().all())

                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "inactive_users": total_users - active_users,
                    "role_distribution": role_stats,
                    "new_users_week": new_users,
                    "cached_at": datetime.now().isoformat(),
                }

    @staticmethod
    @monitor_performance("bulk_update_users")
    async def bulk_update_users(updates: List[Dict[str, Any]]) -> int:
        """Массовое обновление пользователей"""
        if not updates:
            return 0

        async with db_profiler.profile_query(
            "bulk_update_users", f"BULK UPDATE {len(updates)} users"
        ):
            async with AsyncSessionLocal() as session:
                updated_count = 0
                invalidated_tg_ids = []

                for update_data in updates:
                    tg_id = update_data.get("tg_id")
                    if not tg_id:
                        continue

                    result = await session.execute(
                        update(User)
                        .where(User.tg_id == tg_id)
                        .values(**{k: v for k, v in update_data.items() if k != "tg_id"})
                    )

                    if result.rowcount > 0:
                        updated_count += 1
                        invalidated_tg_ids.append(tg_id)

                await session.commit()

                # Инвалидируем кеши для обновленных пользователей
                for tg_id in invalidated_tg_ids:
                    await cache_service.invalidate_user(tg_id)

                return updated_count


# Глобальный экземпляр репозитория
optimized_user_repo = OptimizedUserRepository()


# Функции-обертки для обратной совместимости
async def get_user(tg_id: int) -> Optional[Dict[str, Any]]:
    """Получить пользователя (обертка для обратной совместимости)"""
    return await optimized_user_repo.get_user_by_tg_id(tg_id)


async def get_users_by_role(role: UserRole, limit: int = 100) -> List[Dict[str, Any]]:
    """Получить пользователей по роли (обертка для обратной совместимости)"""
    return await optimized_user_repo.get_users_by_role(role, limit)


async def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Создать пользователя (обертка для обратной совместимости)"""
    return await optimized_user_repo.create_user(user_data)


async def update_user(tg_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Обновить пользователя (обертка для обратной совместимости)"""
    return await optimized_user_repo.update_user(tg_id, update_data)
