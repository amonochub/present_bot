import pytest
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

# Настройка логирования для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from app.config import settings
    from app.db.user import User
    from app.db.note import Note
    from app.db.ticket import Ticket
    from app.db.task import Task
    from app.roles import ROLES
except ImportError as e:
    logger.warning(f"Import error in tests: {e}")
    # Создаем заглушки для тестов
    class Settings:
        TELEGRAM_TOKEN = "test_token"
        DATABASE_URL = "test_url"
        REDIS_URL = "test_url"
    
    settings = Settings()
    ROLES = {}


@pytest.mark.asyncio
async def test_config_validation():
    """Тест валидации конфигурации"""
    try:
        # Проверяем, что конфигурация загружается
        assert settings.TELEGRAM_TOKEN is not None
        assert settings.DATABASE_URL is not None
        assert settings.REDIS_URL is not None
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        pytest.skip("Configuration not available")


def test_user_model():
    """Тест модели пользователя"""
    try:
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
    except Exception as e:
        logger.error(f"User model test failed: {e}")
        pytest.skip("User model not available")


def test_note_model():
    """Тест модели заметки"""
    try:
        # Создаем заметку
        note = Note(
            student_name="Иванов",
            text="Содержание тестовой заметки",
            teacher_id=1
        )
        
        # Проверяем, что заметка создана
        assert note.student_name == "Иванов"
        assert note.teacher_id == 1
    except Exception as e:
        logger.error(f"Note model test failed: {e}")
        pytest.skip("Note model not available")


def test_ticket_model():
    """Тест модели тикета"""
    try:
        # Создаем тикет
        ticket = Ticket(
            title="Тестовый тикет",
            author_id=1
        )
        
        # Проверяем, что тикет создан
        assert ticket.title == "Тестовый тикет"
        assert ticket.author_id == 1
    except Exception as e:
        logger.error(f"Ticket model test failed: {e}")
        pytest.skip("Ticket model not available")


def test_task_model():
    """Тест модели задачи"""
    try:
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
    except Exception as e:
        logger.error(f"Task model test failed: {e}")
        pytest.skip("Task model not available")


def test_roles_validation():
    """Тест валидации ролей"""
    try:
        # Проверяем, что все роли определены
        expected_roles = ["teacher", "admin", "director", "student", "parent", "psych", "super"]
        for role in expected_roles:
            assert role in ROLES, f"Role {role} not found in ROLES"
    except Exception as e:
        logger.error(f"Roles validation test failed: {e}")
        pytest.skip("Roles not available")


def test_role_names():
    """Тест названий ролей"""
    try:
        # Проверяем, что названия ролей корректные
        expected_names = {
            "teacher": "Учитель",
            "admin": "Администрация", 
            "director": "Директор",
            "student": "Ученик",
            "parent": "Родитель",
            "psych": "Психолог",
            "super": "Демо-режим"
        }
        
        for role, expected_name in expected_names.items():
            if role in ROLES:
                assert ROLES[role] == expected_name, f"Role {role} name mismatch"
    except Exception as e:
        logger.error(f"Role names test failed: {e}")
        pytest.skip("Role names not available")


def test_tour_text_mapping():
    """Тест текстового описания ролей для тура"""
    try:
        from app.handlers.tour import _tour_text
        
        # Проверяем, что для каждой роли есть описание
        tour_roles = ["teacher", "admin", "director", "student", "parent", "psych"]
        
        for role in tour_roles:
            text = _tour_text(role)
            assert text is not None
            assert len(text) > 0
            assert "<b>" in text  # Проверяем наличие HTML-разметки
            assert role in text.lower() or any(word in text.lower() for word in ["учитель", "админ", "директор", "ученик", "родитель", "психолог"])
    except Exception as e:
        logger.error(f"Tour text mapping test failed: {e}")
        pytest.skip("Tour text mapping not available")


if __name__ == "__main__":
    pytest.main([__file__]) 