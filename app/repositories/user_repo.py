import logging
from typing import List

from sqlalchemy import select, update

from app.db.session import AsyncSessionLocal
from app.db.user import User

logger = logging.getLogger(__name__)


async def teacher_ids() -> List[int]:
    """Получить список Telegram ID учителей"""
    try:
        async with AsyncSessionLocal() as s:
            rows = await s.scalars(
                select(User.tg_id).where(User.role == "teacher", User.tg_id.is_not(None))
            )
            return list(rows)
    except Exception as e:
        logger.error(f"Ошибка при получении ID учителей: {e}")
        return []


async def get_user(tg_id: int) -> User:
    """Получить пользователя по Telegram ID"""
    try:
        async with AsyncSessionLocal() as s:
            result = await s.execute(select(User).where(User.tg_id == tg_id))
            user = result.scalar_one_or_none()
            if not user:
                # Создаем нового пользователя
                user = User(
                    tg_id=tg_id, 
                    role="student", 
                    seen_intro=False,
                    theme="light",
                    notifications_enabled=True,
                    email_notifications=False,
                    is_active=True,
                    used=False
                )  # По умолчанию
                s.add(user)
                await s.commit()
                await s.refresh(user)
            return user
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя {tg_id}: {e}")
        # Создаем пользователя по умолчанию в случае ошибки
        return User(
            tg_id=tg_id, 
            role="student", 
            seen_intro=False,
            theme="light",
            notifications_enabled=True,
            email_notifications=False,
            is_active=True,
            used=False
        )


async def update_user_intro(tg_id: int, seen_intro: bool) -> None:
    """Обновить статус онбординга пользователя"""
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(update(User).where(User.tg_id == tg_id).values(seen_intro=seen_intro))
            await s.commit()
    except Exception as e:
        logger.error(f"Ошибка при обновлении онбординга для {tg_id}: {e}")
        raise


async def create_user(tg_id: int, role: str = "student", seen_intro: bool = False) -> User:
    """Создать нового пользователя"""
    try:
        async with AsyncSessionLocal() as s:
            user = User(
                tg_id=tg_id, 
                role=role, 
                seen_intro=seen_intro,
                theme="light",
                notifications_enabled=True,
                email_notifications=False,
                is_active=True,
                used=False
            )
            s.add(user)
            await s.commit()
            await s.refresh(user)
            return user
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя {tg_id}: {e}")
        raise
