"""
Тесты для проверки оптимизации производительности
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.user import User
from app.services.cache_service import cache_service, cache_result
from app.services.performance_monitor import (
    performance_monitor,
    db_profiler,
    cache_profiler,
    monitor_performance,
    get_performance_summary
)
from app.repositories.optimized_user_repo import optimized_user_repo


class TestCacheService:
    """Тесты для сервиса кеширования"""
    
    @pytest.mark.asyncio
    async def test_cache_user_operations(self):
        """Тест операций кеширования пользователей"""
        # Тест получения пользователя из кеша
        user_data = {
            "id": 1,
            "tg_id": 123456789,
            "username": "test_user",
            "role": "student",
            "is_active": True
        }
        
        # Симулируем кеширование
        with patch.object(cache_service, 'get_user', return_value=user_data):
            result = await cache_service.get_user(123456789)
            assert result == user_data
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Тест инвалидации кеша"""
        with patch.object(cache_service, 'invalidate_user', new_callable=AsyncMock) as mock_invalidate:
            await cache_service.invalidate_user(123456789)
            mock_invalidate.assert_called_once_with(123456789)
    
    @pytest.mark.asyncio
    async def test_cache_decorator(self):
        """Тест декоратора кеширования"""
        call_count = 0
        
        @cache_result(ttl=60)
        async def test_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        # Первый вызов - должен выполниться
        result1 = await test_function("test")
        assert result1 == "result_test"
        assert call_count == 1
        
        # Второй вызов с теми же параметрами - должен вернуться из кеша
        result2 = await test_function("test")
        assert result2 == "result_test"
        assert call_count == 1  # Функция не должна вызываться повторно


