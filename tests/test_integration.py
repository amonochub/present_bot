"""
Интеграционные тесты для School_bot
Проверяют взаимодействие между различными компонентами системы
"""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.middlewares.csrf import CSRFMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.repositories.user_repo import get_user, update_user_intro
from app.routes.intro import INTRO_SLIDES, send_intro_slide
from app.services.limiter import LimitResult, hit


class TestDatabaseIntegration:
    """Тесты интеграции с базой данных"""

    @pytest.mark.asyncio
    async def test_user_creation_and_retrieval(self):
        """Тест создания и получения пользователя"""
        # Подготавливаем тестовые данные
        test_tg_id = 123456789
        test_role = "teacher"

        # Создаем пользователя
        user = await get_user(test_tg_id)

        # Проверяем, что пользователь создан корректно
        assert user.tg_id == test_tg_id
        assert user.role == "student"  # По умолчанию
        assert user.seen_intro is False
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_user_intro_update(self):
        """Тест обновления статуса онбординга"""
        test_tg_id = 987654321

        # Создаем пользователя
        user = await get_user(test_tg_id)
        assert user.seen_intro is False

        # Обновляем статус
        await update_user_intro(test_tg_id, True)

        # Проверяем обновление
        updated_user = await get_user(test_tg_id)
        assert updated_user.seen_intro is True

    @pytest.mark.asyncio
    async def test_teacher_ids_retrieval(self):
        """Тест получения списка ID учителей"""
        from app.repositories.user_repo import teacher_ids

        # Создаем тестовых учителей
        test_teachers = [
            {"tg_id": 111, "role": "teacher"},
            {"tg_id": 222, "role": "teacher"},
            {"tg_id": 333, "role": "student"},  # Не учитель
        ]

        # Получаем список ID учителей
        teacher_ids_list = await teacher_ids()

        # Проверяем, что возвращается список
        assert isinstance(teacher_ids_list, list)
        # Проверяем, что все элементы - числа
        assert all(isinstance(tid, int) for tid in teacher_ids_list)


class TestMiddlewareIntegration:
    """Тесты интеграции middleware"""

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_integration(self):
        """Тест интеграции rate limit middleware"""
        middleware = RateLimitMiddleware(limit=2, window=60)

        # Создаем мок сообщения
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = AsyncMock()
        mock_message.from_user.id = 12345

        # Создаем мок handler
        mock_handler = AsyncMock()

        # Первые два запроса должны пройти
        with patch("app.services.limiter.hit") as mock_hit:
            mock_hit.return_value = LimitResult(allowed=True)

            result1 = await middleware(mock_handler, mock_message, {})
            result2 = await middleware(mock_handler, mock_message, {})

            assert result1 is not None
            assert result2 is not None
            assert mock_hit.call_count == 2

    @pytest.mark.asyncio
    async def test_csrf_middleware_integration(self):
        """Тест интеграции CSRF middleware"""
        middleware = CSRFMiddleware()

        # Создаем мок callback query
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "test_nonce:test_data"
        mock_callback.message = AsyncMock()
        mock_callback.message.chat.id = 12345
        mock_callback.from_user.id = 67890

        # Создаем мок storage
        mock_storage = AsyncMock()
        mock_storage.get_data.return_value = {"csrf": "test_nonce"}

        # Создаем мок handler
        mock_handler = AsyncMock()

        # Создаем контекст данных
        data = {"dp": AsyncMock()}
        data["dp"].storage = mock_storage

        # Тестируем middleware
        with patch("app.utils.csrf.check_nonce") as mock_check:
            mock_check.return_value = True

            result = await middleware(mock_handler, mock_callback, data)

            assert result is not None
            assert mock_callback.data == "test_data"  # Проверяем, что данные обновлены


class TestIntroIntegration:
    """Тесты интеграции онбординга"""

    @pytest.mark.asyncio
    async def test_intro_slides_integration(self):
        """Тест интеграции слайдов онбординга"""
        # Проверяем структуру слайдов
        assert len(INTRO_SLIDES) == 6

        # Проверяем каждый слайд
        for i, slide in enumerate(INTRO_SLIDES):
            assert "title" in slide
            assert "text" in slide
            assert "icon" in slide
            assert isinstance(slide["title"], str)
            assert isinstance(slide["text"], str)
            assert isinstance(slide["icon"], str)
            assert len(slide["text"]) > 10

    @pytest.mark.asyncio
    async def test_send_intro_slide_integration(self):
        """Тест интеграции отправки слайда"""
        # Создаем мок сообщения
        mock_message = AsyncMock(spec=Message)

        # Тестируем отправку первого слайда
        await send_intro_slide(mock_message, 0, "ru")

        # Проверяем, что сообщение было отправлено
        mock_message.answer.assert_called_once()

        # Проверяем структуру отправленного сообщения
        call_args = mock_message.answer.call_args
        assert "parse_mode" in call_args[1]
        assert call_args[1]["parse_mode"] == "HTML"
        assert "reply_markup" in call_args[1]


