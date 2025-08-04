#!/bin/bash

# Скрипт для настройки инструментов качества кода
# Использование: ./scripts/setup_quality.sh

set -e

echo "🔧 Настройка инструментов качества кода..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.11+"
    exit 1
fi

# Проверяем версию Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Требуется Python $REQUIRED_VERSION или выше. Текущая версия: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python версия: $PYTHON_VERSION"

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Обновляем pip
echo "⬆️ Обновление pip..."
pip install --upgrade pip

# Устанавливаем зависимости для разработки
echo "📦 Установка зависимостей для качества кода..."
pip install -r requirements.txt
pip install black ruff mypy bandit safety pre-commit pytest pytest-cov pytest-asyncio

# Устанавливаем pre-commit hooks
echo "🔗 Установка pre-commit hooks..."
pre-commit install

# Проверяем наличие необходимых файлов
echo "📋 Проверка конфигурационных файлов..."

REQUIRED_FILES=(
    ".pre-commit-config.yaml"
    "pyproject.toml"
    "pytest.ini"
    "requirements.txt"
    "env.example"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file найден"
    else
        echo "❌ $file не найден"
        exit 1
    fi
done

# Проверяем структуру проекта
echo "📁 Проверка структуры проекта..."

REQUIRED_DIRS=(
    "app"
    "app/routes"
    "app/db"
    "app/handlers"
    "app/keyboards"
    "app/middlewares"
    "app/repositories"
    "app/schemas"
    "app/services"
    "app/utils"
    "tests"
    "migrations"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir найден"
    else
        echo "❌ $dir не найден"
        exit 1
    fi
done

# Проверяем файлы локализации
echo "🌐 Проверка файлов локализации..."

LOCALE_FILES=(
    "app/i18n/ru.toml"
    "app/i18n/en.toml"
)

for file in "${LOCALE_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file найден"
    else
        echo "❌ $file не найден"
        exit 1
    fi
done

# Запускаем базовые проверки
echo "🔍 Запуск базовых проверок..."

# Проверка форматирования
echo "🎨 Проверка форматирования кода..."
black --check --diff . || {
    echo "❌ Код требует форматирования. Запустите: black ."
    exit 1
}

# Проверка линтера
echo "🔍 Проверка линтера..."
ruff check . || {
    echo "❌ Найдены ошибки линтера. Запустите: ruff check --fix ."
    exit 1
}

# Проверка типов
echo "📝 Проверка типизации..."
mypy app/ || {
    echo "⚠️ Найдены ошибки типизации"
}

# Проверка безопасности
echo "🔒 Проверка безопасности..."
bandit -r app/ || {
    echo "⚠️ Найдены потенциальные проблемы безопасности"
}

# Проверка зависимостей
echo "📦 Проверка уязвимостей в зависимостях..."
safety check || {
    echo "⚠️ Найдены уязвимости в зависимостях"
}

# Запуск тестов
echo "🧪 Запуск тестов..."
pytest tests/ -v --tb=short || {
    echo "❌ Тесты не прошли"
    exit 1
}

# Проверка покрытия
echo "📊 Проверка покрытия тестами..."
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80 || {
    echo "❌ Покрытие тестами ниже 80%"
    exit 1
}

# Проверка pre-commit
echo "🔗 Проверка pre-commit hooks..."
pre-commit run --all-files || {
    echo "❌ Pre-commit hooks не прошли"
    exit 1
}

echo ""
echo "🎉 Настройка инструментов качества кода завершена успешно!"
echo ""
echo "📋 Доступные команды:"
echo "  black .                    - форматирование кода"
echo "  ruff check --fix .         - проверка и исправление линтера"
echo "  mypy app/                  - проверка типизации"
echo "  bandit -r app/             - проверка безопасности"
echo "  safety check               - проверка уязвимостей зависимостей"
echo "  pytest tests/ -v           - запуск тестов"
echo "  pytest tests/ --cov=app    - запуск тестов с покрытием"
echo "  pre-commit run --all-files - запуск всех pre-commit hooks"
echo ""
echo "💡 Рекомендации:"
echo "  - Настройте IDE для автоматического форматирования"
echo "  - Используйте pre-commit hooks перед каждым коммитом"
echo "  - Регулярно обновляйте зависимости"
echo "  - Следите за покрытием тестами"
echo ""
echo "🚀 Готово к разработке!" 