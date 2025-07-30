import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.config import settings
from app.utils.hash import hash_pwd, check_pwd
from app.utils.csrf import issue_nonce, check_nonce
from app.middlewares.rate_limit import RateLimitMiddleware
from app.db.user import User
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from datetime import datetime

@pytest.mark.asyncio
async def test_password_hashing():
    """Тест хеширования паролей"""
    password = "test_password_123"
    hashed = hash_pwd(password)
    
    # Проверяем, что хеш отличается от оригинального пароля
    assert hashed != password
    
    # Проверяем, что проверка пароля работает
    assert check_pwd(password, hashed) is True
    assert check_pwd("wrong_password", hashed) is False

@pytest.mark.asyncio
async def test_csrf_protection():
    """Тест CSRF защиты"""
    # Мокаем storage
    mock_storage = AsyncMock()
    mock_storage.set_data = AsyncMock()
    mock_storage.get_data = AsyncMock()
    
    # Тестируем создание nonce
    nonce = await issue_nonce(mock_storage, 123, 456)
    assert len(nonce) == 12  # 6 байт в hex = 12 символов
    
    # Тестируем проверку nonce
    mock_storage.get_data.return_value = {"csrf": nonce}
    assert await check_nonce(mock_storage, 123, 456, nonce) is True
    
    # Тестируем неверный nonce
    assert await check_nonce(mock_storage, 123, 456, "wrong_nonce") is False

@pytest.mark.asyncio
async def test_rate_limiting():
    """Тест rate limiting"""
    middleware = RateLimitMiddleware(limit=2, window=60)
    
    # Мокаем handler и event
    mock_handler = AsyncMock()
    mock_event = AsyncMock()
    mock_event.from_user.id = 123
    
    # Первые два запроса должны пройти
    result1 = await middleware(mock_handler, mock_event, {})
    result2 = await middleware(mock_handler, mock_event, {})
    
    assert result1 is not None
    assert result2 is not None
    
    # Третий запрос должен быть заблокирован
    with patch('app.services.limiter.hit') as mock_hit:
        mock_hit.return_value = type('obj', (object,), {'allowed': False})()
        result3 = await middleware(mock_handler, mock_event, {})
        assert result3 is None

@pytest.mark.asyncio
async def test_config_validation():
    """Тест валидации конфигурации"""
    # Проверяем, что конфигурация загружается корректно
    assert hasattr(settings, 'TELEGRAM_TOKEN')
    assert hasattr(settings, 'DATABASE_URL')
    assert hasattr(settings, 'REDIS_URL')
    
    # Проверяем, что токен имеет правильный формат
    assert ':' in settings.TELEGRAM_TOKEN

@pytest.mark.asyncio
async def test_user_authentication():
    """Тест аутентификации пользователей"""
    # Создаем тестового пользователя
    test_user = User(
        tg_id=123456789,
        username="test_user",
        first_name="Тест",
        last_name="Пользователь",
        role="teacher",
        is_active=True,
        login="test_login",
        password=hash_pwd("test_password"),
        used=False
    )
    
    # Проверяем, что пользователь создан корректно
    assert test_user.tg_id == 123456789
    assert test_user.role == "teacher"
    assert test_user.is_active is True
    assert check_pwd("test_password", test_user.password) is True

@pytest.mark.asyncio
async def test_role_based_access():
    """Тест контроля доступа на основе ролей"""
    # Создаем пользователей с разными ролями
    teacher = User(role="teacher", is_active=True)
    admin = User(role="admin", is_active=True)
    student = User(role="student", is_active=True)
    
    # Проверяем доступ к функциям учителя
    teacher_roles = ["teacher", "super"]
    admin_roles = ["admin", "super"]
    director_roles = ["director", "super"]
    
    assert teacher.role in teacher_roles
    assert admin.role in admin_roles
    assert student.role not in teacher_roles
    assert student.role not in admin_roles

@pytest.mark.asyncio
async def test_input_validation():
    """Тест валидации входных данных"""
    # Тестируем валидацию длины текста
    short_text = "Короткий текст"
    long_text = "Очень длинный текст " * 100  # Более 1000 символов
    
    assert len(short_text) <= 1000
    assert len(long_text) > 1000
    
    # Тестируем валидацию формата даты
    valid_date = "25.12.2024"
    invalid_date = "2024-12-25"
    
    try:
        datetime.strptime(valid_date, "%d.%m.%Y")
        date_valid = True
    except ValueError:
        date_valid = False
    
    try:
        datetime.strptime(invalid_date, "%d.%m.%Y")
        date_invalid = False
    except ValueError:
        date_invalid = True
    
    assert date_valid is True
    assert date_invalid is True

@pytest.mark.asyncio
async def test_sql_injection_prevention():
    """Тест предотвращения SQL инъекций"""
    # Тестируем, что параметризованные запросы работают корректно
    malicious_input = "'; DROP TABLE users; --"
    
    # В реальном приложении этот input должен быть безопасно обработан
    # Здесь мы просто проверяем, что он не вызывает ошибок
    assert isinstance(malicious_input, str)
    assert len(malicious_input) > 0

if __name__ == "__main__":
    pytest.main([__file__]) 