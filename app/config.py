from typing import List

from pydantic import validator
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

    @validator("TELEGRAM_TOKEN")
    def validate_telegram_token(cls, v):
        """Валидация формата Telegram токена"""
        if not v or ":" not in v:
            raise ValueError("Invalid Telegram token format")
        parts = v.split(":")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1]:
            raise ValueError("Invalid Telegram token format")
        return v

    @validator("DB_PASS")
    def validate_db_password(cls, v):
        """Валидация сложности пароля базы данных"""
        if len(v) < 8:
            raise ValueError("Database password must be at least 8 characters long")
        return v

    @validator("DB_PORT")
    def validate_db_port(cls, v):
        """Валидация порта базы данных"""
        if not 1 <= v <= 65535:
            raise ValueError("Database port must be between 1 and 65535")
        return v

    @validator("KEEP_DAYS")
    def validate_keep_days(cls, v):
        """Валидация количества дней хранения"""
        if v < 1 or v > 365:
            raise ValueError("KEEP_DAYS must be between 1 and 365")
        return v

    def __init__(self, **kwargs) -> None:
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
