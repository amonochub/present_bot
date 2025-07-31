import pytest
import os
from unittest.mock import patch
from app.config import Settings, settings

class TestConfigSecurity:
    """Тесты безопасности конфигурации"""
    
    def test_telegram_token_validation(self):
        """Тест валидации формата Telegram токена"""
        # Правильный формат
        valid_token = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
        with patch.dict(os.environ, {'TELEGRAM_TOKEN': valid_token}):
            settings_obj = Settings()
            assert settings_obj.TELEGRAM_TOKEN == valid_token
        
        # Неправильный формат - должен вызвать ошибку
        invalid_tokens = [
            "",  # пустой
            "1234567890",  # без двоеточия
            ":ABCdefGHIjklMNOpqrsTUVwxyz",  # без ID
            "abc:ABCdefGHIjklMNOpqrsTUVwxyz",  # ID не число
            "1234567890:",  # без секрета
        ]
        
        for invalid_token in invalid_tokens:
            with patch.dict(os.environ, {'TELEGRAM_TOKEN': invalid_token}):
                with pytest.raises(ValueError, match="Invalid Telegram token format"):
                    Settings()
    
    def test_database_password_validation(self):
        """Тест валидации сложности пароля БД"""
        # Короткий пароль - должен вызвать ошибку
        short_password = "1234567"  # 7 символов
        with patch.dict(os.environ, {
            'DB_PASS': short_password,
            'DB_NAME': 'test',
            'DB_USER': 'test',
            'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        }):
            with pytest.raises(ValueError, match="Database password must be at least 8 characters long"):
                Settings()
        
        # Длинный пароль - должен пройти
        long_password = "secure_password_123"
        with patch.dict(os.environ, {
            'DB_PASS': long_password,
            'DB_NAME': 'test',
            'DB_USER': 'test',
            'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        }):
            settings_obj = Settings()
            assert settings_obj.DB_PASS == long_password
    
    def test_database_port_validation(self):
        """Тест валидации порта БД"""
        # Неправильные порты
        invalid_ports = [0, 65536, -1, 70000]
        for port in invalid_ports:
            with patch.dict(os.environ, {
                'DB_PORT': str(port),
                'DB_NAME': 'test',
                'DB_USER': 'test',
                'DB_PASS': 'secure_password_123',
                'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
            }):
                with pytest.raises(ValueError, match="Database port must be between 1 and 65535"):
                    Settings()
        
        # Правильные порты
        valid_ports = [1, 5432, 65535]
        for port in valid_ports:
            with patch.dict(os.environ, {
                'DB_PORT': str(port),
                'DB_NAME': 'test',
                'DB_USER': 'test',
                'DB_PASS': 'secure_password_123',
                'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
            }):
                settings_obj = Settings()
                assert settings_obj.DB_PORT == port
    
    def test_keep_days_validation(self):
        """Тест валидации количества дней хранения"""
        # Неправильные значения
        invalid_days = [0, 366, -1, 1000]
        for days in invalid_days:
            with patch.dict(os.environ, {
                'KEEP_DAYS': str(days),
                'DB_NAME': 'test',
                'DB_USER': 'test',
                'DB_PASS': 'secure_password_123',
                'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
            }):
                with pytest.raises(ValueError, match="KEEP_DAYS must be between 1 and 365"):
                    Settings()
        
        # Правильные значения
        valid_days = [1, 14, 365]
        for days in valid_days:
            with patch.dict(os.environ, {
                'KEEP_DAYS': str(days),
                'DB_NAME': 'test',
                'DB_USER': 'test',
                'DB_PASS': 'secure_password_123',
                'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
            }):
                settings_obj = Settings()
                assert settings_obj.KEEP_DAYS == days
    
    def test_admin_ids_parsing(self):
        """Тест парсинга ID администраторов"""
        # Пустая строка
        with patch.dict(os.environ, {
            'ADMIN_IDS': '',
            'DB_NAME': 'test',
            'DB_USER': 'test',
            'DB_PASS': 'secure_password_123',
            'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        }):
            settings_obj = Settings()
            assert settings_obj.ADMIN_IDS_LIST == []
        
        # Один ID
        with patch.dict(os.environ, {
            'ADMIN_IDS': '123456789',
            'DB_NAME': 'test',
            'DB_USER': 'test',
            'DB_PASS': 'secure_password_123',
            'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        }):
            settings_obj = Settings()
            assert settings_obj.ADMIN_IDS_LIST == [123456789]
        
        # Несколько ID
        with patch.dict(os.environ, {
            'ADMIN_IDS': '123456789, 987654321, 555666777',
            'DB_NAME': 'test',
            'DB_USER': 'test',
            'DB_PASS': 'secure_password_123',
            'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        }):
            settings_obj = Settings()
            assert settings_obj.ADMIN_IDS_LIST == [123456789, 987654321, 555666777]
        
        # С невалидными значениями
        with patch.dict(os.environ, {
            'ADMIN_IDS': '123456789, abc, 987654321, def',
            'DB_NAME': 'test',
            'DB_USER': 'test',
            'DB_PASS': 'secure_password_123',
            'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        }):
            settings_obj = Settings()
            assert settings_obj.ADMIN_IDS_LIST == [123456789, 987654321]
    
    def test_database_url_construction(self):
        """Тест построения URL базы данных"""
        with patch.dict(os.environ, {
            'DB_NAME': 'testdb',
            'DB_USER': 'testuser',
            'DB_PASS': 'testpass123',
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        }):
            settings_obj = Settings()
            expected_url = "postgresql+asyncpg://testuser:testpass123@localhost:5432/testdb"
            assert settings_obj.DATABASE_URL == expected_url
    
    def test_redis_url_alias(self):
        """Тест алиаса для Redis URL"""
        with patch.dict(os.environ, {
            'REDIS_DSN': 'redis://localhost:6379/1',
            'DB_NAME': 'test',
            'DB_USER': 'test',
            'DB_PASS': 'secure_password_123',
            'TELEGRAM_TOKEN': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        }):
            settings_obj = Settings()
            assert settings_obj.REDIS_URL == 'redis://localhost:6379/1'
    
    def test_environment_variables_not_in_code(self):
        """Тест, что секреты не захардкожены в коде"""
        # Проверяем, что токен не захардкожен
        assert not hasattr(settings, 'TELEGRAM_TOKEN') or settings.TELEGRAM_TOKEN != 'your_bot_token_here'
        
        # Проверяем, что пароль БД не захардкожен
        assert not hasattr(settings, 'DB_PASS') or settings.DB_PASS != 'your_secure_password_here'
        
        # Проверяем, что DSN не захардкожен
        assert not hasattr(settings, 'GLITCHTIP_DSN') or settings.GLITCHTIP_DSN is None or 'CHANGE_ME' not in str(settings.GLITCHTIP_DSN)

if __name__ == "__main__":
    pytest.main([__file__]) 