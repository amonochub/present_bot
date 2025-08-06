# 🚨 DEPLOYMENT_CHECKLIST.md

## Чек-лист развертывания SchoolBot на сервере

### 🔍 **Анализ потенциальных проблем и решения**

## 1. 🐳 **Docker и Контейнеризация**

### ❌ Проблемы:
- Отсутствие Docker/Docker Compose на сервере
- Старая версия Docker (несовместимость с compose 3.9)
- Недостаток места для образов
- Проблемы с правами доступа к Docker

### ✅ Решения:
```bash
# Проверка системы перед деплоем
./scripts/check_server_requirements.sh

# Установка Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Проверка версий
docker --version          # >= 20.10
docker compose version    # >= 2.0
```

## 2. 🗄️ **База данных PostgreSQL**

### ❌ Проблемы:
- Конфликт портов (5432 уже занят)
- Недостаток места для данных
- Проблемы с кодировкой
- Отсутствие резервного копирования

### ✅ Решения:
```bash
# Проверка свободных портов
netstat -tulpn | grep :5432

# В production изменить порт в docker-compose.yml
# postgres:
#   ports:
#     - "5433:5432"  # Внешний порт 5433

# Автоматическое резервное копирование
crontab -e
# 0 2 * * * /app/scripts/backup_db.sh
```

## 3. 🔄 **Redis**

### ❌ Проблемы:
- Конфликт портов (6379 занят)
- Переполнение памяти
- Потеря данных при рестарте

### ✅ Решения:
```bash
# Проверка Redis
redis-cli ping || echo "Redis недоступен"

# Настройка персистентности в docker-compose.yml
# redis:
#   command: redis-server --appendonly yes
#   volumes:
#     - redis_data:/data
```

## 4. 🌐 **Сеть и Firewall**

### ❌ Проблемы:
- Заблокированные порты
- Конфликты сетей Docker
- Проблемы с DNS

### ✅ Решения:
```bash
# Открытие портов (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp

# Проверка сетевых интерфейсов
docker network ls
docker network prune  # Очистка неиспользуемых сетей
```

## 5. 🔐 **Безопасность**

### ❌ Проблемы:
- Слабые пароли в .env
- Отсутствие SSL/TLS
- Незащищенные порты БД
- Запуск от root

### ✅ Решения:
```bash
# Генерация сильных паролей
openssl rand -base64 32  # Для DB_PASS
openssl rand -hex 16     # Для секретных ключей

# Проверка безопасности
./scripts/security_check.sh

# Настройка SSL (Let's Encrypt)
sudo apt install certbot
sudo certbot --nginx -d yourdomain.com
```

## 6. 📁 **Файловая система**

### ❌ Проблемы:
- Недостаток места на диске
- Неправильные права доступа
- Отсутствие папок для логов

### ✅ Решения:
```bash
# Проверка места
df -h
du -sh /var/lib/docker

# Очистка Docker
docker system prune -af
docker volume prune

# Создание структуры папок
mkdir -p /var/log/schoolbot
mkdir -p /var/backups/schoolbot
mkdir -p /opt/schoolbot/data
```

## 7. 🔧 **Переменные окружения**

### ❌ Проблемы:
- Пустые или некорректные токены
- Отсутствие .env файла
- Неправильные ID администраторов

### ✅ Решения:
```bash
# Валидация .env перед запуском
./scripts/validate_env.sh

# Получение Telegram токена
# 1. Создать бота через @BotFather
# 2. Скопировать токен в .env

# Получение admin ID
# 1. Написать @userinfobot
# 2. Добавить ID в ADMIN_IDS
```

## 8. 🏥 **Мониторинг и Health Checks**

### ❌ Проблемы:
- Отсутствие мониторинга состояния
- Нет автоматического перезапуска
- Нет логирования ошибок

### ✅ Решения:
```bash
# Health check endpoint
curl http://localhost:8080/health

# Мониторинг через systemd
sudo systemctl enable schoolbot
sudo systemctl status schoolbot

# Настройка логирования
# Все логи в /var/log/schoolbot/
```

## 9. 🚀 **CI/CD и Автоматизация**

### ❌ Проблемы:
- Ручное развертывание
- Отсутствие откатов
- Нет тестирования перед деплоем

### ✅ Решения:
```bash
# Автоматический деплой
./scripts/deploy.sh

# Откат к предыдущей версии
./scripts/rollback.sh

# Pre-deployment тесты
./scripts/run_tests.sh
```

## 10. 📊 **Производительность**

### ❌ Проблемы:
- Недостаток RAM
- Медленная БД
- Блокировки процессов

### ✅ Решения:
```bash
# Мониторинг ресурсов
htop
docker stats

# Оптимизация PostgreSQL
# shared_buffers = 256MB
# max_connections = 100
# work_mem = 4MB

# Оптимизация Redis
# maxmemory 512mb
# maxmemory-policy allkeys-lru
```

