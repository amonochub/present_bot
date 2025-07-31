# 🌐 Локализация SchoolBot

## Обзор

Бот поддерживает многоязычность через TOML-файлы. Автоматически определяется язык пользователя по настройкам Telegram.

## Структура

```
app/i18n/
├── __init__.py    # Утилиты локализации
├── ru.toml        # Русский язык
└── en.toml        # Английский язык
```

## Использование

### В коде

```python
from app.i18n import t

# Получение строки
message = t("common.start_welcome", lang)  # lang = "ru" или "en"

# С параметрами
message = t("teacher.ticket_created", lang).format(ticket_id=123)
```

### В обработчиках

```python
@router.callback_query(F.data == "teacher_notes")
async def teacher_notes(call: CallbackQuery, lang: str):
    await call.message.edit_text(
        t("teacher.notes_empty", lang),
        reply_markup=menu("teacher", lang)
    )
```

## Добавление нового языка

1. Скопируйте `ru.toml` → `es.toml`
2. Переведите все строки
3. Обновите `LocaleMiddleware` в `app/middlewares/locale.py`:

```python
if lang not in ("ru", "en", "es"):  # добавьте новый код
    lang = self.default
```

## Структура TOML-файлов

```toml
[common]
start_welcome = "👋 Добро пожаловать в SchoolBot!\nВведите логин:"
auth_success = "✅ Авторизация успешна!"

[teacher]
menu_notes = "📝 Мои заметки"
menu_add = "➕ Добавить заметку"

[student]
menu_notes = "📝 Мои заметки"
# ...
```

## Секции

- `common` - общие сообщения (авторизация, ошибки)
- `teacher` - интерфейс учителя
- `student` - интерфейс ученика
- `parent` - интерфейс родителя
- `psych` - интерфейс психолога
- `admin` - интерфейс администратора
- `director` - интерфейс директора
- `errors` - системные ошибки

## Middleware

`LocaleMiddleware` автоматически:
- Определяет язык из профиля Telegram
- Добавляет `lang` в контекст обработчиков
- Fallback на русский для неподдерживаемых языков

## Кэширование

Файлы локализации кэшируются в памяти. Для разработки используйте:

```python
from app.i18n import clear_cache
clear_cache()  # очистить кэш
```

## Тестирование

```bash
# Проверка работы локализации
python3 -c "from app.i18n import t; print(t('common.start_welcome', 'en'))"
```

## Лучшие практики

1. **Ключи**: используйте иерархию `section.key`
2. **Эмодзи**: сохраняйте эмодзи в переводах
3. **Параметры**: используйте `.format()` для динамических значений
4. **Fallback**: всегда проверяйте существование ключа
5. **Консистентность**: одинаковые фразы должны иметь одинаковые ключи
