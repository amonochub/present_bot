# 🚀 Сводка по деплою School Bot на сервер

## ✅ Статус: Готово к деплою

Все инструменты для деплоя на сервер `89.169.38.246` созданы и готовы к использованию.

## 📋 Созданные инструменты

### 1. **Автоматический скрипт деплоя**
```bash
./scripts/deploy_to_server.sh
```
- Автоматически копирует все файлы на сервер
- Настраивает Docker и зависимости
- Создает systemd сервис
- Настраивает firewall
- Включает автозапуск

### 2. **Скрипт настройки сервера**
```bash
./scripts/server_setup.sh
```
- Устанавливает все необходимые пакеты
- Настраивает окружение
- Создает конфигурационные файлы
- Настраивает мониторинг

### 3. **Подробное руководство**
`SERVER_DEPLOYMENT_GUIDE.md` - полное руководство по деплою

## 🔧 Быстрый старт

### Вариант 1: Автоматический деплой
```bash
# Установите sshpass (если не установлен)
brew install sshpass  # macOS
# или
sudo apt install sshpass  # Ubuntu

# Запустите автоматический деплой
./scripts/deploy_to_server.sh
```

### Вариант 2: Ручная настройка
```bash
# 1. Подключитесь к серверу
ssh root@89.169.38.246

# 2. Скачайте и запустите скрипт настройки
curl -o /tmp/server_setup.sh https://raw.githubusercontent.com/your-repo/school-bot/main/scripts/server_setup.sh
chmod +x /tmp/server_setup.sh
/tmp/server_setup.sh

# 3. Настройте переменные окружения
nano /opt/school-bot/.env

# 4. Запустите сервис
systemctl start schoolbot.service
```

## 📊 Информация о сервере

### Сервер
- **IP**: `89.169.38.246`
- **Пользователь**: `root`
- **Пароль**: `e*xB9L%ZfPiu`

### Порты
- **22**: SSH
- **80**: HTTP
- **443**: HTTPS
- **8080**: Bot health check
- **9000**: Webhook server

## 🔍 Проверка после деплоя

### 1. Подключение к серверу
```bash
ssh root@89.169.38.246
```

### 2. Проверка статуса
```bash
# Статус сервиса
systemctl status schoolbot.service

# Статус контейнеров
docker-compose ps

# Мониторинг
/opt/school-bot/scripts/monitor.sh
```

### 3. Проверка webhook-сервера
```bash
# Проверка основного эндпоинта
curl http://localhost:9000/

# Проверка health endpoint
curl http://localhost:9000/health

# Тест webhook для School Bot
curl -X POST http://localhost:9000/webhook/school-bot
```

### 4. Проверка бота
```bash
# Health check
curl http://localhost:8080/health

# Логи бота
docker-compose logs bot
```

## 🛠️ Управление после деплоя

### Основные команды
```bash
# Запуск/остановка сервиса
systemctl start schoolbot.service
systemctl stop schoolbot.service
systemctl restart schoolbot.service

# Просмотр логов
docker-compose logs -f bot
journalctl -u schoolbot.service -f

# Обновление
/opt/school-bot/scripts/update.sh

# Мониторинг
/opt/school-bot/scripts/monitor.sh
```

### Интеграция с webhook-сервером
Если у вас уже есть webhook-сервер, добавьте новый эндпоинт:

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

## 🔒 Безопасность

### Настроенный firewall
- SSH (22)
- HTTP (80)
- HTTPS (443)
- Bot health check (8080)
- Webhook server (9000)

### Рекомендации
1. Измените пароль root после настройки
2. Настройте SSH-ключи вместо пароля
3. Регулярно обновляйте систему
4. Настройте бэкапы

## 📈 Мониторинг

### Системные ресурсы
```bash
# Использование ресурсов
htop
df -h
free -h
```

### Логирование
```bash
# Логи systemd
journalctl -u schoolbot.service -f

# Логи Docker
docker-compose logs -f

# Логи webhook-сервера
journalctl -u webhook-server -f
```

## 🎯 CI/CD

### Настройка webhook в GitHub/GitLab
URL: `http://89.169.38.246:9000/webhook/school-bot`

### Автоматическое обновление
При push в репозиторий бот автоматически обновится через webhook.

## ✅ Чек-лист завершения

- [ ] Сервер доступен по SSH
- [ ] Автоматический скрипт деплоя создан
- [ ] Руководство по деплою создано
- [ ] Скрипты мониторинга готовы
- [ ] Инструкции по управлению созданы
- [ ] Рекомендации по безопасности предоставлены

## 🎉 Готово!

Все инструменты для деплоя School Bot на сервер созданы и готовы к использованию.

**Быстрый запуск:**
```bash
./scripts/deploy_to_server.sh
```

**Полезные ссылки:**
- Health check: `http://89.169.38.246:8080/health`
- Webhook: `http://89.169.38.246:9000/webhook/school-bot`
- Мониторинг: `/opt/school-bot/scripts/monitor.sh`

---

**Дата создания**: $(date)  
**Статус**: ✅ Готово к деплою 