---

## 🛠️ **Скрипты для решения проблем**

### 1. **scripts/check_server_requirements.sh**
```bash
#!/bin/bash
# Проверка готовности сервера к деплою

echo "🔍 Проверка системных требований..."

# Проверка ОС
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo "✅ ОС: $NAME $VERSION"
else
    echo "❌ Не удалось определить ОС"
    exit 1
fi

# Проверка Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker: $(docker --version)"
else
    echo "❌ Docker не установлен"
    exit 1
fi

# Проверка Docker Compose
if command -v docker compose &> /dev/null; then
    echo "✅ Docker Compose: $(docker compose version)"
else
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Проверка портов
check_port() {
    if ss -tulpn | grep ":$1" > /dev/null; then
        echo "⚠️  Порт $1 занят"
        return 1
    else
        echo "✅ Порт $1 свободен"
        return 0
    fi
}

check_port 5432  # PostgreSQL
check_port 6379  # Redis
check_port 8080  # Health check

# Проверка места на диске
available_space=$(df / | awk 'NR==2 {print $4}')
if [[ $available_space -lt 5000000 ]]; then  # 5GB
    echo "⚠️  Мало места на диске: $(($available_space/1024/1024))GB"
else
    echo "✅ Достаточно места на диске"
fi

# Проверка RAM
total_ram=$(free -m | awk 'NR==2{print $2}')
if [[ $total_ram -lt 1024 ]]; then  # 1GB
    echo "⚠️  Мало RAM: ${total_ram}MB"
else
    echo "✅ Достаточно RAM: ${total_ram}MB"
fi

echo "🎯 Проверка завершена"
```

### 2. **scripts/validate_env.sh**
```bash
#!/bin/bash
# Валидация переменных окружения

echo "🔍 Проверка переменных окружения..."

if [[ ! -f .env ]]; then
    echo "❌ Файл .env не найден"
    exit 1
fi

source .env

# Проверка обязательных переменных
required_vars=(
    "TELEGRAM_TOKEN"
    "DB_NAME"
    "DB_USER"
    "DB_PASS"
    "ADMIN_IDS"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Переменная $var не задана"
        exit 1
    else
        echo "✅ $var: задана"
    fi
done

# Проверка формата токена
if [[ ${#TELEGRAM_TOKEN} -lt 40 ]]; then
    echo "❌ Токен Telegram слишком короткий"
    exit 1
fi

# Проверка сложности пароля БД
if [[ ${#DB_PASS} -lt 8 ]]; then
    echo "⚠️  Пароль БД слишком простой"
fi

echo "🎯 Проверка переменных завершена"
```

### 3. **scripts/backup_db.sh**
```bash
#!/bin/bash
# Автоматическое резервное копирование БД

BACKUP_DIR="/var/backups/schoolbot"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/schoolbot_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

# Создание бэкапа
docker exec present-bot-postgres pg_dump -U schoolbot -d schoolbot > $BACKUP_FILE

if [[ $? -eq 0 ]]; then
    echo "✅ Бэкап создан: $BACKUP_FILE"
    
    # Сжатие
    gzip $BACKUP_FILE
    
    # Удаление старых бэкапов (старше 7 дней)
    find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
    
else
    echo "❌ Ошибка создания бэкапа"
    exit 1
fi
```

---

## 🚨 **Emergency Procedures**

### Быстрый откат
```bash
# 1. Остановить текущий контейнер
docker compose down

# 2. Восстановить предыдущую версию
git reset --hard HEAD~1

# 3. Перезапустить
docker compose up -d
```

### Восстановление БД
```bash
# 1. Найти последний бэкап
ls -la /var/backups/schoolbot/

# 2. Восстановить
gunzip -c backup_file.sql.gz | docker exec -i present-bot-postgres psql -U schoolbot -d schoolbot
```

### Экстренные контакты
- Администратор БД: `your_dba@company.com`
- DevOps команда: `devops@company.com`
- Мониторинг: `monitoring@company.com`

---

## ✅ **Финальный чек-лист перед деплоем**

- [ ] ✅ Сервер соответствует системным требованиям
- [ ] ✅ Docker и Docker Compose установлены
- [ ] ✅ Порты 5432, 6379, 8080 свободны
- [ ] ✅ Переменные окружения заданы корректно
- [ ] ✅ Telegram токен получен и проверен
- [ ] ✅ Admin IDs добавлены в конфигурацию
- [ ] ✅ SSL сертификаты настроены
- [ ] ✅ Firewall правила применены
- [ ] ✅ Мониторинг настроен
- [ ] ✅ Резервное копирование настроено
- [ ] ✅ Процедуры отката готовы

**После выполнения всех пунктов можно запускать деплой!** 🚀
