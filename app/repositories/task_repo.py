from datetime import date
from typing import List

from sqlalchemy import select, update

from app.db.enums import Status
from app.db.session import AsyncSessionLocal
from app.db.task import Task, TaskStatus


async def create_task(title: str, description: str, deadline: date | None, author_id: int) -> Task:
    """Создать новую задачу"""
    async with AsyncSessionLocal() as s:
        task = Task(
            title=title,
            description=description,
            deadline=deadline,
            author_id=author_id,
            status=TaskStatus.PENDING
        )
        s.add(task)
        await s.commit()
        await s.refresh(task)
        return task


async def list_open() -> List[Task]:
    """Получить список открытых поручений"""
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(Task).where(Task.status == TaskStatus.PENDING))
        tasks = result.scalars().all()
        return list(tasks)


async def set_status(task_id: int, status: Status) -> bool:
    """Изменить статус поручения"""
    try:
        async with AsyncSessionLocal() as s:
            # Конвертируем Status в TaskStatus
            task_status_map = {
                Status.open: TaskStatus.PENDING,
                Status.in_progress: TaskStatus.IN_PROGRESS,
                Status.done: TaskStatus.COMPLETED,
            }
            await s.execute(
                update(Task).where(Task.id == task_id).values(status=task_status_map[status])
            )
            await s.commit()
            return True
    except Exception:
        return False


async def get_overdue_count() -> int:
    """Получить количество просроченных поручений"""
    async with AsyncSessionLocal() as s:
        result = await s.scalar(
            select(Task).where(Task.status == TaskStatus.PENDING, Task.deadline < date.today())
        )
        return result or 0
