# 🚀 Деплой SchoolBot на сервер

## 📋 Требования

- Сервер с Docker и Docker Compose
- SSH доступ к серверу
- Git репозиторий с кодом

## 🔧 Настройка переменных окружения

Создайте файл `.env` на основе `env.example`:

```bash
# Telegram Bot
TELEGRAM_TOKEN=your_telegram_bot_token

# Database
POSTGRES_DB=schoolbot
POSTGRES_USER=schoolbot
POSTGRES_PASSWORD=secure_password_here

# Redis
REDIS_URL=redis://redis:6379/0

# Admin configuration
ADMIN_IDS=123456789,987654321

# Monitoring
GLITCHTIP_DSN=your_glitchtip_dsn
ENVIRONMENT=prod

# App settings
KEEP_DAYS=14
```

## 🚀 Автоматический деплой

### 1. Настройка переменных для деплоя

```bash
export SERVER_HOST=89.169.38.246
export SERVER_USER=root
```

### 2. Запуск деплоя

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## 🔧 Ручной деплой

### 1. Подключение к серверу

```bash
ssh root@89.169.38.246
```

### 2. Создание директории для бота

```bash
mkdir -p /srv/bots/present-bot
cd /srv/bots/present-bot
```

### 3. Клонирование репозитория

```bash
git clone https://github.com/your-repo/schoolbot.git .
```

### 4. Создание .env файла

```bash
cp env.example .env
# Отредактируйте .env файл с вашими настройками
nano .env
```

### 5. Создание общей сети Docker

```bash
docker network create shared-net
```

### 6. Запуск бота

```bash
docker-compose up -d
```

## 📊 Мониторинг

### Health Check

```bash
# Проверка здоровья бота
curl http://localhost:8080/health

# Детальная проверка
curl http://localhost:8080/health/detailed

# Prometheus метрики
curl http://localhost:8080/metrics
```

### Логи

```bash
# Логи бота
docker-compose logs -f bot

# Логи базы данных
docker-compose logs -f postgres

# Логи Redis
docker-compose logs -f redis
```

### Статус контейнеров

```bash
docker-compose ps
```

## 🔄 Обновление

### Автоматическое обновление

Создан скрипт для автоматического обновления:

```bash
/srv/bots/update_all_bots.sh
```

### Ручное обновление

```bash
cd /srv/bots/present-bot
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🛠️ Устранение неполадок

### Проблемы с зависимостями

```bash
# Пересборка образа
docker-compose build --no-cache

# Проверка requirements.txt
cat requirements.txt
```

### Проблемы с базой данных

```bash
# Проверка подключения к БД
docker-compose exec postgres psql -U schoolbot -d schoolbot

# Применение миграций
docker-compose exec bot python manage.py migrate
```

### Проблемы с Redis

```bash
# Проверка Redis
docker-compose exec redis redis-cli ping

# Очистка Redis
docker-compose exec redis redis-cli flushall
```

### Проблемы с сетью

```bash
# Проверка сетей Docker
docker network ls

# Создание общей сети
docker network create shared-net
```

## 📈 Мониторинг и логирование

### Grafana Dashboard

Доступен по адресу: `http://server:3000`
- Логин: `admin`
- Пароль: `admin123`

### Prometheus

Доступен по адресу: `http://server:9090`

### GlitchTip (мониторинг ошибок)

Доступен по адресу: `http://server:9000`

## 🔒 Безопасность

### Firewall

```bash
# Открываем только необходимые порты
ufw allow 22/tcp    # SSH
ufw allow 8080/tcp  # Health check
ufw allow 3000/tcp  # Grafana
ufw allow 9090/tcp  # Prometheus
ufw enable
```

### SSL/TLS

Для продакшена рекомендуется настроить SSL/TLS через nginx или traefik.

## 📝 Логи

Логи сохраняются в следующих местах:

- Docker логи: `docker-compose logs`
- Системные логи: `/var/log/syslog`
- Обновления: `/var/log/bot-updates.log`

## 🔄 Автоматические обновления

Настроена cron задача для автоматических обновлений каждые 6 часов:

```bash
# Проверка cron задач
crontab -l

# Ручной запуск обновления
/srv/bots/update_all_bots.sh
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs`
2. Проверьте health check: `curl http://localhost:8080/health`
3. Проверьте статус контейнеров: `docker-compose ps`
4. Проверьте использование ресурсов: `docker stats` 