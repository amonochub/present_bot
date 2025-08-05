# План улучшения кода present_bot

## ✅ Выполнено (приоритет 1 - критичные проблемы безопасности)

### Исправлены SQL Injection уязвимости:
- ✅ `app/repositories/optimized_user_repo.py` - устранены все 4 случая SQL injection
- ✅ `app/bot.py` - исправлена привязка к интерфейсам (0.0.0.0 → 127.0.0.1)

### Результат:
- 🔒 **Bandit ошибок**: 5 → 0 (все проблемы безопасности устранены)
- ⚡ **Ruff ошибок**: ~350 → 254 (улучшение на ~27%)

## 🔄 В процессе (приоритет 2 - типизация и стиль)

### Частично исправлено:
- ✅ Устаревшие импорты в `app/repositories/optimized_user_repo.py`
- ✅ Устаревшие импорты в `app/config.py`
- ✅ Сравнения с `True` заменены на прямые булевы проверки
- ✅ Длинные строки разбиты на несколько строк

### Остается сделать:

#### 1. Устаревшие импорты (приоритет 2.1)
```bash
# Файлы для исправления:
app/db/session.py - AsyncGenerator from typing
app/health.py - Dict from typing  
app/i18n/__init__.py - Dict from typing
app/middlewares/*.py - Awaitable, Callable from typing
app/repositories/media_repo.py - List from typing
app/repositories/note_repo.py - List from typing
app/schemas/news.py - типы
```

#### 2. Неиспользуемые импорты (приоритет 2.2)
```bash
# Основные файлы:
tests/test_docs_and_news_fixed.py - удалить Chat, InlineKeyboardMarkup, InlineKeyboardButton
tests/test_help_system.py - удалить Command, User
tests/test_localization.py - удалить pytest
tests/test_roles_and_access.py - удалить Dict, Any, patch
```

#### 3. Неорганизованные импорты (приоритет 2.3)
```bash
# Файлы требующие isort:
app/health.py
app/i18n/__init__.py  
tests/test_help_system.py
tests/test_localization.py
tests/test_performance_optimization.py
tests/test_roles_and_access.py
```

#### 4. Модульные импорты (приоритет 2.4)
```bash
# app/bot.py строки 239-243:
# Переместить импорты в начало файла
```

## 📋 Следующие шаги (приоритет 3 - архитектура)

### 3.1 Исправление типизации mypy (~206 ошибок)
- Исправить определение `Base` в моделях
- Добавить типизацию к декораторам
- Исправить возвращаемые типы Any
- Добавить missing type annotations

### 3.2 Длинные строки (приоритет 3.2)  
- Разбить строки превышающие 100 символов
- Улучшить читаемость кода

### 3.3 Архитектурные улучшения (приоритет 3.3)
- Вынести бизнес-логику из handlers
- Улучшить обработку ошибок
- Добавить документацию к функциям

## 🎯 Целевые метрики

### Текущие:
- **Bandit**: 0 ошибок ✅
- **Ruff**: 254 ошибки
- **MyPy**: 206 ошибок

### Цель (краткосрочная - 1 неделя):
- **Bandit**: 0 ошибок ✅
- **Ruff**: < 50 ошибок
- **MyPy**: < 100 ошибок

### Цель (долгосрочная - 1 месяц):
- **Bandit**: 0 ошибок ✅
- **Ruff**: 0 ошибок
- **MyPy**: 0 ошибок
- **Покрытие тестами**: 90%+

## 🛠 Рекомендуемые инструменты

### Автоматизация исправлений:
```bash
# Автоисправление ruff
ruff check . --fix

# Сортировка импортов  
isort app/ tests/

# Форматирование кода
black app/ tests/

# Обновление типов
pyupgrade --py311-plus app/**/*.py
```

### Настройка pre-commit:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
```

## 📊 Прогресс

### Безопасность: ✅ 100% (5/5 исправлено)
### Стиль кода: 🔄 27% (96/350 исправлено)  
### Типизация: ❌ 0% (0/206 исправлено)
### Общий прогресс: 🔄 17% (101/561 исправлено)

---

*Последнее обновление: 5 августа 2025 г.*
