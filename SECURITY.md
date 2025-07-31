# 🔒 Документация по безопасности SchoolBot

## Обзор безопасности

SchoolBot реализует многоуровневую систему безопасности для защиты данных пользователей и предотвращения несанкционированного доступа.

## 🔐 Аутентификация и авторизация

### Хеширование паролей
- Используется bcrypt для хеширования паролей
- Автоматическая генерация соли для каждого пароля
- Защита от timing attacks при проверке паролей

```python
from app.utils.hash import hash_pwd, check_pwd

# Хеширование пароля
hashed = hash_pwd("user_password")

# Проверка пароля
is_valid = check_pwd("user_password", hashed)
```

### Ролевая модель доступа
- **teacher**: Учителя - создание заметок, заявки IT, медиа-заявки
- **admin**: Администрация - управление заявками, рассылки
- **director**: Директор - KPI, поручения
- **student**: Ученики - обращения к психологу
- **parent**: Родители - просмотр заданий
- **psych**: Психолог - обработка обращений
- **super**: Демо-режим - доступ ко всем функциям

### Проверка ролей
Все критичные операции проверяют роль пользователя:

```python
async def get_user_role(tg_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == tg_id))
        return user.role if user else None

# Проверка доступа
if user_role not in ["admin", "super"]:
    await call.answer("Доступ запрещен", show_alert=True)
    return
```

## 🛡️ CSRF защита

### Nonce токены
- Генерация уникальных токенов для каждой сессии
- Проверка токенов при каждом callback запросе
- Автоматическое отклонение запросов с неверными токенами

```python
# Генерация токена
nonce = await issue_nonce(storage, chat_id, user_id)

# Проверка токена
is_valid = await check_nonce(storage, chat_id, user_id, nonce)
```

## 🚦 Rate Limiting

### Ограничение запросов
- Лимит: 20 запросов в минуту на пользователя
- Использование Redis для хранения счетчиков
- Автоматическая блокировка при превышении лимита

```python
class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit=20, window=60):
        self.limit = limit
        self.window = window
```

## 📊 Аудит и мониторинг

### Логирование действий
- AuditMiddleware логирует все действия пользователей
- Разные уровни логирования для разных типов действий
- Защита от логирования чувствительных данных

### Sentry интеграция
- Автоматический сбор ошибок
- Фильтрация ложных срабатываний
- Контекстная информация о пользователях

## 🗄️ Безопасность базы данных

### Параметризованные запросы
Все запросы к базе данных используют параметризацию для предотвращения SQL инъекций:

```python
# Безопасно
await s.execute(select(User).where(User.tg_id == user_id))

# Небезопасно (НЕ ИСПОЛЬЗОВАТЬ)
await s.execute(f"SELECT * FROM users WHERE tg_id = {user_id}")
```

### Row Level Security (RLS)
- Настройка RLS для изоляции данных пользователей
- Автоматическая установка контекста пользователя

## 🔍 Валидация входных данных

### Конфигурация
```python
class Settings(BaseSettings):
    @validator('TELEGRAM_TOKEN')
    def validate_telegram_token(cls, v):
        if not v or ':' not in v:
            raise ValueError('Invalid Telegram token format')
        return v

    @validator('DB_PASS')
    def validate_db_password(cls, v):
        if len(v) < 8:
            raise ValueError('Database password must be at least 8 characters long')
        return v
```

### Валидация пользовательского ввода
- Проверка длины текста (максимум 1000 символов для заметок)
- Валидация формата дат
- Санитизация HTML-разметки

## 🚨 Обработка ошибок

### Безопасное логирование
- Не логируются пароли и токены
- Ограничение длины логов
- Маскирование чувствительных данных

### Graceful degradation
- Возврат безопасных сообщений об ошибках
- Не раскрытие внутренней структуры системы
- Fallback значения при ошибках

## 🔧 Рекомендации по развертыванию

### Переменные окружения
```bash
# Обязательные
BOT_TOKEN=your_bot_token_here
DB_PASS=your_secure_password_here

# Рекомендуемые
ENVIRONMENT=production
GLITCHTIP_DSN=your_sentry_dsn
```

### Сетевая безопасность
- Использование HTTPS для webhook
- Ограничение доступа к портам
- Настройка firewall

### Мониторинг
- Регулярная проверка логов
- Мониторинг метрик Prometheus
- Алерты при подозрительной активности

## 🧪 Тестирование безопасности

### Автоматические тесты
```bash
# Запуск тестов безопасности
pytest tests/test_security.py -v
```

### Ручное тестирование
1. Проверка CSRF токенов
2. Тестирование rate limiting
3. Валидация ролевого доступа
4. Проверка SQL инъекций

## 📋 Чек-лист безопасности

- [x] Хеширование паролей (bcrypt)
- [x] CSRF защита (nonce токены)
- [x] Rate limiting
- [x] Ролевая модель доступа
- [x] Параметризованные SQL запросы
- [x] Валидация входных данных
- [x] Аудит действий пользователей
- [x] Безопасное логирование
- [x] Обработка ошибок
- [x] Мониторинг и алерты

## 🆘 Контакты по безопасности

При обнаружении уязвимостей безопасности:
1. НЕ создавайте публичные issues
2. Свяжитесь с командой разработки напрямую
3. Предоставьте детальное описание проблемы
4. Укажите шаги для воспроизведения

## 📚 Дополнительные ресурсы

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Telegram Bot API Security](https://core.telegram.org/bots/api#security-considerations)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/security.html)
