from datetime import date, timedelta

from app.db.task import Task, TaskPriority, TaskStatus
from app.db.user import User


def test_task_status_enum():
    """Тест enum статусов задач"""
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.CANCELLED.value == "cancelled"


def test_task_priority_enum():
    """Тест enum приоритетов задач"""
    assert TaskPriority.LOW.value == "low"
    assert TaskPriority.MEDIUM.value == "medium"
    assert TaskPriority.HIGH.value == "high"
    assert TaskPriority.URGENT.value == "urgent"


def test_task_model():
    """Тест модели задачи"""
    # Создаем тестовую задачу
    task = Task(
        title="Тестовая задача",
        description="Описание тестовой задачи",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        deadline=date.today() + timedelta(days=1),
        author_id=1,
    )

    # Проверяем, что задача создана
    assert task.title == "Тестовая задача"
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM
    assert task.author_id == 1


def test_user_model():
    """Тест модели пользователя"""
    # Создаем тестового пользователя
    user = User(
        tg_id=123456789,
        username="test_user",
        first_name="Тест",
        last_name="Пользователь",
        role="teacher",
        is_active=True,
    )

    # Проверяем, что пользователь создан
    assert user.tg_id == 123456789
    assert user.role == "teacher"
    assert user.is_active is True
