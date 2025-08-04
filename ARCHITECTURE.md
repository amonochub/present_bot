# 🏗️ Архитектура School Bot

## 📋 Обзор системы

School Bot - это Telegram-бот для управления школьными процессами, построенный на принципах чистой архитектуры с разделением ответственности.

## 🏛️ Архитектурные принципы

### 1. **Слоистая архитектура**
```
┌─────────────────────────────────────┐
│           Presentation Layer        │
│  (Routes, Keyboards, Middlewares)  │
├─────────────────────────────────────┤
│           Business Logic           │
│         (Services, Utils)          │
├─────────────────────────────────────┤
│           Data Access Layer        │
│      (Repositories, Database)      │
├─────────────────────────────────────┤
│           Infrastructure           │
│    (Config, Logging, Monitoring)   │
└─────────────────────────────────────┘
```

### 2. **Принципы проектирования**
- **Single Responsibility**: каждый модуль отвечает за одну задачу
- **Dependency Inversion**: зависимости от абстракций, а не от конкретных реализаций
- **Open/Closed**: открыт для расширения, закрыт для модификации
- **Interface Segregation**: клиенты не зависят от неиспользуемых интерфейсов

## 📁 Структура проекта

### Корневая директория
```
School_bot/
├── app/                    # Основной код приложения
├── scripts/               # Скрипты деплоя и управления
├── tests/                 # Тесты
├── migrations/            # Миграции базы данных
├── alembic/              # Конфигурация Alembic
├── grafana/              # Дашборды мониторинга
├── prometheus/           # Конфигурация метрик
├── alertmanager/         # Уведомления
└── docs/                 # Документация
```

### Директория `app/`
```
app/
├── __init__.py           # Инициализация приложения
├── bot.py               # Точка входа бота
├── config.py            # Конфигурация
├── health.py            # Health check endpoint
├── roles.py             # Ролевая модель
├── db/                  # Модели базы данных
├── routes/              # Обработчики команд
├── services/            # Бизнес-логика
├── repositories/        # Доступ к данным
├── middlewares/         # Промежуточное ПО
├── keyboards/           # Клавиатуры
├── handlers/            # Специальные обработчики
├── schemas/             # Pydantic схемы
├── utils/               # Утилиты
└── i18n/               # Локализация
```

## 🔄 Поток данных

### 1. **Обработка команды пользователя**
```
User Input → Middleware → Route → Service → Repository → Database
                ↓
Response ← Keyboard ← Service ← Repository ← Database
```

### 2. **Детальный поток**
```
1. Пользователь отправляет команду
   ↓
2. Middleware (Rate Limit, CSRF, Audit)
   ↓
3. Route Handler (проверка роли)
   ↓
4. Service (бизнес-логика)
   ↓
5. Repository (доступ к данным)
   ↓
6. Database (PostgreSQL/Redis)
   ↓
7. Response (клавиатура + сообщение)
```

## 🏢 Основные компоненты

### 1. **Routes** (`app/routes/`)
**Назначение**: Обработка команд пользователей
**Принципы**:
- Один файл на роль (student.py, teacher.py, etc.)
- Проверка роли пользователя
- Делегирование бизнес-логики сервисам

**Пример структуры**:
```python
@router.message(Command("start"))
async def start_command(message: Message, user: User) -> None:
    """Обработка команды /start"""
    await start_service.handle_start(message, user)
```

### 2. **Services** (`app/services/`)
**Назначение**: Бизнес-логика приложения
**Принципы**:
- Инкапсуляция сложной логики
- Независимость от фреймворка
- Тестируемость

**Основные сервисы**:
- `notification_service.py` - уведомления
- `pdf_factory.py` - генерация PDF
- `scheduler.py` - планировщик задач
- `limiter.py` - ограничение запросов

### 3. **Repositories** (`app/repositories/`)
**Назначение**: Доступ к данным
**Принципы**:
- Абстракция над базой данных
- CRUD операции
- Кэширование

**Основные репозитории**:
- `user_repo.py` - пользователи
- `task_repo.py` - задачи
- `note_repo.py` - заметки
- `ticket_repo.py` - тикеты

### 4. **Database Models** (`app/db/`)
**Назначение**: Модели данных
**Принципы**:
- SQLAlchemy ORM
- Валидация данных
- Связи между таблицами

**Основные модели**:
- `user.py` - пользователи
- `task.py` - задачи
- `note.py` - заметки
- `ticket.py` - тикеты

### 5. **Middlewares** (`app/middlewares/`)
**Назначение**: Промежуточная обработка
**Принципы**:
- Cross-cutting concerns
- Переиспользуемость
- Конфигурируемость

