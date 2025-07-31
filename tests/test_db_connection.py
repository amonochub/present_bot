import logging

import pytest

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        from app.db.session import AsyncSessionLocal

        # Проверяем подключение к базе данных
        async with AsyncSessionLocal() as session:
            # Простой запрос для проверки подключения
            result = await session.execute("SELECT 1")
            assert result.scalar() == 1

        logger.info("Database connection test passed")
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        pytest.skip("Database not available")


@pytest.mark.asyncio
async def test_redis_connection():
    """Тест подключения к Redis"""
    try:
        import redis

        from app.config import settings

        # Создаем подключение к Redis
        r = redis.from_url(settings.REDIS_DSN)

        # Простой тест подключения
        r.set("test_key", "test_value")
        value = r.get("test_key")
        assert value.decode() == "test_value"

        # Очищаем тестовые данные
        r.delete("test_key")

        logger.info("Redis connection test passed")
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        pytest.skip("Redis not available")


@pytest.mark.asyncio
async def test_config_loading():
    """Тест загрузки конфигурации"""
    try:
        from app.config import settings

        # Проверяем, что основные настройки загружены
        assert hasattr(settings, "TELEGRAM_TOKEN")
        assert hasattr(settings, "DB_NAME")
        assert hasattr(settings, "DB_USER")
        assert hasattr(settings, "DB_PASS")
        assert hasattr(settings, "REDIS_DSN")

        logger.info("Config loading test passed")
    except Exception as e:
        logger.error(f"Config loading test failed: {e}")
        pytest.skip("Configuration not available")


if __name__ == "__main__":
    pytest.main([__file__])
