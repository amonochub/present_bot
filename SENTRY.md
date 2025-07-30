# 🐛 Sentry Self-Hosted - Мониторинг ошибок

## Обзор

Sentry предоставляет полноценный журнал traceback-ов и метрик прямо в веб-интерфейсе. Все данные хранятся на школьном сервере без передачи сторонним SaaS.

## 🚀 Быстрый старт

### 1. Запуск Sentry

```bash
# Запуск всех сервисов
docker-compose up -d

# Инициализация Sentry (только первый раз)
./scripts/init_sentry.sh
```

### 2. Настройка проекта

1. Откройте http://localhost:9000
2. Создайте аккаунт администратора
3. Создайте проект "SchoolBot" (Platform: Python)
4. Скопируйте DSN и добавьте в `.env`:

```env
SENTRY_DSN=http://<public_key>@sentry:9000/1
```

### 3. Тестирование

```bash
# Отправьте боту команду
/crash
```

В Sentry появится новая Issue с ZeroDivisionError.

## 🔧 Конфигурация

### Docker Compose

```yaml
sentry:
  image: getsentry/sentry:24.6.0
  environment:
    SENTRY_SECRET_KEY: "CHANGE_ME_32_random_chars_here_12345"
    SENTRY_POSTGRES_HOST: postgres
    SENTRY_DB_NAME: schoolbot
    SENTRY_DB_USER: schoolbot
    SENTRY_DB_PASSWORD: schoolbot
    SENTRY_REDIS_HOST: redis
    SENTRY_REDIS_PORT: 6379
    SENTRY_REDIS_DB: 1
    SENTRY_TSDB: "sentry.tsdb.dummy.DummyTSDB"
  ports:
    - "9000:9000"
```

### Интеграция в код

```python
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        AioHttpIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "development"),
    release="schoolbot@1.0.0",
)
```

## 🛡️ Фильтрация событий

Автоматически фильтруются:
- Ошибки валидации логина
- Rate limit ошибки
- Повторяющиеся исключения

```python
def _should_suppress_event(event, hint):
    exc = hint.get("exc_info", (None, None, None))[1]
    if exc:
        if isinstance(exc, ValueError) and "логин" in str(exc).lower():
            return True
        if "rate" in str(exc).lower() and "limit" in str(exc).lower():
            return True
    return False
```

## 📊 Health Check

Бот предоставляет health check endpoint:

```bash
# Проверка состояния
curl http://localhost:8080/healthz

# Ответ
{
  "status": "healthy",
  "timestamp": 1703123456.789,
  "database": "connected",
  "redis": "connected"
}
```

## 🔔 Алерты

### Настройка уведомлений

1. В Sentry: Settings → Alerts
2. Создайте правило: "No events in 30 min"
3. Добавьте уведомления:
   - Email
   - Telegram (через webhook)
   - Slack (если используется)

### Мониторинг контейнеров

```bash
# Проверка статуса
docker-compose ps

# Логи Sentry
docker-compose logs sentry

# Логи бота
docker-compose logs bot
```

## 📈 Метрики

Sentry автоматически собирает:
- Количество ошибок по типам
- Время отклика запросов
- Производительность SQL запросов
- Использование памяти

## 🧪 Тестирование

### Тестовая команда

```python
@dp.message(Command("crash"))
async def crash(msg: Message):
    """Тестовая команда для проверки Sentry"""
    1/0  # ZeroDivisionError
```

### Ручное тестирование

```python
import sentry_sdk

# Отправка ошибки вручную
sentry_sdk.capture_exception(Exception("Test error"))
```

## 🔒 Безопасность

- Все данные хранятся локально
- Нет передачи данных за рубеж
- Доступ только через внутреннюю сеть
- Аутентификация через Sentry

## 📋 Troubleshooting

### Проблема: Sentry не запускается

```bash
# Проверьте логи
docker-compose logs sentry

# Пересоздайте контейнер
docker-compose down
docker-compose up -d
```

### Проблема: Ошибки не отправляются

1. Проверьте SENTRY_DSN в .env
2. Убедитесь, что Sentry доступен
3. Проверьте логи бота

### Проблема: Много спама в Sentry

Настройте фильтры в `_should_suppress_event()` или в веб-интерфейсе Sentry.

## 🚀 Альтернативы

### GlitchTip (лёгкий)

Если Sentry слишком тяжёлый для VPS:

```yaml
glitchtip:
  image: glitchtip/glitchtip-backend:latest
  environment:
    DATABASE_URL: postgresql://schoolbot:schoolbot@postgres:5432/glitchtip
  ports:
    - "8000:8000"
```

## 📚 Дополнительные ресурсы

- [Sentry Documentation](https://docs.sentry.io/)
- [Self-Hosted Sentry](https://develop.sentry.dev/self-hosted/)
- [Python SDK](https://docs.sentry.io/platforms/python/) 