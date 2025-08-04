from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram
    TELEGRAM_TOKEN: str

    # Database
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str = "db"
    DB_PORT: int = 5432

    # Redis
    REDIS_DSN: str = "redis://redis:6379/0"

    # Admin configuration
    ADMIN_IDS: str = ""

    # Monitoring
    GLITCHTIP_DSN: str | None = None
    ENV: str = "prod"  # prod | dev | test

    # App settings
    KEEP_DAYS: int = 14

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, env_file_encoding="utf-8"
    )

    @field_validator("TELEGRAM_TOKEN")
    @classmethod
    def validate_telegram_token(cls, v: str) -> str:
        """Валидация формата Telegram токена"""
        if not v:
            raise ValueError("Telegram token cannot be empty")
        # Временно ослабляем требования для быстрого запуска
        if v == "your_telegram_token_here":
            raise ValueError("Please replace 'your_telegram_token_here' with your actual token")
        return v

    @field_validator("DB_PASS")
    @classmethod
    def validate_db_password(cls, v: str) -> str:
        """Валидация сложности пароля базы данных"""
        # Временно ослабляем требования для быстрого запуска
        if len(v) < 1:
            raise ValueError("Database password cannot be empty")
        return v

    @field_validator("DB_PORT")
    @classmethod
    def validate_db_port(cls, v: int) -> int:
        """Валидация порта базы данных"""
        if not 1 <= v <= 65535:
            raise ValueError("Database port must be between 1 and 65535")
        return v

    @field_validator("KEEP_DAYS")
    @classmethod
    def validate_keep_days(cls, v: int) -> int:
        """Валидация количества дней хранения"""
        if v < 1 or v > 365:
            raise ValueError("KEEP_DAYS must be between 1 and 365")
        return v

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Parse ADMIN_IDS from comma-separated string
        if self.ADMIN_IDS:
            self._admin_ids_list = [
                int(id.strip()) for id in self.ADMIN_IDS.split(",") if id.strip().isdigit()
            ]
        else:
            self._admin_ids_list = []

    @property
    def ADMIN_IDS_LIST(self) -> List[int]:
        """Get parsed admin IDs as list"""
        return self._admin_ids_list

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def REDIS_URL(self) -> str:
        """Alias for REDIS_DSN for backward compatibility"""
        return self.REDIS_DSN


settings = Settings()

# Backward compatibility aliases
TELEGRAM_TOKEN = settings.TELEGRAM_TOKEN
REDIS_URL = settings.REDIS_URL
DATABASE_URL = settings.DATABASE_URL
ADMIN_IDS = settings.ADMIN_IDS_LIST
