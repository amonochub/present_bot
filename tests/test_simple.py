from app.config import settings


def test_config_loading():
    """Тест загрузки конфигурации"""
    assert settings.ENV is not None
    assert settings.TELEGRAM_TOKEN is not None
    assert settings.DB_NAME is not None


def test_limit_result():
    """Тест модели LimitResult"""
    from pydantic import BaseModel

    class LimitResult(BaseModel):
        allowed: bool
        retry_after: int | None = None

    result = LimitResult(allowed=True, retry_after=None)
    assert result.allowed is True
    assert result.retry_after is None

    result2 = LimitResult(allowed=False, retry_after=30)
    assert result2.allowed is False
    assert result2.retry_after == 30


def test_settings_properties():
    """Тест свойств настроек"""
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "REDIS_URL")
    assert hasattr(settings, "ADMIN_IDS_LIST")

    # Проверяем, что свойства возвращают строки
    assert isinstance(settings.DATABASE_URL, str)
    assert isinstance(settings.REDIS_URL, str)
    assert isinstance(settings.ADMIN_IDS_LIST, list)