**Основные middleware**:
- `rate_limit.py` - ограничение запросов
- `csrf.py` - защита от CSRF
- `audit.py` - аудит действий
- `locale.py` - локализация

### 6. **Keyboards** (`app/keyboards/`)
**Назначение**: Пользовательский интерфейс
**Принципы**:
- Ролевые клавиатуры
- Контекстные меню
- Локализация

## 🔧 Внешние сервисы

### 1. **База данных**
- **PostgreSQL**: основное хранилище данных
- **Redis**: кэширование и сессии
- **Alembic**: миграции

### 2. **Мониторинг**
- **Prometheus**: сбор метрик
- **Grafana**: визуализация
- **Alertmanager**: уведомления
- **Sentry/GlitchTip**: отслеживание ошибок

### 3. **Логирование**
- **Structured logging**: JSON формат
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Log rotation**: автоматическая ротация

### 4. **Безопасность**
- **CSRF tokens**: защита от подделки
- **Rate limiting**: защита от DDoS
- **Role-based access**: ролевая модель
- **Input validation**: валидация ввода

## 🔄 Жизненный цикл запроса

### 1. **Инициализация**
```python
# bot.py
async def main():
    # 1. Загрузка конфигурации
    config = load_config()
    
    # 2. Инициализация базы данных
    await init_database()
    
    # 3. Настройка middleware
    dp = setup_middleware()
    
    # 4. Регистрация роутов
    register_routes(dp)
    
    # 5. Запуск бота
    await dp.start_polling()
```

### 2. **Обработка сообщения**
```python
# 1. Получение сообщения от Telegram
message = await bot.get_updates()

# 2. Применение middleware
for middleware in middlewares:
    message = await middleware(message)

# 3. Маршрутизация
handler = router.get_handler(message)
if handler:
    response = await handler(message)
else:
    response = await default_handler(message)

# 4. Отправка ответа
await bot.send_message(response)
```

## 📊 Модель данных

### Основные сущности:
```
User (Пользователь)
├── id: int (PK)
├── telegram_id: int (UK)
├── role: UserRole
├── language: str
└── created_at: datetime

Task (Задача)
├── id: int (PK)
├── title: str
├── description: text
├── deadline: datetime
├── assigned_to: int (FK -> User)
└── status: TaskStatus

Note (Заметка)
├── id: int (PK)
├── content: text
├── author_id: int (FK -> User)
├── student_id: int (FK -> User)
└── created_at: datetime

Ticket (Тикет)
├── id: int (PK)
├── title: str
├── description: text
├── author_id: int (FK -> User)
├── status: TicketStatus
└── created_at: datetime
```

## 🎯 Паттерны проектирования

### 1. **Repository Pattern**
```python
class UserRepository:
    async def get_by_id(self, user_id: int) -> User:
        """Получить пользователя по ID"""
        
    async def create(self, user: User) -> User:
        """Создать пользователя"""
        
    async def update(self, user: User) -> User:
        """Обновить пользователя"""
```

### 2. **Service Layer Pattern**
```python
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def create_user(self, telegram_id: int, role: UserRole) -> User:
        """Создать нового пользователя"""
```

### 3. **Middleware Pattern**
```python
class RateLimitMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # Проверка лимита
        if not await self.check_limit(event):
            return await self.handle_limit_exceeded(event)
        return await handler(event, data)
```

## 🔧 Конфигурация

### Переменные окружения:
```env
# Telegram
TELEGRAM_TOKEN=your_bot_token

# Database
DB_NAME=schoolbot
DB_USER=schoolbot
DB_PASS=password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_DSN=redis://localhost:6379/0

# Environment
ENV=prod
ADMIN_IDS=123456,789012
```

## 📈 Масштабирование

### 1. **Горизонтальное масштабирование**
- Множественные экземпляры бота
- Балансировка нагрузки
- Общий Redis для сессий

### 2. **Вертикальное масштабирование**
- Увеличение ресурсов сервера
- Оптимизация запросов к БД
- Кэширование частых операций

### 3. **Микросервисная архитектура**
- Разделение на отдельные сервисы
- API Gateway
- Event-driven архитектура

## 🛡️ Безопасность

### 1. **Аутентификация**
- Telegram ID как основной идентификатор
- Ролевая модель доступа
- Валидация входных данных

### 2. **Авторизация**
- Проверка роли для каждого действия
- Изоляция данных между ролями
- Аудит всех действий

### 3. **Защита данных**
- Шифрование чувствительных данных
- Бэкапы с шифрованием
- Логирование доступа

---

**Дата создания**: $(date)  
**Версия**: 1.0  
**Статус**: ✅ Актуально 