from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.user import User
from typing import List
import logging

logger = logging.getLogger(__name__)

async def teacher_ids() -> List[int]:
    """Получить список Telegram ID учителей"""
    try:
        async with AsyncSessionLocal() as s:
            rows = await s.scalars(
                select(User.tg_id).where(
                    User.role == "teacher",
                    User.tg_id.is_not(None))
            )
            return list(rows)
    except Exception as e:
        logger.error(f"Ошибка при получении ID учителей: {e}")
        return [] 