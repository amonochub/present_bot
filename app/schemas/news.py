"""
Pydantic модели для валидации новостей согласно Context7
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class NewsCard(BaseModel):
    """Модель карточки новости с валидацией"""

    title: str = Field(..., min_length=5, max_length=200, description="Заголовок новости")
    date: str = Field(..., description="Дата новости")
    desc: str = Field(..., description="Описание новости")
    url: HttpUrl = Field(..., description="URL новости")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Валидация заголовка"""
        if not v.strip():
            raise ValueError("Заголовок не может быть пустым")
        return v.strip()

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Валидация даты"""
        if not v.strip():
            return "Не указана"
        return v.strip()

    @field_validator("desc")
    @classmethod
    def validate_desc(cls, v: str) -> str:
        """Валидация описания"""
        if not v.strip():
            return "Описание недоступно"
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_url_domain(cls, v: HttpUrl) -> HttpUrl:
        """Валидация домена URL"""
        allowed_domains = ["www.mos.ru", "mos.ru", "dpomos.ru"]
        if not any(domain in str(v) for domain in allowed_domains):
            raise ValueError("URL должен принадлежать разрешенному домену")
        return v


class NewsResponse(BaseModel):
    """Модель ответа с новостями"""

    news: List[NewsCard] = Field(..., description="Список новостей")
    total_count: int = Field(..., ge=0, description="Общее количество новостей")
    cached: bool = Field(default=False, description="Флаг кэширования")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время получения")


class NewsRequest(BaseModel):
    """Модель запроса новостей"""

    limit: int = Field(default=5, ge=1, le=20, description="Лимит новостей")
    force_refresh: bool = Field(default=False, description="Принудительное обновление")


class NewsError(BaseModel):
    """Модель ошибки новостей"""

    error: str = Field(..., description="Описание ошибки")
    code: str = Field(..., description="Код ошибки")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время ошибки")
    details: Optional[str] = Field(None, description="Детали ошибки")


class RateLimitInfo(BaseModel):
    """Модель информации о rate limiting"""

    key: str = Field(..., description="Ключ rate limiting")
    requests_count: int = Field(..., ge=0, description="Количество запросов")
    max_requests: int = Field(..., ge=1, description="Максимальное количество запросов")
    window_seconds: int = Field(..., ge=1, description="Окно времени в секундах")
    can_request: bool = Field(..., description="Можно ли выполнить запрос")


class CacheInfo(BaseModel):
    """Модель информации о кэше"""

    cache_key: str = Field(..., description="Ключ кэша")
    cached_at: datetime = Field(..., description="Время кэширования")
    ttl_seconds: int = Field(..., description="TTL в секундах")
    is_expired: bool = Field(..., description="Истек ли кэш")
    cache_size: int = Field(..., ge=0, description="Размер кэша")
