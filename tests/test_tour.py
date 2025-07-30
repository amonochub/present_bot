import pytest
import asyncio
from app.db.user import User
from app.roles import ROLES


def test_tour_roles():
    """Тест ролей для тура"""
    # Проверяем, что все роли доступны для тура
    tour_roles = ["teacher", "admin", "director", "student", "parent", "psych"]
    
    for role in tour_roles:
        assert role in ROLES
        assert ROLES[role] is not None


def test_tour_user_creation():
    """Тест создания пользователя для тура"""
    # Создаем тестового пользователя
    user = User(
        tg_id=2001,
        username="test_tour_user",
        first_name="Tester",
        last_name="Tour",
        role="student",
        is_active=True
    )
    
    # Проверяем, что пользователь создан
    assert user.tg_id == 2001
    assert user.role == "student"


def test_tour_flow_logic():
    """Тест логики тура"""
    # Проверяем, что тур содержит все необходимые роли
    expected_roles = ["teacher", "admin", "director", "student", "parent", "psych"]
    
    for role in expected_roles:
        assert role in ROLES
        assert ROLES[role] in ["Учитель", "Администрация", "Директор", "Ученик", "Родитель", "Психолог"] 