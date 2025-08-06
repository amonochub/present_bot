# 📊 DATABASE_SETUP.md

## Настройка базы данных SchoolBot

Этот документ описывает настройку и инициализацию базы данных для проекта SchoolBot.

## 🏗️ Структура

```
sql/
├── 01_init_schema.sql      # Основная схема БД
├── 02_demo_data.sql        # Демо-данные для тестирования
└── README.md               # Документация SQL

scripts/
├── init_db.sh              # Скрипт инициализации БД
└── run_migrations.sh       # Основной скрипт запуска
```

## 🚀 Автоматическая инициализация

При запуске Docker-контейнера БД инициализируется автоматически:

1. **Проверка готовности PostgreSQL**
2. **Создание БД** (если не существует)
3. **Применение схемы** из `01_init_schema.sql`
4. **Загрузка демо-данных** (в dev/test режиме)
5. **Применение миграций Alembic**

### Переменные окружения

```env
DB_NAME=schoolbot
DB_USER=schoolbot
DB_PASS=schoolbot_secure_password
DB_HOST=postgres
DB_PORT=5432
ENV=prod  # prod/dev/test
```

## 🛠️ Ручная настройка

### Локальная разработка

```bash
# 1. Запуск PostgreSQL
docker run -d \
  --name postgres-schoolbot \
  -e POSTGRES_DB=schoolbot \
  -e POSTGRES_USER=schoolbot \
  -e POSTGRES_PASSWORD=schoolbot \
  -p 5432:5432 \
  postgres:15-alpine

# 2. Выполнение SQL-скриптов
psql -h localhost -U schoolbot -d schoolbot -f sql/01_init_schema.sql
psql -h localhost -U schoolbot -d schoolbot -f sql/02_demo_data.sql

# 3. Применение миграций
alembic upgrade head
```

### Production

```bash
# Только схема, без демо-данных
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/01_init_schema.sql
alembic upgrade head
```

## 🏢 Схема базы данных

### Основные таблицы

| Таблица | Описание | Связи |
|---------|----------|-------|
| `users` | Пользователи системы | Основная таблица |
| `notes` | Заметки учителей | users.id |
| `tickets` | Тикеты техподдержки | users.id |
| `psych_requests` | Запросы к психологу | users.id |
| `media_requests` | Запросы документов | users.id |
| `tasks` | Задачи от администрации | users.id |
| `broadcasts` | Рассылки | users.id |
| `notifications` | Уведомления | users.id |

### Роли пользователей

- `admin` - Администратор системы
- `director` - Директор школы  
- `teacher` - Учитель
- `psych` - Школьный психолог
- `parent` - Родитель
- `student` - Ученик

## 🔧 Миграции

### Создание новой миграции

```bash
# Автогенерация на основе изменений в моделях
alembic revision --autogenerate -m "Описание изменений"

# Ручное создание миграции
alembic revision -m "Описание изменений"
```

### Применение миграций

```bash
# Применить все неприменённые миграции
alembic upgrade head

# Применить до конкретной ревизии
alembic upgrade <revision_id>

# Откат к предыдущей версии
alembic downgrade -1
```

## 🔍 Мониторинг

### Полезные запросы

```sql
-- Статистика пользователей по ролям
SELECT role, COUNT(*) as count 
FROM users 
WHERE is_active = true 
GROUP BY role;

-- Непрочитанные уведомления
SELECT u.username, COUNT(n.id) as unread_notifications
FROM users u
LEFT JOIN notifications n ON u.id = n.user_id AND n.is_read = false
GROUP BY u.id, u.username
HAVING COUNT(n.id) > 0;

-- Открытые тикеты по приоритету
SELECT priority, COUNT(*) as count
FROM tickets 
WHERE status IN ('open', 'pending')
GROUP BY priority
ORDER BY 
  CASE priority 
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2  
    WHEN 'low' THEN 3
  END;
```

### Индексы производительности

Система использует следующие индексы:

- `idx_users_tg_id` - Поиск по Telegram ID
- `idx_users_role` - Фильтрация по ролям
- `idx_tickets_status` - Фильтрация тикетов по статусу
- `idx_notifications_is_read` - Непрочитанные уведомления

## 🔒 Безопасность

### Рекомендации

1. **Пароли БД**: Используйте сложные пароли в production
2. **Доступ**: Ограничьте сетевой доступ к PostgreSQL
3. **Резервные копии**: Настройте регулярное резервное копирование
4. **SSL**: Используйте SSL-соединения в production

### Резервное копирование

```bash
# Создание бэкапа
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_file.sql
```

## 🚨 Troubleshooting

### Типичные проблемы

1. **Таблицы не созданы**
   ```bash
   # Проверьте логи контейнера
   docker logs present-bot-postgres
   
   # Выполните инициализацию вручную
   docker exec -it present-bot psql -h postgres -U schoolbot -d schoolbot -f /app/sql/01_init_schema.sql
   ```

2. **Ошибки миграций**
   ```bash
   # Проверьте состояние миграций
   alembic current
   alembic history
   
   # Принудительно установите текущую версию
   alembic stamp head
   ```

3. **Проблемы с доступом**
   ```bash
   # Проверьте подключение
   docker exec -it present-bot-postgres psql -U schoolbot -d schoolbot -c "SELECT 1;"
   ```

## ✅ Проверка работоспособности

```bash
# Проверка подключения к БД
docker exec -it present-bot python -c "
from app.db.session import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT COUNT(*) FROM users')
        print(f'Пользователей в БД: {result.scalar()}')
asyncio.run(test())
"

# Проверка демо-данных
docker exec -it present-bot-postgres psql -U schoolbot -d schoolbot -c "
SELECT role, COUNT(*) 
FROM users 
GROUP BY role;
"
```
