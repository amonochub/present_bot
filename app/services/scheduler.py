import asyncio
import logging
from datetime import date
from sqlalchemy import func, select
from app.db.session import AsyncSessionLocal
from app.db.task import Task, TaskStatus
from app.db.enums import Status
from app.middlewares.metrics import TASKS_TOTAL, TASKS_COMPLETED, TASKS_OVERDUE

logger = logging.getLogger(__name__)

async def kpi_loop():
    """Фоновая корутина для обновления KPI метрик каждые 60 секунд"""
    while True:
        try:
            async with AsyncSessionLocal() as s:
                # Всего поручений
                total = await s.scalar(select(func.count()).select_from(Task))
                
                # Выполнено поручений
                done = await s.scalar(
                    select(func.count()).select_from(Task)
                    .where(Task.status == TaskStatus.COMPLETED))
                
                # Просрочено поручений
                overdue = await s.scalar(
                    select(func.count()).select_from(Task)
                    .where(Task.status == TaskStatus.PENDING, Task.deadline < date.today()))
            
            # Обновляем метрики Prometheus
            TASKS_TOTAL.set(total or 0)
            TASKS_COMPLETED.set(done or 0)
            TASKS_OVERDUE.set(overdue or 0)
            
        except Exception as e:
            # Логируем ошибку, но продолжаем работу
            logger.error(f"Ошибка обновления KPI метрик: {e}")
        
        # Ждем 60 секунд до следующего обновления
        await asyncio.sleep(60) 