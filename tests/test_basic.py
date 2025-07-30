import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.user import User
from app.db.note import Note
from app.db.ticket import Ticket
from app.db.task import Task
from app.roles import ROLES


@pytest.mark.asyncio
async def test_config_validation():
    """Тест валидации конфигурации"""
    # Проверяем, что конфигурация загружается
    assert settings.TELEGRAM_TOKEN is not None
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None


def test_user_model():
    """Тест модели пользователя"""
    # Создаем тестового пользователя
    user = User(
        tg_id=123456789,
        username="test_user",
        first_name="Тест",
        last_name="Пользователь",
        role="teacher",
        is_active=True
    )
    
    # Проверяем, что пользователь создан
    assert user.tg_id == 123456789
    assert user.role == "teacher"
    assert user.is_active is True


def test_note_model():
    """Тест модели заметки"""
    # Создаем заметку
    note = Note(
        student_name="Иванов",
        text="Содержание тестовой заметки",
        teacher_id=1
    )
    
    # Проверяем, что заметка создана
    assert note.student_name == "Иванов"
    assert note.teacher_id == 1


def test_ticket_model():
    """Тест модели тикета"""
    # Создаем тикет
    ticket = Ticket(
        title="Тестовый тикет",
        author_id=1
    )
    
    # Проверяем, что тикет создан
    assert ticket.title == "Тестовый тикет"
    assert ticket.author_id == 1


def test_task_model():
    """Тест модели задачи"""
    # Создаем задачу
    task = Task(
        title="Тестовая задача",
        description="Описание тестовой задачи",
        author_id=1,
        status="active"
    )
    
    # Проверяем, что задача создана
    assert task.title == "Тестовая задача"
    assert task.author_id == 1


def test_roles_validation():
    """Тест валидации ролей"""
    # Проверяем, что все роли определены
    assert "teacher" in ROLES
    assert "admin" in ROLES
    assert "director" in ROLES
    assert "student" in ROLES
    assert "parent" in ROLES
    assert "psych" in ROLES
    assert "super" in ROLES


def test_role_names():
    """Тест названий ролей"""
    # Проверяем, что названия ролей корректные
    assert ROLES["teacher"] == "Учитель"
    assert ROLES["admin"] == "Администрация"
    assert ROLES["director"] == "Директор"
    assert ROLES["student"] == "Ученик"
    assert ROLES["parent"] == "Родитель"
    assert ROLES["psych"] == "Психолог"
    assert ROLES["super"] == "Демо-режим"


def test_tour_text_mapping():
    """Тест текстового описания ролей для тура"""
    from app.handlers.tour import _tour_text
    
    # Проверяем, что для каждой роли есть описание
    tour_roles = ["teacher", "admin", "director", "student", "parent", "psych"]
    
    for role in tour_roles:
        text = _tour_text(role)
        assert text is not None
        assert len(text) > 0
        assert "<b>" in text  # Проверяем наличие HTML-разметки
        assert role in text.lower() or any(word in text.lower() for word in ["учитель", "админ", "директор", "ученик", "родитель", "психолог"])


if __name__ == "__main__":
    pytest.main([__file__]) 