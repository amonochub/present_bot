# UX Система - Светлая/Тёмная тема + Адаптивные эмодзи

Система переключения тем с адаптивными эмодзи для улучшения пользовательского опыта.

## 🌗 Темы

### Доступные темы

| Тема | Описание | Эмодзи стиль |
|------|----------|--------------|
| `light` | Светлая тема (по умолчанию) | Классические эмодзи |
| `dark` | Тёмная тема | Альтернативные эмодзи |

### Переключение темы

#### Команда /theme
```bash
# В Telegram
/theme
```

#### Кнопка "🌗 Тема"
- Доступна во всех меню
- Переключает тему одним нажатием
- Сохраняет выбор в БД

## 🎨 Адаптивные эмодзи

### Светлая тема (light)

| Функция | Эмодзи | Описание |
|---------|--------|----------|
| Заметки | 📝 | Классическая записная книжка |
| Добавить | ➕ | Плюс для добавления |
| Заявки | 🛠 | Инструменты |
| Медиа | 📹 | Видеокамера |
| Рассылка | 📢 | Мегафон |
| Задания | 📋 | Клипборд |
| Психолог | 🆘 | SOS |

### Тёмная тема (dark)

| Функция | Эмодзи | Описание |
|---------|--------|----------|
| Заметки | 📜 | Свиток (более тёмный) |
| Добавить | ➕ | Плюс (без изменений) |
| Заявки | 🔧 | Гаечный ключ |
| Медиа | 🎥 | Киноплёнка |
| Рассылка | 📢 | Мегафон (без изменений) |
| Задания | 📋 | Клипборд (без изменений) |
| Психолог | 🆘 | SOS (без изменений) |
| Тема | ☀️ | Солнце (вместо 🌗) |

## 💾 Хранение настроек

### База данных

```sql
-- Поле theme в таблице users
ALTER TABLE users ADD COLUMN theme VARCHAR DEFAULT 'light';
```

### Модель User

```python
# app/db/user.py
class User(Base, TimestampMixin):
    # ... другие поля ...
    theme = Column(String, default="light")  # 'light' | 'dark'
```

## 🔄 Переключение темы

### Функция toggle_theme()

```python
# app/handlers/theme.py
async def toggle_theme(uid: int) -> str:
    async with AsyncSessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == uid))
        new = "dark" if user.theme == "light" else "light"
        await s.execute(update(User).where(User.id == user.id).values(theme=new))
        await s.commit()
        return new
```

### Обработчики

```python
@router.message(Command("theme"))
async def cmd_theme(msg: Message, lang: str):
    new = await toggle_theme(msg.from_user.id)
    # Обновляет меню с новой темой

@router.callback_query(lambda c: c.data == "switch_theme")
async def cb_theme(call: CallbackQuery, lang: str):
    new = await toggle_theme(call.from_user.id)
    # Обновляет текущее меню
```

## 🎯 Клавиатуры с темами

### Фабрика эмодзи

```python
# app/keyboards/main_menu.py
EMOJI = {
    "light": {
        "teacher_notes": "📝",
        "teacher_add": "➕",
        # ... другие эмодзи
    },
    "dark": {
        "teacher_notes": "📜",
        "teacher_add": "➕",
        # ... альтернативные эмодзи
    },
}
```

### Использование в меню

```python
def menu(role: str, lang="ru", theme="light", nonce="") -> InlineKeyboardMarkup:
    e = EMOJI[theme]  # Получаем эмодзи для темы
    
    if role == "teacher":
        kb = [
            [InlineKeyboardButton(
                text=f"{e['teacher_notes']} {t('teacher.menu_notes', lang)}",
                callback_data=f"{nonce}:teacher_notes"
            )],
            # ... другие кнопки
        ]
```

## 🌐 Локализация

### Русский (ru.toml)

```toml
[common]
theme_switched = "🌗 Тема переключена!"
```

### Английский (en.toml)

```toml
[common]
theme_switched = "🌗 Theme switched!"
```

## 🔧 Интеграция

### Передача темы в меню

```python
# Везде, где вызывается menu()
await m.answer(text, reply_markup=menu(user.role, lang, user.theme))
```

### Обновление при переключении ролей

```python
# При переключении роли сохраняется тема
await call.message.edit_text(
    text,
    reply_markup=menu(role_target, lang, user.theme)
)
```

## 🧪 Тестирование

### Проверка переключения

1. **Команда /theme**:
   ```bash
   /theme
   ```
   - Эмодзи меняются
   - Сообщение "🌗 Тема переключена!"

2. **Кнопка "🌗 Тема"**:
   - Работает в любом меню
   - Обновляет текущее меню

3. **Сохранение в БД**:
   ```sql
   SELECT theme FROM users WHERE tg_id = YOUR_ID;
   ```

4. **Переключение ролей**:
   - Тема сохраняется при смене роли
   - Эмодзи адаптируются к теме

## 📊 Миграция

### Создание миграции

```bash
python manage.py makemigrations "add_user_theme"
```

### Применение

```bash
python manage.py migrate
```

### Файл миграции

```python
# migrations/versions/003_add_user_theme.py
def upgrade() -> None:
    op.add_column('users', sa.Column('theme', sa.String(), server_default='light'))

def downgrade() -> None:
    op.drop_column('users', 'theme')
```

## 🎨 Расширение тем

### Добавление новой темы

1. **Добавить эмодзи**:
   ```python
   EMOJI["neon"] = {
       "teacher_notes": "✨",
       "teacher_add": "⚡",
       # ... новые эмодзи
   }
   ```

2. **Обновить toggle_theme()**:
   ```python
   def get_next_theme(current: str) -> str:
       themes = ["light", "dark", "neon"]
       current_idx = themes.index(current)
       return themes[(current_idx + 1) % len(themes)]
   ```

3. **Добавить в БД**:
   ```sql
   ALTER TABLE users ADD CONSTRAINT check_theme 
   CHECK (theme IN ('light', 'dark', 'neon'));
   ```

## 🎯 Результат

После внедрения UX системы:

- ✅ **Одно нажатие** - переключение всех меню
- ✅ **Сохранение в БД** - настройки не сбрасываются
- ✅ **Адаптивные эмодзи** - разные стили для тем
- ✅ **Локализация** - сообщения на двух языках
- ✅ **Интеграция** - работает во всех частях бота
- ✅ **Расширяемость** - легко добавить новые темы

**UX система тем полностью реализована!** 🌗 