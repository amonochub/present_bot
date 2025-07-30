from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.db.note import Note
from app.db.ticket import Ticket
from app.db.task import Task, TaskStatus
from datetime import date
from typing import Dict, Any

async def kpi_summary() -> Dict[str, Any]:
    """Получить сводку KPI метрик"""
    try:
        async with AsyncSessionLocal() as s:
            # всего заметок
            notes_total = await s.scalar(select(func.count()).select_from(Note))

            # заявки IT
            tickets_total = await s.scalar(select(func.count()).select_from(Ticket))
            tickets_done  = await s.scalar(
                select(func.count()).select_from(Ticket).where(Ticket.status == "done"))

            # поручения директора
            tasks_total = await s.scalar(select(func.count()).select_from(Task))
            tasks_done  = await s.scalar(
                select(func.count()).select_from(Task).where(Task.status == TaskStatus.COMPLETED))
            
            # просроченные поручения
            overdue = await s.scalar(
                select(func.count()).select_from(Task)
                .where(Task.status == TaskStatus.PENDING, Task.deadline < date.today()))

        return dict(
            notes_total=notes_total or 0,
            tickets_total=tickets_total or 0,
            tickets_done=tickets_done or 0,
            tasks_total=tasks_total or 0,
            tasks_done=tasks_done or 0,
            overdue=overdue or 0,
        )
    except Exception as e:
        # Возвращаем нулевые значения в случае ошибки
        return dict(
            notes_total=0,
            tickets_total=0,
            tickets_done=0,
            tasks_total=0,
            tasks_done=0,
            overdue=0,
        ) 