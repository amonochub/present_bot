# 🚀 DevOps Guide - SchoolBot

Полное руководство по развертыванию, мониторингу и обслуживанию SchoolBot в продакшн-среде.

## 📋 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Архитектура](#архитектура)
3. [Мониторинг](#мониторинг)
4. [Масштабирование](#масштабирование)
5. [Бэкапы и восстановление](#бэкапы-и-восстановление)
6. [Деплой](#деплой)
7. [Безопасность](#безопасность)
8. [Troubleshooting](#troubleshooting)

## 🚀 Быстрый старт

### Требования

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM минимум
- 10GB свободного места

### Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd SchoolBot

# Настройка переменных окружения
cp env.example .env
# Отредактируйте .env с вашими настройками

# Инициализация системы мониторинга
./scripts/init_monitoring.sh

# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### Проверка работоспособности

```bash
# Health check
curl http://localhost:8080/healthz

# Метрики
curl http://localhost:8080/metrics

# Grafana
open http://localhost:3000  # admin/admin123

# Prometheus
open http://localhost:9090
```

## 🏗️ Архитектура

### Компоненты системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │   SchoolBot     │    │   PostgreSQL    │
│   Bot API       │◄──►│   (Aiogram)     │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Cache/FSM)   │
                       └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │    Grafana      │    │  Alertmanager   │
│   (Metrics)     │◄──►│   (Dashboards)  │◄──►│  (Alerts)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   GlitchTip     │
                       │  (Error Logs)   │
                       └─────────────────┘
```

### Сервисы Docker Compose

| Сервис | Порт | Назначение |
|--------|------|------------|
| `bot` | 8080 | Основной бот + health check |
| `postgres` | 5432 | База данных |
| `redis` | 6379 | Кэш и FSM |
| `prometheus` | 9090 | Сбор метрик |
| `grafana` | 3000 | Дашборды |
| `alertmanager` | 9093 | Уведомления |
| `glitchtip` | 9000 | Логирование ошибок |
| `nginx` | 80 | Load balancer (при масштабировании) |

## 📊 Мониторинг

### Метрики Prometheus

#### Автоматически собираемые метрики

- **`bot_requests_total`** - Общее количество запросов
- **`bot_errors_total`** - Общее количество ошибок
- **`bot_latency_seconds`** - Время выполнения запросов
- **`bot_tickets_open`** - Количество открытых заявок
- **`kpi_tasks_total`** - Всего поручений директора
- **`kpi_tasks_done`** - Выполнено поручений
- **`kpi_tasks_overdue`** - Просрочено поручений

#### Полезные запросы

```promql
# Запросы в секунду
rate(bot_requests_total[5m])

# Ошибки в секунду
rate(bot_errors_total[5m])

# 95-й перцентиль латентности
histogram_quantile(0.95, rate(bot_latency_seconds_bucket[5m]))

# Открытые заявки
bot_tickets_open

# Процент выполнения задач
(kpi_tasks_done / kpi_tasks_total) * 100
```

### Алерты

#### Настроенные алерты

| Алерт | Условие | Действие |
|-------|---------|----------|
| **HighErrorRate** | >3 ошибок за 5 мин | Критический |
| **TooManyOpenTickets** | >10 открытых заявок | Предупреждение |
| **BotDown** | Бот недоступен 30с | Критический |
| **HighLatency** | 95% > 2 секунд | Предупреждение |
| **TooManyOverdueTasks** | >3 просроченных задач | Критический |

#### Настройка уведомлений

1. **Создайте бота** через @BotFather
2. **Добавьте в чат/канал** для уведомлений
3. **Получите chat_id**:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```
4. **Добавьте в .env**:
   ```env
   TELEGRAM_BOT_TOKEN=123456:ABC...
   TELEGRAM_CHAT_ID=-987654321
   ```

### Дашборды Grafana

#### Автоматически создаваемые панели

- **Requests per Second** - График запросов в секунду
- **Errors per Second** - График ошибок в секунду
- **95th Percentile Latency** - 95-й перцентиль времени ответа
- **Open Tickets** - Количество открытых заявок
- **Task Completion Rate** - Процент выполнения задач

#### Кастомизация дашбордов

1. Откройте Grafana: http://localhost:3000
2. Логин: `admin/admin123`
3. Дашборд "SchoolBot Dashboard" создается автоматически
4. Для кастомизации: Edit → Export → Save to file

## 📈 Масштабирование

### Горизонтальное масштабирование

```bash
# Масштабирование до 3 экземпляров
./scripts/scale.sh 3

# Проверка статуса
docker-compose ps

# Мониторинг производительности
docker stats
```

### Автоматическое масштабирование

```yaml
# docker-compose.override.yml
services:
  bot:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

### Load Balancer

Nginx автоматически настраивается для распределения нагрузки:

```nginx
upstream bot_backend {
    least_conn;
    server bot:8080 max_fails=3 fail_timeout=30s;
}
```

### Мониторинг производительности

```bash
# Использование ресурсов
docker stats

# Логи производительности
docker-compose logs --tail=100 bot

# Метрики в реальном времени
curl http://localhost:8080/metrics
```

## 💾 Бэкапы и восстановление

### Автоматические бэкапы

```bash
# Создание бэкапа
./scripts/backup.sh

# Список бэкапов
ls -la backups/

# Размер бэкапов
du -sh backups/*
```

### Восстановление из бэкапа

```bash
# Восстановление
./scripts/restore.sh [backup_file]

# Интерактивный выбор
./scripts/restore.sh
```

### Планирование бэкапов

```bash
# Добавление в crontab
echo "0 2 * * * /path/to/SchoolBot/scripts/backup.sh" | crontab -

# Проверка расписания
crontab -l
```

### Валидация бэкапов

```bash
# Проверка целостности
pg_restore --list backup_file.sql

# Тестовое восстановление
pg_restore --dry-run backup_file.sql
```

## 🚀 Деплой

### Автоматический деплой

```bash
# Деплой в продакшн
./scripts/deploy.sh prod

# Деплой в staging
./scripts/deploy.sh staging

# Деплой без тестов
RUN_TESTS=false ./scripts/deploy.sh prod
```

### Zero-Downtime деплой

1. **Создание бэкапа** текущего состояния
2. **Запуск тестов** для проверки работоспособности
3. **Применение миграций** базы данных
4. **Graceful restart** сервисов
5. **Проверка здоровья** всех компонентов

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: python3 -m pytest tests/
      - name: Security scan
        run: bandit -r app/
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: ./scripts/deploy.sh prod
```

### Переменные окружения

#### Обязательные переменные

```env
# Telegram Bot
TELEGRAM_TOKEN=your_bot_token_here

# Database
POSTGRES_DB=schoolbot
POSTGRES_USER=schoolbot
POSTGRES_PASSWORD=secure_password_here

# Redis
REDIS_URL=redis://redis:6379/0

# Monitoring
GLITCHTIP_DSN=http://PublicKey@glitchtip:8000/1
TELEGRAM_BOT_TOKEN=your_alert_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Application
ENVIRONMENT=prod
KEEP_DAYS=14
```

#### Опциональные переменные

```env
# Scaling
BOT_INSTANCE_ID=0
LOG_LEVEL=INFO

# Backup
BACKUP_BEFORE_DEPLOY=true
RUN_TESTS=true
NOTIFY_TELEGRAM=true
```

## 🔒 Безопасность

### Секреты и переменные окружения

```bash
# Проверка секретов
grep -r "password\|token\|secret" . --exclude-dir=.git

# Ротация токенов
# 1. Создайте новый токен в BotFather
# 2. Обновите TELEGRAM_TOKEN в .env
# 3. Перезапустите сервисы
docker-compose restart bot
```

### Сетевая безопасность

```bash
# Проверка открытых портов
netstat -tlnp

# Firewall правила
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (если используется)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Обновления безопасности

```bash
# Обновление образов
docker-compose pull

# Пересборка с обновлениями
docker-compose build --no-cache

# Проверка уязвимостей
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image schoolbot_bot:latest
```

## 🔧 Troubleshooting

### Проблемы с ботом

```bash
# Проверка логов
docker-compose logs bot

# Проверка здоровья
curl http://localhost:8080/healthz

# Перезапуск бота
docker-compose restart bot

# Проверка подключения к Telegram
curl "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe"
```

### Проблемы с базой данных

```bash
# Проверка подключения
docker-compose exec postgres pg_isready -U schoolbot

# Проверка миграций
docker-compose exec bot python manage.py showmigrations

# Применение миграций
docker-compose exec bot python manage.py migrate

# Проверка данных
docker-compose exec postgres psql -U schoolbot -d schoolbot -c "SELECT COUNT(*) FROM users;"
```

### Проблемы с мониторингом

```bash
# Проверка Prometheus
curl http://localhost:9090/api/v1/status/targets

# Проверка Grafana
curl http://localhost:3000/api/health

# Проверка Alertmanager
curl http://localhost:9093/api/v1/status

# Проверка GlitchTip
curl http://localhost:9000/health
```

### Проблемы с производительностью

```bash
# Использование ресурсов
docker stats

# Проверка метрик
curl http://localhost:8080/metrics

# Анализ логов
docker-compose logs --tail=1000 bot | grep ERROR

# Проверка кэша Redis
docker-compose exec redis redis-cli INFO memory
```

### Восстановление после сбоя

```bash
# Полная перезагрузка
docker-compose down
docker-compose up -d

# Восстановление из бэкапа
./scripts/restore.sh latest_backup.sql

# Проверка всех сервисов
./scripts/init_monitoring.sh
```

## 📚 Дополнительные ресурсы

### Документация

- [Docker Compose](https://docs.docker.com/compose/)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [GlitchTip](https://glitchtip.com/docs/)
- [Aiogram](https://docs.aiogram.dev/)

### Полезные команды

```bash
# Просмотр всех логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f bot

# Выполнение команд в контейнере
docker-compose exec bot python manage.py shell

# Создание бэкапа с сжатием
docker-compose exec postgres pg_dump -U schoolbot schoolbot | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Мониторинг в реальном времени
watch -n 1 'docker stats --no-stream'
```

### Контакты для поддержки

- **Issues**: GitHub Issues
- **Documentation**: README.md и документация в репозитории
- **Monitoring**: Grafana и GlitchTip дашборды
- **Logs**: Docker logs и GlitchTip

---

**🎉 Поздравляем!** Ваш SchoolBot готов к продакшн-эксплуатации с полным набором DevOps-инструментов для мониторинга, масштабирования и обслуживания. 