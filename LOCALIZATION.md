# 🌍 Локализация School Bot

## 📋 Обзор системы локализации

School Bot поддерживает многоязычность через систему локализации на основе TOML файлов. Система автоматически определяет язык пользователя и предоставляет интерфейс на соответствующем языке.

## 🏗️ Архитектура локализации

### Структура файлов
```
app/i18n/
├── __init__.py          # Инициализация локализации
├── en.toml             # Английский язык
└── ru.toml             # Русский язык
```

### Принципы работы
1. **Автоопределение языка**: система определяет язык из Telegram
2. **Fallback механизм**: при отсутствии перевода используется русский
3. **Кэширование**: переводы кэшируются в памяти
4. **Динамическое обновление**: поддержка hot-reload переводов

## 📝 Формат файлов переводов

### Структура TOML файла
```toml
# app/i18n/ru.toml
[common]
start = "Добро пожаловать в School Bot! 🎓"
help = "Помощь по использованию бота"
rate_limited = "Слишком много запросов. Попробуйте позже."

[roles]
student = "Ученик"
teacher = "Учитель"
parent = "Родитель"
director = "Директор"
admin = "Администратор"

[errors]
not_found = "Запрашиваемая информация не найдена"
permission_denied = "У вас нет прав для выполнения этого действия"
invalid_input = "Неверный формат данных"
```

### Правила именования ключей
- **Иерархическая структура**: `section.subsection.key`
- **Описательные имена**: `user.profile.updated`
- **Консистентность**: одинаковые ключи во всех языках
- **Группировка**: логическое разделение по функциональности

## 🔧 Использование в коде

### 1. **Импорт функции перевода**
```python
from app.i18n import t

# Простой перевод
message = t("common.start", lang)

# Перевод с параметрами
message = t("user.welcome", lang, name=user.name)
```

### 2. **Получение языка пользователя**
```python
from app.middlewares.locale import get_user_language

# В обработчике
async def some_handler(message: Message, user: User):
    lang = get_user_language(user)
    response = t("common.help", lang)
    await message.answer(response)
```

### 3. **Работа с клавиатурами**
```python
from app.keyboards.main_menu import get_main_menu

async def show_main_menu(message: Message, user: User):
    lang = get_user_language(user)
    keyboard = get_main_menu(lang)
    await message.answer(t("menu.main", lang), reply_markup=keyboard)
```

## 📚 Добавление нового языка

### 1. **Создание файла перевода**
```bash
# Создать новый файл
touch app/i18n/en.toml
```

### 2. **Структура нового файла**
```toml
# app/i18n/en.toml
[common]
start = "Welcome to School Bot! 🎓"
help = "Help on bot usage"
rate_limited = "Too many requests. Try again later."

[roles]
student = "Student"
teacher = "Teacher"
parent = "Parent"
director = "Director"
admin = "Administrator"

[errors]
not_found = "Requested information not found"
permission_denied = "You don't have permission to perform this action"
invalid_input = "Invalid data format"
```

### 3. **Регистрация языка**
```python
# app/i18n/__init__.py
SUPPORTED_LANGUAGES = {
    "ru": "Русский",
    "en": "English",
    # Добавить новый язык
    "es": "Español"
}
```

### 4. **Добавление в middleware**
```python
# app/middlewares/locale.py
async def get_user_language(user: User) -> str:
    """Получить язык пользователя"""
    if user.language in SUPPORTED_LANGUAGES:
        return user.language
    return "ru"  # Fallback на русский
```

## 🛠️ Best Practices

### 1. **Никогда не хардкодить текст**
```python
# ❌ Плохо
await message.answer("Добро пожаловать!")

# ✅ Хорошо
await message.answer(t("common.welcome", lang))
```

### 2. **Использовать консистентные ключи**
```python
# ❌ Плохо
t("welcome_message", lang)
t("greeting", lang)

# ✅ Хорошо
t("common.welcome", lang)
t("common.greeting", lang)
```

