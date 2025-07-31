#!/bin/bash
set -euo pipefail

# Скрипт для проверки готовности к продакшену
# Использование: ./scripts/production_checklist.sh

echo "🔍 Проверка готовности к продакшену"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода статуса
print_status() {
    local status="$1"
    local message="$2"
    if [[ "$status" == "OK" ]]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [[ "$status" == "WARNING" ]]; then
        echo -e "${YELLOW}⚠️ $message${NC}"
    else
        echo -e "${RED}❌ $message${NC}"
    fi
}

# Функция для проверки файлов
check_file_exists() {
    local file="$1"
    local description="$2"
    if [[ -f "$file" ]]; then
        print_status "OK" "$description"
    else
        print_status "ERROR" "$description (файл не найден)"
    fi
}

# Функция для проверки переменных окружения
check_env_variable() {
    local var="$1"
    local description="$2"
    if grep -q "^${var}=" .env 2>/dev/null; then
        print_status "OK" "$description"
    else
        print_status "WARNING" "$description (не настроена)"
    fi
}

# Функция для проверки секретов в коде
check_secrets_in_code() {
    echo "🔐 Проверка секретов в коде..."

    # Проверяем наличие токенов в коде
    if grep -r "BOT_TOKEN\|TELEGRAM_TOKEN" app/ --exclude-dir=__pycache__ 2>/dev/null | grep -v "env\|config"; then
        print_status "ERROR" "Найдены токены в коде"
    else
        print_status "OK" "Токены не найдены в коде"
    fi

    # Проверяем наличие паролей в коде
    if grep -r "password\|secret" app/ --exclude-dir=__pycache__ 2>/dev/null | grep -v "env\|config\|hash"; then
        print_status "ERROR" "Найдены пароли в коде"
    else
        print_status "OK" "Пароли не найдены в коде"
    fi
}

# Функция для проверки .gitignore
check_gitignore() {
    echo "📁 Проверка .gitignore..."

    if grep -q "\.env" .gitignore; then
        print_status "OK" ".env в .gitignore"
    else
        print_status "ERROR" ".env не в .gitignore"
    fi

    if grep -q "__pycache__" .gitignore; then
        print_status "OK" "__pycache__ в .gitignore"
    else
        print_status "WARNING" "__pycache__ не в .gitignore"
    fi

    if grep -q "venv" .gitignore; then
        print_status "OK" "venv в .gitignore"
    else
        print_status "WARNING" "venv не в .gitignore"
    fi
}

# Функция для проверки конфигурации
check_configuration() {
    echo "⚙️ Проверка конфигурации..."

    # Проверяем переменные окружения
    check_env_variable "TELEGRAM_TOKEN" "TELEGRAM_TOKEN"
    check_env_variable "POSTGRES_PASSWORD" "POSTGRES_PASSWORD"
    check_env_variable "POSTGRES_DB" "POSTGRES_DB"
    check_env_variable "POSTGRES_USER" "POSTGRES_USER"

    # Проверяем опциональные переменные
    check_env_variable "GLITCHTIP_DSN" "GLITCHTIP_DSN (опционально)"
    check_env_variable "TELEGRAM_BOT_TOKEN" "TELEGRAM_BOT_TOKEN (опционально)"
    check_env_variable "TELEGRAM_CHAT_ID" "TELEGRAM_CHAT_ID (опционально)"
}

