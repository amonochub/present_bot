# Руководство по безопасности

## Обзор

Данный документ описывает меры безопасности, реализованные в проекте School Bot, а также рекомендации по их поддержанию и улучшению.

## Управление секретами

### Переменные окружения

Все чувствительные данные хранятся в переменных окружения:

```bash
# Telegram Bot
TELEGRAM_TOKEN=your_bot_token_here

# Database
DB_NAME=schoolbot
DB_USER=schoolbot
DB_PASS=your_secure_password_here

# Redis
REDIS_DSN=redis://redis:6379/0

# Admin IDs
ADMIN_IDS=123456789,987654321

# Monitoring
GLITCHTIP_DSN=http://<public_key>@glitchtip:8000/1
```

### Правила безопасности

1. **Никогда не коммитьте файл `.env`** - он добавлен в `.gitignore`
2. **Используйте сложные пароли** - минимум 8 символов
3. **Регулярно ротируйте токены** - особенно после утечек
4. **Ограничьте доступ к секретам** - только необходимые люди

## Хранение данных

### Хеширование паролей

Пароли хешируются с использованием BCrypt:

```python
from app.utils.hash import hash_pwd, check_pwd

# Хеширование
hashed = hash_pwd("user_password")

# Проверка
is_valid = check_pwd("user_password", hashed)
```

### Защита персональных данных

1. **Минимизация данных** - храним только необходимую информацию
2. **Ролевой доступ** - пользователи видят только свои данные
3. **Логирование доступа** - отслеживаем все операции с данными

## Защита от атак

### XSS (Cross-Site Scripting)

Реализована защита от XSS через экранирование HTML:

```python
from app.utils.csrf import escape_html

# Экранирование пользовательского ввода
safe_text = escape_html(user_input)
```

### CSRF (Cross-Site Request Forgery)

Используются nonce токены для защиты callback'ов:

```python
from app.utils.csrf import issue_nonce, check_nonce

# Создание nonce
nonce = await issue_nonce(storage, chat_id, user_id)

# Проверка nonce
is_valid = await check_nonce(storage, chat_id, user_id, nonce)
```

### Rate Limiting

Ограничение частоты запросов для предотвращения спама:

```python
from app.middlewares.rate_limit import RateLimitMiddleware

# Настройка лимитов
middleware = RateLimitMiddleware(limit=10, window=60)
```

### SQL Injection

Используется ORM (SQLAlchemy) с параметризованными запросами:

```python
# Безопасно
user = await session.execute(
    select(User).where(User.tg_id == user_id)
)

# НЕ делайте так
user = await session.execute(
    f"SELECT * FROM users WHERE tg_id = {user_id}"
)
```

## Ролевая модель

### Роли пользователей

- **student** - ученик
- **teacher** - учитель
- **admin** - администратор
- **director** - директор
- **psych** - психолог
- **parent** - родитель
- **super** - демо-режим (только для тестирования)

### Контроль доступа

```python
# Проверка роли
if user.role == "teacher":
    # Доступ к функциям учителя
    pass
elif user.role == "admin":
    # Доступ к функциям администратора
    pass
```

## Мониторинг безопасности

### Логирование

Все важные события логируются:

- Аутентификация пользователей
- Доступ к чувствительным данным
- Ошибки безопасности
- Попытки обхода ограничений

### Алерты

Настроены уведомления о:

- Неудачных попытках входа
- Подозрительной активности
- Ошибках системы
- Превышении лимитов

## Тестирование безопасности

### Автоматические тесты

Запуск тестов безопасности:

```bash
# Все тесты безопасности
pytest tests/test_security.py tests/test_config_security.py tests/test_xss_protection.py

# С покрытием
pytest tests/test_security.py --cov=app --cov-report=html
```

### Ручное тестирование

1. **Проверка валидации ввода**
2. **Тестирование ролевого доступа**
3. **Проверка защиты от XSS**
4. **Тестирование rate limiting**

## Рекомендации по развертыванию

### Продакшн

1. **Используйте HTTPS** для всех соединений
2. **Настройте firewall** для ограничения доступа
3. **Регулярно обновляйте зависимости**
4. **Мониторьте логи** на предмет подозрительной активности
5. **Создавайте резервные копии** данных

### Docker

```bash
# Безопасный запуск
docker-compose up -d

# Проверка логов
docker-compose logs -f bot
```

## Инциденты безопасности

### Процедура реагирования

1. **Немедленно изолируйте** затронутые системы
2. **Соберите доказательства** (логи, дампы)
3. **Оцените масштаб** ущерба
4. **Исправьте уязвимости**
5. **Уведомите затронутых** пользователей
6. **Документируйте инцидент**

### Контакты

- **Ответственный за безопасность**: [email]
- **Техническая поддержка**: [email]
- **Экстренные случаи**: [phone]

## Обновления безопасности

### Регулярные проверки

- [ ] Еженедельно: обновление зависимостей
- [ ] Ежемесячно: аудит безопасности
- [ ] Ежеквартально: penetration testing
- [ ] Ежегодно: полный security review

### Чек-лист безопасности

- [ ] Все секреты в переменных окружения
- [ ] Пароли хешируются BCrypt
- [ ] Включен rate limiting
- [ ] Настроено логирование
- [ ] Тесты безопасности проходят
- [ ] Мониторинг активен
- [ ] Резервные копии создаются
- [ ] HTTPS используется везде
- [ ] Firewall настроен
- [ ] Обновления применяются регулярно

## Дополнительные ресурсы

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Telegram Bot API Security](https://core.telegram.org/bots/api#security-considerations)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
- [Docker Security](https://docs.docker.com/engine/security/)
