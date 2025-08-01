"""
Тесты производительности для School_bot
Проверяют эффективность и скорость работы системы
"""

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from app.repositories.user_repo import get_user, update_user_intro
from app.services.limiter import LimitResult, hit
from app.utils.csrf import check_nonce, issue_nonce
from app.utils.hash import check_pwd, hash_pwd


class TestPerformanceLimiter:
    """Тесты производительности rate limiter"""

    @pytest.mark.asyncio
    async def test_limiter_performance_high_load(self):
        """Тест производительности limiter при высокой нагрузке"""
        # Тестируем 1000 запросов подряд
        start_time = time.time()

        tasks = []
        for i in range(1000):
            task = hit(f"perf_key_{i}", 100, 60)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Проверяем, что все запросы обработаны
        assert len(results) == 1000
        assert all(isinstance(r, LimitResult) for r in results)

        # Проверяем время выполнения (должно быть менее 5 секунд)
        execution_time = end_time - start_time
        assert execution_time < 5.0

        print(f"Обработано 1000 запросов за {execution_time:.2f} секунд")

    @pytest.mark.asyncio
    async def test_limiter_concurrent_performance(self):
        """Тест производительности limiter при одновременных запросах"""
        # Создаем 100 одновременных запросов
        start_time = time.time()

        async def make_concurrent_requests():
            tasks = []
            for i in range(100):
                task = hit(f"concurrent_key_{i}", 50, 60)
                tasks.append(task)
            return await asyncio.gather(*tasks)

        results = await make_concurrent_requests()
        end_time = time.time()

        # Проверяем результаты
        assert len(results) == 100
        assert all(isinstance(r, LimitResult) for r in results)

        # Проверяем время выполнения
        execution_time = end_time - start_time
        assert execution_time < 2.0

        print(f"Обработано 100 одновременных запросов за {execution_time:.2f} секунд")

    @pytest.mark.asyncio
    async def test_limiter_memory_usage(self):
        """Тест использования памяти limiter"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Выполняем множество запросов
        for i in range(1000):
            await hit(f"memory_key_{i}", 10, 60)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Проверяем, что увеличение памяти не превышает 50MB
        assert memory_increase < 50.0

        print(f"Увеличение использования памяти: {memory_increase:.2f} MB")


class TestPerformanceHashing:
    """Тесты производительности хеширования паролей"""

    def test_password_hashing_performance(self):
        """Тест производительности хеширования паролей"""
        passwords = [
            "short",
            "medium_password_123",
            "very_long_password_with_many_characters_and_numbers_123456789",
            "unicode_password_🚀🌟✨",
            "special_chars_!@#$%^&*()_+-=[]{}|;':\",./<>?",
        ]

        start_time = time.time()

        hashes = []
        for password in passwords:
            hashed = hash_pwd(password)
            hashes.append(hashed)

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем, что все хеши созданы
        assert len(hashes) == len(passwords)
        assert all(len(h) > 0 for h in hashes)

        # Проверяем время выполнения (должно быть менее 1 секунды)
        assert execution_time < 1.0

        print(f"Создано {len(hashes)} хешей за {execution_time:.3f} секунд")

    def test_password_verification_performance(self):
        """Тест производительности проверки паролей"""
        test_password = "test_password_123"
        hashed = hash_pwd(test_password)

        start_time = time.time()

        # Выполняем 1000 проверок
        for _ in range(1000):
            result = check_pwd(test_password, hashed)
            assert result is True

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем время выполнения
        assert execution_time < 2.0

        print(f"Выполнено 1000 проверок паролей за {execution_time:.3f} секунд")

    def test_hashing_different_password_lengths(self):
        """Тест производительности хеширования паролей разной длины"""
        password_lengths = [10, 50, 100, 500, 1000]

        results = {}
        for length in password_lengths:
            password = "a" * length
            start_time = time.time()

            hashed = hash_pwd(password)
            result = check_pwd(password, hashed)

            end_time = time.time()
            execution_time = end_time - start_time

            results[length] = execution_time
            assert result is True

        # Проверяем, что время хеширования не растет экспоненциально
        for length in password_lengths[1:]:
            assert results[length] < results[length - 1] * 2

        print("Время хеширования для разных длин паролей:")
        for length, exec_time in results.items():
            print(f"  {length} символов: {exec_time:.4f} сек")


class TestPerformanceCSRF:
    """Тесты производительности CSRF токенов"""

    @pytest.mark.asyncio
    async def test_csrf_token_generation_performance(self):
        """Тест производительности генерации CSRF токенов"""
        mock_storage = AsyncMock()

        start_time = time.time()

        # Генерируем 1000 токенов
        tokens = []
        for i in range(1000):
            token = await issue_nonce(mock_storage, i, i * 2)
            tokens.append(token)

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем результаты
        assert len(tokens) == 1000
        assert all(len(t) > 0 for t in tokens)
        assert len(set(tokens)) == 1000  # Все токены уникальны

        # Проверяем время выполнения
        assert execution_time < 1.0

        print(f"Создано 1000 CSRF токенов за {execution_time:.3f} секунд")

    @pytest.mark.asyncio
    async def test_csrf_token_validation_performance(self):
        """Тест производительности валидации CSRF токенов"""
        mock_storage = AsyncMock()
        mock_storage.get_data.return_value = {"csrf": "test_nonce"}

        start_time = time.time()

        # Выполняем 1000 проверок
        for _ in range(1000):
            result = await check_nonce(mock_storage, 12345, 67890, "test_nonce")
            assert result is True

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем время выполнения
        assert execution_time < 1.0

        print(f"Выполнено 1000 проверок CSRF токенов за {execution_time:.3f} секунд")


class TestPerformanceUserRepository:
    """Тесты производительности репозитория пользователей"""

    @pytest.mark.asyncio
    async def test_user_creation_performance(self):
        """Тест производительности создания пользователей"""
        start_time = time.time()

        # Создаем 100 пользователей
        users = []
        for i in range(100):
            user = await get_user(1000000 + i)
            users.append(user)

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем результаты
        assert len(users) == 100
        assert all(user.tg_id == 1000000 + i for i, user in enumerate(users))

        # Проверяем время выполнения
        assert execution_time < 10.0  # Более длительное время из-за БД

        print(f"Создано 100 пользователей за {execution_time:.3f} секунд")

    @pytest.mark.asyncio
    async def test_user_update_performance(self):
        """Тест производительности обновления пользователей"""
        # Сначала создаем пользователей
        user_ids = list(range(2000000, 2000100))
        for user_id in user_ids:
            await get_user(user_id)

        start_time = time.time()

        # Обновляем всех пользователей
        for user_id in user_ids:
            await update_user_intro(user_id, True)

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем время выполнения
        assert execution_time < 15.0  # Более длительное время из-за БД

        print(f"Обновлено 100 пользователей за {execution_time:.3f} секунд")


class TestPerformanceLoadTesting:
    """Тесты нагрузочного тестирования"""

    @pytest.mark.asyncio
    async def test_simultaneous_operations(self):
        """Тест одновременных операций"""
        start_time = time.time()

        # Создаем задачи для разных операций
        tasks = []

        # Rate limiting операции
        for i in range(100):
            task = hit(f"load_key_{i}", 50, 60)
            tasks.append(task)

        # Хеширование паролей
        for i in range(50):
            task = asyncio.to_thread(hash_pwd, f"password_{i}")
            tasks.append(task)

        # CSRF операции
        mock_storage = AsyncMock()
        for i in range(50):
            task = issue_nonce(mock_storage, i, i * 2)
            tasks.append(task)

        # Выполняем все задачи одновременно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем результаты
        assert len(results) == 200
        assert all(not isinstance(r, Exception) for r in results)

        # Проверяем время выполнения
        assert execution_time < 5.0

        print(f"Выполнено 200 одновременных операций за {execution_time:.3f} секунд")

    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Тест эффективности использования памяти"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Выполняем множество операций
        operations = []

        # Rate limiting
        for i in range(500):
            operations.append(hit(f"memory_test_{i}", 10, 60))

        # Хеширование
        for i in range(500):
            operations.append(asyncio.to_thread(hash_pwd, f"pwd_{i}"))

        # CSRF
        mock_storage = AsyncMock()
        for i in range(500):
            operations.append(issue_nonce(mock_storage, i, i))

        # Выполняем все операции
        await asyncio.gather(*operations, return_exceptions=True)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Проверяем, что увеличение памяти разумное
        assert memory_increase < 100.0  # Не более 100MB

        print(f"Увеличение памяти после 1500 операций: {memory_increase:.2f} MB")


class TestPerformanceBenchmarks:
    """Бенчмарки производительности"""

    @pytest.mark.asyncio
    async def test_rate_limiter_benchmark(self):
        """Бенчмарк rate limiter"""
        print("\n=== Бенчмарк Rate Limiter ===")

        # Тест 1: Одиночные запросы
        start_time = time.time()
        for i in range(1000):
            await hit(f"benchmark_single_{i}", 100, 60)
        single_time = time.time() - start_time

        # Тест 2: Одновременные запросы
        start_time = time.time()
        tasks = [hit(f"benchmark_concurrent_{i}", 100, 60) for i in range(1000)]
        await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time

        print(f"Одиночные запросы (1000): {single_time:.3f} сек")
        print(f"Одновременные запросы (1000): {concurrent_time:.3f} сек")
        print(f"Ускорение: {single_time / concurrent_time:.2f}x")

    def test_password_hashing_benchmark(self):
        """Бенчмарк хеширования паролей"""
        print("\n=== Бенчмарк Password Hashing ===")

        passwords = [
            "short",
            "medium_password_123",
            "very_long_password_with_many_characters_and_numbers_123456789",
            "unicode_password_🚀🌟✨",
            "special_chars_!@#$%^&*()_+-=[]{}|;':\",./<>?",
        ]

        for password in passwords:
            start_time = time.time()
            hashed = hash_pwd(password)
            hash_time = time.time() - start_time

            start_time = time.time()
            result = check_pwd(password, hashed)
            verify_time = time.time() - start_time

            print(f"Пароль ({len(password)} символов):")
            print(f"  Хеширование: {hash_time:.4f} сек")
            print(f"  Проверка: {verify_time:.4f} сек")
            print(f"  Результат: {result}")

    @pytest.mark.asyncio
    async def test_csrf_benchmark(self):
        """Бенчмарк CSRF операций"""
        print("\n=== Бенчмарк CSRF ===")

        mock_storage = AsyncMock()

        # Тест генерации токенов
        start_time = time.time()
        tokens = []
        for i in range(1000):
            token = await issue_nonce(mock_storage, i, i * 2)
            tokens.append(token)
        generation_time = time.time() - start_time

        # Тест валидации токенов
        mock_storage.get_data.return_value = {"csrf": "test_nonce"}
        start_time = time.time()
        for _ in range(1000):
            await check_nonce(mock_storage, 12345, 67890, "test_nonce")
        validation_time = time.time() - start_time

        print(f"Генерация токенов (1000): {generation_time:.3f} сек")
        print(f"Валидация токенов (1000): {validation_time:.3f} сек")
        print(f"Уникальных токенов: {len(set(tokens))}")


@pytest.fixture
def performance_config():
    """Конфигурация для тестов производительности"""
    return {
        "rate_limit_requests": 1000,
        "password_iterations": 1000,
        "csrf_iterations": 1000,
        "user_operations": 100,
        "timeout_seconds": 30,
    }