# Функция для проверки миграций
check_migrations() {
    echo "🗄️ Проверка миграций..."

    if [[ -d "alembic/versions" ]]; then
        local migration_count=$(ls alembic/versions/*.py 2>/dev/null | wc -l)
        if [[ $migration_count -gt 0 ]]; then
            print_status "OK" "Миграции найдены ($migration_count файлов)"
        else
            print_status "WARNING" "Папка миграций пуста"
        fi
    else
        print_status "ERROR" "Папка миграций не найдена"
    fi

    if [[ -f "alembic.ini" ]]; then
        print_status "OK" "alembic.ini найден"
    else
        print_status "ERROR" "alembic.ini не найден"
    fi
}

# Функция для проверки тестов
check_tests() {
    echo "🧪 Проверка тестов..."

    if [[ -d "tests" ]]; then
        local test_count=$(find tests -name "test_*.py" | wc -l)
        if [[ $test_count -gt 0 ]]; then
            print_status "OK" "Тесты найдены ($test_count файлов)"
        else
            print_status "WARNING" "Тесты не найдены"
        fi
    else
        print_status "ERROR" "Папка tests не найдена"
    fi

    # Проверяем наличие основных тестов
    check_file_exists "tests/test_security.py" "Тесты безопасности"
    check_file_exists "tests/test_basic.py" "Базовые тесты"
}

# Функция для проверки документации
check_documentation() {
    echo "📚 Проверка документации..."

    check_file_exists "README.md" "README.md"
    check_file_exists "LICENSE" "LICENSE"
    check_file_exists "CHANGELOG.md" "CHANGELOG.md"
    check_file_exists "SECURITY.md" "SECURITY.md"
    check_file_exists "DEVOPS_GUIDE.md" "DEVOPS_GUIDE.md"
    check_file_exists "QUICK_START.md" "QUICK_START.md"
}

# Функция для проверки мониторинга
check_monitoring() {
    echo "📊 Проверка мониторинга..."

    check_file_exists "docker-compose.yml" "docker-compose.yml"
    check_file_exists "prometheus/prometheus.yml" "Конфигурация Prometheus"
    check_file_exists "prometheus/rules.yml" "Правила алертов"
    check_file_exists "alertmanager/alertmanager.yml" "Конфигурация Alertmanager"
    check_file_exists "grafana/provisioning/dashboards/dashboards.yml" "Конфигурация Grafana"
}

# Функция для проверки скриптов
check_scripts() {
    echo "🛠️ Проверка скриптов..."

    check_file_exists "scripts/deploy.sh" "Скрипт деплоя"
    check_file_exists "scripts/backup.sh" "Скрипт бэкапа"
    check_file_exists "scripts/restore.sh" "Скрипт восстановления"
    check_file_exists "scripts/init_monitoring.sh" "Скрипт инициализации мониторинга"
    check_file_exists "scripts/scale.sh" "Скрипт масштабирования"

    # Проверяем исполняемость скриптов
    if [[ -x "scripts/deploy.sh" ]]; then
        print_status "OK" "Скрипт deploy.sh исполняемый"
    else
        print_status "WARNING" "Скрипт deploy.sh не исполняемый"
    fi
}

# Функция для проверки демо-данных
check_demo_data() {
    echo "🎭 Проверка демо-данных..."

    if grep -r "teacher\|student\|admin" scripts/init_demo.py 2>/dev/null; then
        print_status "WARNING" "Демо-аккаунты с простыми паролями"
        echo "   Рекомендация: Измените пароли демо-аккаунтов перед продакшеном"
    else
        print_status "OK" "Демо-аккаунты не найдены"
    fi
}

# Функция для проверки производительности
check_performance() {
    echo "⚡ Проверка производительности..."

    # Проверяем наличие health check
    if grep -r "health" app/health.py 2>/dev/null; then
        print_status "OK" "Health check реализован"
    else
        print_status "WARNING" "Health check не найден"
    fi

    # Проверяем наличие метрик
    if grep -r "prometheus" app/middlewares/metrics.py 2>/dev/null; then
        print_status "OK" "Метрики Prometheus настроены"
    else
        print_status "WARNING" "Метрики Prometheus не найдены"
    fi
}

# Функция для проверки безопасности
check_security() {
    echo "🔒 Проверка безопасности..."

    # Проверяем CSRF защиту
    if grep -r "csrf" app/utils/csrf.py 2>/dev/null; then
        print_status "OK" "CSRF защита реализована"
    else
        print_status "WARNING" "CSRF защита не найдена"
    fi

    # Проверяем rate limiting
    if grep -r "rate.*limit" app/middlewares/ 2>/dev/null; then
        print_status "OK" "Rate limiting настроен"
    else
        print_status "WARNING" "Rate limiting не найден"
    fi

    # Проверяем валидацию ввода
    if grep -r "pydantic\|validation" app/ 2>/dev/null; then
        print_status "OK" "Валидация ввода настроена"
    else
        print_status "WARNING" "Валидация ввода не найдена"
    fi
}

# Функция для финальной оценки
final_assessment() {
    echo ""
    echo "📋 Финальная оценка готовности к продакшену:"
    echo ""

    local total_checks=0
    local passed_checks=0
    local warnings=0
    local errors=0

    # Подсчитываем результаты (упрощенная версия)
    if [[ -f ".env" ]]; then ((passed_checks++)); else ((errors++)); fi
    ((total_checks++))

    if [[ -f "docker-compose.yml" ]]; then ((passed_checks++)); else ((errors++)); fi
    ((total_checks++))

    if [[ -d "tests" ]]; then ((passed_checks++)); else ((warnings++)); fi
    ((total_checks++))

    if [[ -f "LICENSE" ]]; then ((passed_checks++)); else ((warnings++)); fi
    ((total_checks++))

    if [[ -f "README.md" ]]; then ((passed_checks++)); else ((warnings++)); fi
    ((total_checks++))

    local success_rate=$((passed_checks * 100 / total_checks))

    echo "📊 Результаты:"
    echo "   Всего проверок: $total_checks"
    echo "   Успешно: $passed_checks"
    echo "   Предупреждения: $warnings"
    echo "   Ошибки: $errors"
    echo "   Процент готовности: $success_rate%"

    if [[ $success_rate -ge 90 ]]; then
        print_status "OK" "Проект готов к продакшену! 🎉"
    elif [[ $success_rate -ge 70 ]]; then
        print_status "WARNING" "Проект почти готов, требуется доработка"
    else
        print_status "ERROR" "Проект не готов к продакшену"
    fi
}

# Функция для рекомендаций
show_recommendations() {
    echo ""
    echo "💡 Рекомендации для продакшена:"
    echo ""
    echo "1. 🔐 Безопасность:"
    echo "   • Измените пароли демо-аккаунтов"
    echo "   • Настройте HTTPS для веб-интерфейсов"
    echo "   • Включите firewall на сервере"
    echo ""
    echo "2. 📊 Мониторинг:"
    echo "   • Настройте алерты в Telegram"
    echo "   • Проверьте дашборды Grafana"
    echo "   • Настройте логирование"
    echo ""
    echo "3. 🗄️ База данных:"
    echo "   • Создайте бэкап перед деплоем"
    echo "   • Примените все миграции"
    echo "   • Настройте регулярные бэкапы"
    echo ""
    echo "4. 🚀 Деплой:"
    echo "   • Протестируйте на staging окружении"
    echo "   • Подготовьте план отката"
    echo "   • Настройте CI/CD pipeline"
    echo ""
    echo "5. 📚 Документация:"
    echo "   • Обновите README с инструкциями"
    echo "   • Создайте Wiki для команды"
    echo "   • Подготовьте runbook для инцидентов"
}

# Основной процесс
main() {
    echo "🔍 Начинаем проверку готовности к продакшену..."
    echo ""

    check_secrets_in_code
    check_gitignore
    check_configuration
    check_migrations
    check_tests
    check_documentation
    check_monitoring
    check_scripts
    check_demo_data
    check_performance
    check_security

    final_assessment
    show_recommendations

    echo ""
    echo "🎯 Следующие шаги:"
    echo "1. Исправьте все найденные ошибки"
    echo "2. Обратите внимание на предупреждения"
    echo "3. Протестируйте на staging окружении"
    echo "4. Подготовьте план деплоя"
    echo "5. Настройте мониторинг и алерты"
}

# Запуск основного процесса
main "$@"