### 3. **Группировать связанные переводы**
```toml
# ✅ Хорошо
[user]
profile = "Профиль"
settings = "Настройки"
logout = "Выйти"

[task]
create = "Создать задачу"
edit = "Редактировать задачу"
delete = "Удалить задачу"
```

### 4. **Использовать параметры для динамического контента**
```python
# В коде
message = t("task.assigned", lang, task=task.title, user=user.name)

# В TOML
task.assigned = "Задача '{task}' назначена пользователю {user}"
```

## 🔍 Проверка переводов

### 1. **Автоматическая проверка**
```bash
# Скрипт для проверки консистентности
python scripts/check_translations.py
```

### 2. **Ручная проверка**
```python
# Проверить все ключи
from app.i18n import check_translations

missing_keys = check_translations()
if missing_keys:
    print("Missing translations:", missing_keys)
```

### 3. **Валидация структуры**
```python
# Проверить структуру TOML файлов
import tomllib

def validate_toml_structure():
    with open("app/i18n/ru.toml", "rb") as f:
        data = tomllib.load(f)
    # Проверка структуры
```

## 📊 Статистика переводов

### Текущие языки:
- **Русский (ru)**: 100% покрытие
- **Английский (en)**: 85% покрытие
- **Испанский (es)**: 60% покрытие (в разработке)

### Ключевые секции:
- `common`: 50 ключей
- `roles`: 5 ключей
- `errors`: 15 ключей
- `menu`: 30 ключей
- `tasks`: 25 ключей
- `notes`: 20 ключей

## 🔧 Конфигурация

### Переменные окружения:
```env
# Язык по умолчанию
DEFAULT_LANGUAGE=ru

# Поддерживаемые языки
SUPPORTED_LANGUAGES=ru,en,es

# Автоопределение языка
AUTO_DETECT_LANGUAGE=true
```

### Настройка в коде:
```python
# app/config.py
class Config:
    DEFAULT_LANGUAGE: str = "ru"
    SUPPORTED_LANGUAGES: List[str] = ["ru", "en", "es"]
    AUTO_DETECT_LANGUAGE: bool = True
```

## 🚀 Производительность

### 1. **Кэширование**
```python
# Переводы кэшируются в памяти
_translation_cache = {}

def get_translation(key: str, lang: str) -> str:
    cache_key = f"{lang}:{key}"
    if cache_key not in _translation_cache:
        _translation_cache[cache_key] = load_translation(key, lang)
    return _translation_cache[cache_key]
```

### 2. **Lazy Loading**
```python
# Переводы загружаются по требованию
def load_translation(key: str, lang: str) -> str:
    if lang not in _loaded_languages:
        _loaded_languages[lang] = load_language_file(lang)
    return _loaded_languages[lang].get(key, key)
```

## 🔄 Обновление переводов

### 1. **Hot Reload**
```python
# Автоматическое обновление при изменении файлов
def reload_translations():
    global _loaded_languages
    _loaded_languages.clear()
    _translation_cache.clear()
```

### 2. **Версионирование**
```python
# Версионирование переводов
TRANSLATION_VERSION = "1.0.0"

def get_translation_version() -> str:
    return TRANSLATION_VERSION
```

## 📋 Чек-лист для переводчиков

### ✅ Обязательные проверки:
- [ ] Все ключи присутствуют во всех языках
- [ ] Нет хардкода текста в коде
- [ ] Параметры в переводах соответствуют коду
- [ ] Грамматика и пунктуация корректны
- [ ] Контекст перевода понятен

### ✅ Рекомендации:
- [ ] Использовать профессионального переводчика
- [ ] Проверять переводы носителями языка
- [ ] Учитывать культурные особенности
- [ ] Тестировать на реальных пользователях

---

**Дата создания**: $(date)  
**Версия**: 1.0  
**Статус**: ✅ Актуально