class TestSecurityIntegration:
    """Тесты интеграции безопасности"""

    @pytest.mark.asyncio
    async def test_password_hashing_integration(self):
        """Тест интеграции хеширования паролей"""
        from app.utils.hash import check_pwd, hash_pwd

        # Тестовый пароль
        test_password = "test_password_123"

        # Хешируем пароль
        hashed = hash_pwd(test_password)

        # Проверяем, что хеш отличается от оригинала
        assert hashed != test_password

        # Проверяем валидацию правильного пароля
        assert check_pwd(test_password, hashed) is True

        # Проверяем валидацию неправильного пароля
        assert check_pwd("wrong_password", hashed) is False

    @pytest.mark.asyncio
    async def test_csrf_token_integration(self):
        """Тест интеграции CSRF токенов"""
        from app.utils.csrf import check_nonce, escape_html, issue_nonce

        # Создаем мок storage
        mock_storage = AsyncMock()

        # Создаем токен
        nonce = await issue_nonce(mock_storage, 12345, 67890)

        # Проверяем, что токен создан
        assert isinstance(nonce, str)
        assert len(nonce) > 0

        # Проверяем валидацию токена
        is_valid = await check_nonce(mock_storage, 12345, 67890, nonce)
        assert is_valid is True

        # Проверяем экранирование HTML
        test_html = "<script>alert('xss')</script>"
        escaped = escape_html(test_html)
        assert "<" not in escaped
        assert ">" not in escaped

    @pytest.mark.asyncio
    async def test_rate_limiter_integration(self):
        """Тест интеграции rate limiter"""
        # Тестируем успешный запрос
        result = await hit("test_key", 10, 60)
        assert isinstance(result, LimitResult)
        assert result.allowed is True

        # Тестируем превышение лимита
        # Сначала делаем 10 запросов
        for _ in range(10):
            await hit("test_key_limit", 10, 60)

        # 11-й запрос должен быть заблокирован
        result = await hit("test_key_limit", 10, 60)
        assert result.allowed is False


class TestConfigurationIntegration:
    """Тесты интеграции конфигурации"""

    def test_settings_validation_integration(self):
        """Тест интеграции валидации настроек"""
        from app.config import Settings

        # Тестируем валидацию Telegram токена
        with pytest.raises(ValueError):
            Settings(TELEGRAM_TOKEN="invalid_token")

        # Тестируем валидацию пароля БД
        with pytest.raises(ValueError):
            Settings(DB_PASS="short")

        # Тестируем валидацию порта
        with pytest.raises(ValueError):
            Settings(DB_PORT=70000)

        # Тестируем валидацию дней хранения
        with pytest.raises(ValueError):
            Settings(KEEP_DAYS=400)


class TestErrorHandlingIntegration:
    """Тесты интеграции обработки ошибок"""

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Тест обработки ошибок базы данных"""
        # Тестируем обработку ошибки при создании пользователя
        with patch("app.repositories.user_repo.AsyncSessionLocal") as mock_session:
            mock_session.side_effect = Exception("Database connection failed")

            # Должен вернуть пользователя по умолчанию
            user = await get_user(999999)
            assert user.tg_id == 999999
            assert user.role == "student"

    @pytest.mark.asyncio
    async def test_middleware_error_handling(self):
        """Тест обработки ошибок в middleware"""
        middleware = RateLimitMiddleware(limit=2, window=60)

        # Создаем сообщение без пользователя
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = None

        mock_handler = AsyncMock()

        # Middleware должен обработать ошибку корректно
        result = await middleware(mock_handler, mock_message, {})
        assert result is not None


@pytest.fixture
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для тестовой сессии БД"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_bot() -> Bot:
    """Фикстура для мока бота"""
    return AsyncMock(spec=Bot)


@pytest.fixture
def mock_dispatcher() -> Dispatcher:
    """Фикстура для мока диспетчера"""
    return AsyncMock(spec=Dispatcher)


@pytest.fixture
def mock_fsm_context() -> FSMContext:
    """Фикстура для мока FSM контекста"""
    return AsyncMock(spec=FSMContext)
