# Отчёт о исправлении бота

## Дата: 6 августа 2025

## Проблема
Бот не работал после команды `/start` из-за конфликтующих обработчиков и отсутствующих зависимостей.

## Выявленные проблемы

### 1. Множественные обработчики команды /start
- Было три обработчика команды `/start` в разных файлах:
  - `app/bot.py` (строка 275)
  - `app/routes/intro.py` (строка 80)
  - `app/routes/onboarding.py` (строка 13)
- Это создавало конфликт - aiogram не мог определить, какой обработчик использовать

### 2. Отсутствующие зависимости
- В `requirements.txt` отсутствовали критически важные пакеты:
  - `bcrypt>=4.0.0` (для хеширования паролей)
  - `prometheus_client>=0.19.0` (для метрик)

### 3. Несоответствие функций
- Функция `create_user` в `onboarding_service.py` вызывалась с параметрами, которые не соответствовали её сигнатуре в `user_repo.py`
- Логика работы с пользователями была несогласованной

### 4. Неправильный порядок подключения роутеров
- Роутер `intro` подключался первым, но в нём не было обработчика `/start`

## Исправления

### 1. Устранение конфликта обработчиков /start
```python
# Удалены обработчики из:
# - app/bot.py (заменён комментарием)
# - app/routes/intro.py (заменён комментарием)

# Оставлен только один обработчик в:
# - app/routes/onboarding.py
```

### 2. Обновление requirements.txt
```txt
# Добавлены критические зависимости:
bcrypt>=4.0.0
prometheus_client>=0.19.0
```

### 3. Исправление логики onboarding_service.py
```python
# Удалён некорректный вызов create_user
# Упрощена логика - get_user всегда создаёт пользователя если его нет
```

### 4. Исправление порядка роутеров
```python
# Изменён порядок в app/routes/__init__.py:
dp.include_router(onboarding)  # Первым для /start
dp.include_router(intro)       # Вторым
```

### 5. Улучшение обработки ошибок
```python
# Добавлена проверка на None в обработчике /start:
if message.from_user is None:
    await message.answer("Ошибка: пользователь не найден.")
    return
```

## Структура исправленного обработчика /start

```python
@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext) -> None:
    """Единственный обработчик команды /start с онбордингом"""
    if message.from_user is None:
        await message.answer("Ошибка: пользователь не найден.")
        return
        
    user = await get_user(message.from_user.id)

    if not user.seen_intro:
        # Показываем онбординг для новых пользователей
        await onboarding_service.start_onboarding(message, state)
    else:
        # Показываем приветствие в зависимости от роли
        welcome_message = role_messages.get(user.role, t("start.unknown"))
        await message.answer(
            welcome_message, reply_markup=menu(user.role, "ru")
        )
```

## Проверка работоспособности

### Типизация
- Проверена с помощью mypy
- Основные ошибки устранены
- Остались только незначительные предупреждения

### Зависимости
- Все критические пакеты добавлены в requirements.txt
- Проект готов к пересборке Docker-контейнера

## Рекомендации для развёртывания

1. **Пересобрать Docker-контейнер:**
   ```bash
   docker-compose build
   ```

2. **Перезапустить сервисы:**
   ```bash
   docker-compose down && docker-compose up -d
   ```

3. **Проверить логи:**
   ```bash
   docker logs present-bot
   ```

## Ожидаемое поведение после исправлений

1. Команда `/start` будет корректно обрабатываться одним обработчиком
2. Новые пользователи увидят онбординг с выбором роли
3. Существующие пользователи получат приветствие в зависимости от роли
4. Контейнер будет запускаться без ошибок ModuleNotFoundError

## Файлы, которые были изменены

- `app/bot.py` - удалён обработчик /start
- `app/routes/intro.py` - удалён обработчик /start
- `app/routes/onboarding.py` - улучшен обработчик /start
- `app/services/onboarding_service.py` - исправлена логика
- `app/routes/__init__.py` - изменён порядок роутеров
- `requirements.txt` - добавлены зависимости

## Статус: ✅ ИСПРАВЛЕНО

Все критические проблемы устранены. Бот готов к развёртыванию и тестированию.