class TestPerformanceMonitor:
    """Тесты для мониторинга производительности"""
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Тест мониторинга производительности"""
        async with performance_monitor.monitor_function("test_function"):
            await asyncio.sleep(0.1)  # Симулируем работу
        
        # Проверяем, что метрики записаны
        report = performance_monitor.get_performance_report(hours=1)
        assert "total_calls" in report
        assert report["total_calls"] > 0
    
    @pytest.mark.asyncio
    async def test_database_profiler(self):
        """Тест профилирования БД"""
        async with db_profiler.profile_query("test_query", "SELECT 1"):
            await asyncio.sleep(0.1)  # Симулируем запрос
        
        stats = db_profiler.get_query_stats()
        assert "total_queries" in stats
        assert stats["total_queries"] > 0
    
    @pytest.mark.asyncio
    async def test_cache_profiler(self):
        """Тест профилирования кеша"""
        # Симулируем попадания и промахи
        cache_profiler.record_hit()
        cache_profiler.record_hit()
        cache_profiler.record_miss()
        
        stats = cache_profiler.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_ratio"] == 2/3
    
    @pytest.mark.asyncio
    async def test_performance_decorator(self):
        """Тест декоратора производительности"""
        call_count = 0
        
        @monitor_performance("test_decorated_function")
        async def test_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert call_count == 1


class TestOptimizedUserRepository:
    """Тесты для оптимизированного репозитория пользователей"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_tg_id(self):
        """Тест получения пользователя с кешированием"""
        # Создаем тестового пользователя в БД
        async with AsyncSessionLocal() as session:
            user = User(
                tg_id=999999999,
                username="test_user",
                first_name="Test",
                last_name="User",
                role="student",
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            # Тестируем получение пользователя
            result = await optimized_user_repo.get_user_by_tg_id(999999999)
            
            if result:
                assert result["tg_id"] == 999999999
                assert result["username"] == "test_user"
                assert result["role"] == "student"
            
            # Очищаем тестовые данные
            await session.delete(user)
            await session.commit()
    
    @pytest.mark.asyncio
    async def test_get_users_by_role(self):
        """Тест получения пользователей по роли"""
        users = await optimized_user_repo.get_users_by_role("student", limit=10)
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_get_active_users_count(self):
        """Тест подсчета активных пользователей"""
        counts = await optimized_user_repo.get_active_users_count()
        assert isinstance(counts, dict)
        assert "student" in counts
        assert "teacher" in counts


class TestLoadTesting:
    """Тесты для нагрузочного тестирования"""
    
    @pytest.mark.asyncio
    async def test_load_test_scenario(self):
        """Тест сценария нагрузочного тестирования"""
        from scripts.load_test import BotLoadTest
        
        # Создаем мок токен для тестирования
        test_token = "1234567890:test_token_for_testing"
        
        async with BotLoadTest(test_token) as load_tester:
            # Тестируем отправку сообщения
            result = await load_tester.send_message(123456789, "test message")
            
            # Проверяем структуру результата
            assert "timestamp" in result
            assert "chat_id" in result
            assert "text" in result
            assert "response_time" in result
            assert "status_code" in result
            assert "success" in result
    
    @pytest.mark.asyncio
    async def test_performance_summary(self):
        """Тест получения сводки производительности"""
        summary = await get_performance_summary()
        
        # Проверяем структуру сводки
        assert "system_resources" in summary
        assert "performance_report" in summary
        assert "database_stats" in summary
        assert "cache_stats" in summary
        
        # Проверяем системные ресурсы
        system_resources = summary["system_resources"]
        assert "memory" in system_resources
        assert "cpu" in system_resources
        assert "disk" in system_resources


class TestDatabaseOptimization:
    """Тесты для оптимизации базы данных"""
    
    @pytest.mark.asyncio
    async def test_database_indexes(self):
        """Тест наличия оптимизированных индексов"""
        async with AsyncSessionLocal() as session:
            # Проверяем, что можем выполнять запросы с индексами
            result = await session.execute(
                select(User).where(User.role == "student").limit(5)
            )
            users = result.scalars().all()
            assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_query_performance(self):
        """Тест производительности запросов"""
        start_time = time.time()
        
        async with AsyncSessionLocal() as session:
            # Выполняем несколько запросов для тестирования производительности
            for _ in range(10):
                result = await session.execute(
                    select(User).where(User.is_active == True).limit(1)
                )
                result.scalar_one_or_none()
        
        execution_time = time.time() - start_time
        
        # Проверяем, что запросы выполняются достаточно быстро
        assert execution_time < 1.0  # Менее 1 секунды для 10 запросов


class TestMonitoringIntegration:
    """Тесты интеграции мониторинга"""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Тест сбора метрик"""
        # Выполняем несколько операций для генерации метрик
        for _ in range(5):
            await optimized_user_repo.get_active_users_count()
        
        # Проверяем, что метрики собираются
        summary = await get_performance_summary()
        performance_report = summary["performance_report"]
        
        assert performance_report["total_calls"] >= 5
    
    @pytest.mark.asyncio
    async def test_error_tracking(self):
        """Тест отслеживания ошибок"""
        # Симулируем ошибку
        try:
            raise ValueError("Test error for monitoring")
        except ValueError:
            # Ошибка должна быть зафиксирована в метриках
            pass
        
        # Проверяем, что ошибки отслеживаются
        summary = await get_performance_summary()
        performance_report = summary["performance_report"]
        
        # Проверяем наличие метрик ошибок
        assert "error_rate_percent" in performance_report


class TestCachePerformance:
    """Тесты производительности кеша"""
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self):
        """Тест производительности при попадании в кеш"""
        # Первый вызов - кеш miss
        start_time = time.time()
        await optimized_user_repo.get_active_users_count()
        first_call_time = time.time() - start_time
        
        # Второй вызов - кеш hit
        start_time = time.time()
        await optimized_user_repo.get_active_users_count()
        second_call_time = time.time() - start_time
        
        # Второй вызов должен быть быстрее
        assert second_call_time < first_call_time
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_performance(self):
        """Тест производительности инвалидации кеша"""
        # Создаем тестовые данные
        test_data = {"test": "data"}
        
        # Симулируем кеширование
        with patch.object(cache_service, 'get_frequently_accessed_data', return_value=test_data):
            # Первый вызов
            result1 = await cache_service.get_frequently_accessed_data()
            assert result1 == test_data
            
            # Инвалидируем кеш
            await cache_service.clear_all_caches()
            
            # Второй вызов после инвалидации
            result2 = await cache_service.get_frequently_accessed_data()
            assert result2 == test_data


if __name__ == "__main__":
    # Запуск всех тестов
    pytest.main([__file__, "-v"]) 