# 🚀 Quick Start - SchoolBot DevOps

## ⚡ Быстрый запуск

### 1. Подготовка
```bash
# Клонирование и настройка
git clone <repository-url>
cd SchoolBot
cp env.example .env
# Отредактируйте .env с вашими настройками
```

### 2. Инициализация системы мониторинга
```bash
# Автоматическая настройка всех компонентов
./scripts/init_monitoring.sh
```

### 3. Запуск всех сервисов
```bash
# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### 4. Проверка работоспособности
```bash
# Health check
curl http://localhost:8080/healthz

# Метрики
curl http://localhost:8080/metrics

# Откройте в браузере:
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

## 📊 Доступные сервисы

| Сервис | URL | Логин | Назначение |
|--------|-----|-------|------------|
| 📊 **Grafana** | http://localhost:3000 | admin/admin123 | Дашборды и визуализация |
| 📈 **Prometheus** | http://localhost:9090 | - | Сбор метрик |
| 🔔 **Alertmanager** | http://localhost:9093 | - | Уведомления |
| 🤖 **Bot Health** | http://localhost:8080/healthz | - | Проверка здоровья |
| 📊 **Bot Metrics** | http://localhost:8080/metrics | - | Метрики бота |
| 🐛 **GlitchTip** | http://localhost:9000 | - | Логирование ошибок |

## 🛠️ Основные команды

### Мониторинг
```bash
# Просмотр логов
docker-compose logs -f bot

# Проверка метрик
curl http://localhost:8080/metrics

# Статистика контейнеров
docker stats
```

### Бэкапы
```bash
# Создание бэкапа
./scripts/backup.sh

# Восстановление из бэкапа
./scripts/restore.sh

# Список бэкапов
ls -la backups/
```

### Масштабирование
```bash
# Масштабирование до 3 экземпляров
./scripts/scale.sh 3

# Проверка статуса
docker-compose ps
```

### Деплой
```bash
# Деплой в продакшн
./scripts/deploy.sh prod

# Деплой без тестов
RUN_TESTS=false ./scripts/deploy.sh prod
```

## 🔧 Настройка уведомлений

### Telegram алерты
1. Создайте бота через @BotFather
2. Добавьте в чат/канал для уведомлений
3. Получите chat_id:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```
4. Добавьте в `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

### GlitchTip (логирование ошибок)
1. Откройте http://localhost:9000
2. Войдите под суперпользователем
3. Создайте проект "SchoolBot"
4. Скопируйте DSN в `.env`:
   ```env
   GLITCHTIP_DSN=http://PublicKey@glitchtip:8000/1
   ```

## 📋 Переменные окружения

### Обязательные
```env
TELEGRAM_TOKEN=your_bot_token_here
POSTGRES_PASSWORD=secure_password_here
```

### Опциональные
```env
GLITCHTIP_DSN=http://PublicKey@glitchtip:8000/1
TELEGRAM_BOT_TOKEN=your_alert_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ENVIRONMENT=prod
KEEP_DAYS=14
```

## 🚨 Troubleshooting

### Проблемы с запуском
```bash
# Проверка логов
docker-compose logs

# Перезапуск сервисов
docker-compose restart

# Полная перезагрузка
docker-compose down && docker-compose up -d
```

### Проблемы с базой данных
```bash
# Проверка подключения
docker-compose exec postgres pg_isready -U schoolbot

# Применение миграций
docker-compose exec bot python manage.py migrate
```

### Проблемы с мониторингом
```bash
# Проверка Prometheus
curl http://localhost:9090/api/v1/status/targets

# Проверка Grafana
curl http://localhost:3000/api/health
```

## 📚 Дополнительная документация

- **Полное руководство**: [DEVOPS_GUIDE.md](DEVOPS_GUIDE.md)
- **Мониторинг**: [MONITORING.md](MONITORING.md)
- **Безопасность**: [SECURITY_GUIDELINES.md](SECURITY_GUIDELINES.md)
- **Логирование**: [GLITCHTIP.md](GLITCHTIP.md)

## 🎯 Готовность к продакшену

✅ **Полный мониторинг** с Prometheus + Grafana
✅ **Автоматические алерты** в Telegram
✅ **Автоматические бэкапы** с ротацией
✅ **Горизонтальное масштабирование** до 5 экземпляров
✅ **Zero-downtime деплой** с автоматизацией
✅ **Логирование ошибок** через GlitchTip
✅ **Health checks** для всех сервисов
✅ **Load balancer** для распределения нагрузки

---

**🎉 Готово!** Ваш SchoolBot теперь имеет полноценную DevOps-инфраструктуру промышленного уровня.
