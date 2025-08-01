"""
Тесты edge cases и граничных условий для School_bot
Проверяют поведение системы в нестандартных ситуациях
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import CallbackQuery, Message

from app.middlewares.csrf import CSRFMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.repositories.user_repo import get_user, update_user_intro
from app.services.limiter import LimitResult, hit
from app.utils.csrf import check_nonce, escape_html, issue_nonce
from app.utils.hash import check_pwd, hash_pwd


class TestRateLimitEdgeCases:
    """Тесты edge cases для rate limiting"""

    @pytest.mark.asyncio
    async def test_rate_limit_zero_limit(self):
        """Тест rate limiting с нулевым лимитом"""
        middleware = RateLimitMiddleware(limit=0, window=60)

        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = AsyncMock()
        mock_message.from_user.id = 12345

        mock_handler = AsyncMock()

        # С нулевым лимитом все запросы должны блокироваться
        with patch("app.services.limiter.hit") as mock_hit:
            mock_hit.return_value = LimitResult(allowed=False)

            result = await middleware(mock_handler, mock_message, {})

            assert result is None  # Запрос заблокирован

    @pytest.mark.asyncio
    async def test_rate_limit_negative_window(self):
        """Тест rate limiting с отрицательным окном"""
        # Создаем middleware с отрицательным окном
        middleware = RateLimitMiddleware(limit=10, window=-1)

        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = AsyncMock()
        mock_message.from_user.id = 12345

        mock_handler = AsyncMock()

        # Должен обработать корректно
        result = await middleware(mock_handler, mock_message, {})
        assert result is not None

    @pytest.mark.asyncio
    async def test_rate_limit_no_user(self):
        """Тест rate limiting без пользователя"""
        middleware = RateLimitMiddleware(limit=10, window=60)

        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = None  # Нет пользователя

        mock_handler = AsyncMock()

        # Должен пропустить запрос
        result = await middleware(mock_handler, mock_message, {})
        assert result is not None

    @pytest.mark.asyncio
    async def test_rate_limit_concurrent_requests(self):
        """Тест rate limiting при одновременных запросах"""
        middleware = RateLimitMiddleware(limit=5, window=60)

        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = AsyncMock()
        mock_message.from_user.id = 12345

        mock_handler = AsyncMock()

        # Симулируем одновременные запросы
        async def make_request():
            return await middleware(mock_handler, mock_message, {})

        # Создаем несколько одновременных запросов
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем, что все запросы обработаны
        assert len(results) == 10


class TestCSRFEdgeCases:
    """Тесты edge cases для CSRF защиты"""

    @pytest.mark.asyncio
    async def test_csrf_no_data(self):
        """Тест CSRF без данных"""
        middleware = CSRFMiddleware()

        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = None  # Нет данных

        mock_handler = AsyncMock()

        # Должен обработать ошибку
        result = await middleware(mock_handler, mock_callback, {})
        assert result is None

    @pytest.mark.asyncio
    async def test_csrf_malformed_data(self):
        """Тест CSRF с неправильно сформированными данными"""
        middleware = CSRFMiddleware()

        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "no_colon_separator"  # Нет разделителя

        mock_handler = AsyncMock()

        # Должен обработать ошибку
        result = await middleware(mock_handler, mock_callback, {})
        assert result is None

    @pytest.mark.asyncio
    async def test_csrf_no_message(self):
        """Тест CSRF без сообщения"""
        middleware = CSRFMiddleware()

        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "test_nonce:test_data"
        mock_callback.message = None  # Нет сообщения

        mock_handler = AsyncMock()

        # Должен обработать ошибку
        result = await middleware(mock_handler, mock_callback, {})
        assert result is None

    @pytest.mark.asyncio
    async def test_csrf_empty_nonce(self):
        """Тест CSRF с пустым nonce"""
        middleware = CSRFMiddleware()

        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = ":test_data"  # Пустой nonce

        mock_handler = AsyncMock()

        # Должен обработать ошибку
        result = await middleware(mock_handler, mock_callback, {})
        assert result is None


class TestPasswordHashingEdgeCases:
    """Тесты edge cases для хеширования паролей"""

    def test_password_hashing_empty_password(self):
        """Тест хеширования пустого пароля"""
        empty_password = ""

        # Должен обработать пустой пароль
        hashed = hash_pwd(empty_password)
        assert hashed != empty_password
        assert check_pwd(empty_password, hashed) is True

    def test_password_hashing_very_long_password(self):
        """Тест хеширования очень длинного пароля"""
        long_password = "a" * 1000

        # Должен обработать длинный пароль
        hashed = hash_pwd(long_password)
        assert hashed != long_password
        assert check_pwd(long_password, hashed) is True

    def test_password_hashing_special_characters(self):
        """Тест хеширования пароля со специальными символами"""
        special_password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

        # Должен обработать специальные символы
        hashed = hash_pwd(special_password)
        assert hashed != special_password
        assert check_pwd(special_password, hashed) is True

    def test_password_hashing_unicode(self):
        """Тест хеширования пароля с Unicode символами"""
        unicode_password = "пароль123🚀🌟"

        # Должен обработать Unicode символы
        hashed = hash_pwd(unicode_password)
        assert hashed != unicode_password
        assert check_pwd(unicode_password, hashed) is True

    def test_password_verification_invalid_hash(self):
        """Тест проверки пароля с неверным хешем"""
        password = "test_password"
        invalid_hash = "invalid_hash_format"

        # Должен вернуть False для неверного хеша
        assert check_pwd(password, invalid_hash) is False


class TestCSRFTokenEdgeCases:
    """Тесты edge cases для CSRF токенов"""

    @pytest.mark.asyncio
    async def test_issue_nonce_edge_cases(self):
        """Тест создания nonce в edge cases"""
        mock_storage = AsyncMock()

        # Тест с нулевыми ID
        nonce = await issue_nonce(mock_storage, 0, 0)
        assert isinstance(nonce, str)
        assert len(nonce) > 0

        # Тест с отрицательными ID
        nonce = await issue_nonce(mock_storage, -1, -1)
        assert isinstance(nonce, str)
        assert len(nonce) > 0

    @pytest.mark.asyncio
    async def test_check_nonce_edge_cases(self):
        """Тест проверки nonce в edge cases"""
        mock_storage = AsyncMock()
        mock_storage.get_data.return_value = {"csrf": "test_nonce"}

        # Тест с пустым nonce
        is_valid = await check_nonce(mock_storage, 12345, 67890, "")
        assert is_valid is False

        # Тест с None nonce
        is_valid = await check_nonce(mock_storage, 12345, 67890, None)
        assert is_valid is False

        # Тест с неверным nonce
        is_valid = await check_nonce(mock_storage, 12345, 67890, "wrong_nonce")
        assert is_valid is False

    def test_escape_html_edge_cases(self):
        """Тест экранирования HTML в edge cases"""
        # Пустая строка
        assert escape_html("") == ""

        # Строка без HTML
        assert escape_html("plain text") == "plain text"

        # Строка с HTML тегами
        html_text = "<script>alert('xss')</script>"
        escaped = escape_html(html_text)
        assert "<" not in escaped
        assert ">" not in escaped

        # Строка с кавычками
        quote_text = 'He said "Hello"'
        escaped = escape_html(quote_text)
        assert '"' not in escaped

        # Строка с амперсандом
        amp_text = "AT&T & Co."
        escaped = escape_html(amp_text)
        assert "&" not in escaped


class TestUserRepositoryEdgeCases:
    """Тесты edge cases для репозитория пользователей"""

    @pytest.mark.asyncio
    async def test_get_user_edge_cases(self):
        """Тест получения пользователя в edge cases"""
        # Тест с нулевым ID
        user = await get_user(0)
        assert user.tg_id == 0
        assert user.role == "student"

        # Тест с отрицательным ID
        user = await get_user(-1)
        assert user.tg_id == -1
        assert user.role == "student"

        # Тест с очень большим ID
        large_id = 999999999999999
        user = await get_user(large_id)
        assert user.tg_id == large_id
        assert user.role == "student"

    @pytest.mark.asyncio
    async def test_update_user_intro_edge_cases(self):
        """Тест обновления статуса онбординга в edge cases"""
        # Тест с нулевым ID
        await update_user_intro(0, True)
        user = await get_user(0)
        assert user.seen_intro is True

        # Тест с отрицательным ID
        await update_user_intro(-1, False)
        user = await get_user(-1)
        assert user.seen_intro is False


class TestLimiterEdgeCases:
    """Тесты edge cases для rate limiter"""

    @pytest.mark.asyncio
    async def test_hit_edge_cases(self):
        """Тест rate limiter в edge cases"""
        # Тест с пустым ключом
        result = await hit("", 10, 60)
        assert isinstance(result, LimitResult)

        # Тест с нулевым лимитом
        result = await hit("test_key", 0, 60)
        assert isinstance(result, LimitResult)
        assert result.allowed is False

        # Тест с нулевым окном
        result = await hit("test_key", 10, 0)
        assert isinstance(result, LimitResult)

        # Тест с отрицательными значениями
        result = await hit("test_key", -1, -1)
        assert isinstance(result, LimitResult)

    @pytest.mark.asyncio
    async def test_hit_concurrent_access(self):
        """Тест rate limiter при одновременном доступе"""

        # Создаем несколько одновременных запросов
        async def make_hit():
            return await hit("concurrent_key", 5, 60)

        tasks = [make_hit() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем, что все запросы обработаны
        assert len(results) == 10
        assert all(isinstance(r, LimitResult) for r in results)


class TestConfigurationEdgeCases:
    """Тесты edge cases для конфигурации"""

    def test_settings_edge_cases(self):
        """Тест настроек в edge cases"""
        from app.config import Settings

        # Тест с пустыми значениями
        with pytest.raises(ValueError):
            Settings(TELEGRAM_TOKEN="")

        # Тест с очень коротким паролем
        with pytest.raises(ValueError):
            Settings(DB_PASS="123")

        # Тест с недопустимым портом
        with pytest.raises(ValueError):
            Settings(DB_PORT=0)

        # Тест с недопустимыми днями хранения
        with pytest.raises(ValueError):
            Settings(KEEP_DAYS=0)


class TestErrorHandlingEdgeCases:
    """Тесты edge cases для обработки ошибок"""

    @pytest.mark.asyncio
    async def test_middleware_error_edge_cases(self):
        """Тест обработки ошибок в middleware в edge cases"""
        middleware = RateLimitMiddleware(limit=10, window=60)

        # Тест с сообщением без from_user
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = None

        mock_handler = AsyncMock()

        # Должен обработать корректно
        result = await middleware(mock_handler, mock_message, {})
        assert result is not None

        # Тест с handler, который выбрасывает исключение
        mock_handler.side_effect = Exception("Handler error")

        with pytest.raises(Exception):
            await middleware(mock_handler, mock_message, {})

    @pytest.mark.asyncio
    async def test_csrf_error_edge_cases(self):
        """Тест обработки ошибок в CSRF middleware в edge cases"""
        middleware = CSRFMiddleware()

        # Тест с callback без данных
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = None

        mock_handler = AsyncMock()

        # Должен обработать корректно
        result = await middleware(mock_handler, mock_callback, {})
        assert result is None

        # Тест с callback без сообщения
        mock_callback.data = "test_nonce:test_data"
        mock_callback.message = None

        result = await middleware(mock_handler, mock_callback, {})
        assert result is None


@pytest.fixture
def mock_storage():
    """Фикстура для мока storage"""
    return AsyncMock()


@pytest.fixture
def mock_handler():
    """Фикстура для мока handler"""
    return AsyncMock()


@pytest.fixture
def mock_message():
    """Фикстура для мока сообщения"""
    message = AsyncMock(spec=Message)
    message.from_user = AsyncMock()
    message.from_user.id = 12345
    return message


@pytest.fixture
def mock_callback():
    """Фикстура для мока callback"""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "test_nonce:test_data"
    callback.message = AsyncMock()
    callback.message.chat.id = 12345
    callback.from_user.id = 67890
    return callback
