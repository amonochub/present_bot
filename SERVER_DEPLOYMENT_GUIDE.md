# 🚀 Руководство по деплою School Bot на сервер

## 📋 Предварительные требования

### Сервер: `89.169.38.246`
- **Пользователь**: `root`
- **Пароль**: `e*xB9L%ZfPiu`

## 🔧 Пошаговая настройка

### 1. Подключение к серверу
```bash
ssh root@89.169.38.246
# Пароль: e*xB9L%ZfPiu
```

### 2. Запуск автоматического скрипта настройки
```bash
# Скачиваем скрипт на сервер
curl -o /tmp/server_setup.sh https://raw.githubusercontent.com/your-repo/school-bot/main/scripts/server_setup.sh

# Делаем исполняемым и запускаем
chmod +x /tmp/server_setup.sh
/tmp/server_setup.sh
```

### 3. Настройка переменных окружения
```bash
# Редактируем .env файл
nano /opt/school-bot/.env
```

**Содержимое .env:**
```env
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_actual_telegram_token_here

# Database Configuration
POSTGRES_DB=schoolbot
POSTGRES_USER=schoolbot
POSTGRES_PASSWORD=secure_password_change_me

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Admin Configuration
ADMIN_IDS=your_admin_id_here

# Environment
ENVIRONMENT=prod
KEEP_DAYS=14

# Monitoring (optional)
GLITCHTIP_DSN=
```

### 4. Запуск сервиса
```bash
# Запуск сервиса
systemctl start schoolbot.service

# Проверка статуса
systemctl status schoolbot.service

# Проверка контейнеров
docker-compose ps
```

### 5. Интеграция с существующим webhook-сервером

Если у вас уже есть webhook-сервер на порту 9000, добавим School Bot в него:

```bash
# Редактируем webhook-сервер
nano /opt/webhook-server/app.py
```

**Добавляем новый эндпоинт:**
```python
@app.post("/webhook/school-bot")
async def deploy_school_bot(request: Request):
    subprocess.Popen(
        ["/opt/school-bot/scripts/update.sh"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return {"status": "ok", "bot": "school-bot"}
```

**Перезапускаем webhook-сервер:**
```bash
systemctl restart webhook-server
```

## 🔍 Проверка работоспособности

### 1. Проверка webhook-сервера
```bash
# Проверка основного эндпоинта
curl http://localhost:9000/

# Проверка health endpoint
curl http://localhost:9000/health

# Тест webhook для School Bot
curl -X POST http://localhost:9000/webhook/school-bot
```

### 2. Проверка School Bot
```bash
# Статус контейнеров
docker-compose ps

# Логи бота
docker-compose logs bot

# Health check
curl http://localhost:8080/health
```

### 3. Мониторинг системы
```bash
# Использование скрипта мониторинга
/opt/school-bot/scripts/monitor.sh

# Просмотр логов в реальном времени
docker-compose logs -f bot
```

## 🛠️ Полезные команды

### Управление сервисом
```bash
# Запуск
systemctl start schoolbot.service

# Остановка
systemctl stop schoolbot.service

# Перезапуск
systemctl restart schoolbot.service

# Статус
systemctl status schoolbot.service

# Автозапуск
systemctl enable schoolbot.service
```

### Управление контейнерами
```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs bot
docker-compose logs postgres
docker-compose logs redis

# Пересборка и перезапуск
docker-compose build --no-cache
docker-compose up -d

# Остановка
docker-compose down
```

### Обновление
```bash
# Автоматическое обновление
/opt/school-bot/scripts/update.sh

# Или вручную
cd /opt/school-bot
git pull
docker-compose build --no-cache
docker-compose up -d
```

## 🔧 Устранение неполадок

### 1. Проблемы с Docker
```bash
# Перезапуск Docker
systemctl restart docker

# Очистка неиспользуемых ресурсов
docker system prune -f
```

### 2. Проблемы с базой данных
```bash
# Проверка подключения к PostgreSQL
docker-compose exec postgres psql -U schoolbot -d schoolbot -c "SELECT 1;"

# Сброс базы данных (осторожно!)
docker-compose down
docker volume rm school-bot_postgres_data
docker-compose up -d
```

### 3. Проблемы с Redis
```bash
# Проверка Redis
docker-compose exec redis redis-cli ping

# Очистка Redis
docker-compose exec redis redis-cli FLUSHALL
```

### 4. Проблемы с ботом
```bash
# Перезапуск только бота
docker-compose restart bot

# Просмотр логов в реальном времени
docker-compose logs -f bot

# Проверка переменных окружения
docker-compose exec bot env | grep -E "(TELEGRAM|DB_|REDIS|ADMIN)"
```

## 📊 Мониторинг и логирование

### 1. Системный мониторинг
```bash
# Использование ресурсов
htop

# Дисковое пространство
df -h

# Память
free -h

# Сетевые соединения
netstat -tlnp
```

### 2. Логирование
```bash
# Логи systemd
journalctl -u schoolbot.service -f

# Логи Docker
docker-compose logs -f

# Логи webhook-сервера
journalctl -u webhook-server -f
```

## 🔒 Безопасность

### 1. Firewall
```bash
# Проверка статуса firewall
ufw status

# Добавление правил
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8080/tcp  # Bot health check
ufw allow 9000/tcp  # Webhook server
```

### 2. Обновление системы
```bash
# Регулярное обновление
apt update && apt upgrade -y

# Обновление Docker
apt update && apt install docker.io docker-compose
```

## 🎯 Автоматизация

### 1. Настройка CI/CD
Создайте webhook в GitHub/GitLab, указывающий на:
```
http://89.169.38.246:9000/webhook/school-bot
```

### 2. Автоматические бэкапы
```bash
# Создание скрипта бэкапа
cat > /opt/school-bot/scripts/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"

mkdir -p $BACKUP_DIR

# Бэкап базы данных
docker-compose exec postgres pg_dump -U schoolbot schoolbot > $BACKUP_DIR/db_$DATE.sql

# Бэкап конфигурации
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose.yml

echo "Backup completed: $DATE"
EOF

chmod +x /opt/school-bot/scripts/backup.sh
```

## ✅ Чек-лист завершения

- [ ] Сервер настроен и обновлен
- [ ] Docker установлен и запущен
- [ ] School Bot развернут и работает
- [ ] Webhook-сервер настроен
- [ ] Переменные окружения настроены
- [ ] Firewall настроен
- [ ] Автозапуск включен
- [ ] Мониторинг настроен
- [ ] Бэкапы настроены

## 🎉 Готово!

Ваш School Bot теперь развернут на сервере и готов к работе!

**Полезные ссылки:**
- Health check: `http://89.169.38.246:8080/health`
- Webhook: `http://89.169.38.246:9000/webhook/school-bot`
- Мониторинг: `/opt/school-bot/scripts/monitor.sh`

---

**Дата создания**: $(date)  
**Статус**: ✅ Готово к использованию 