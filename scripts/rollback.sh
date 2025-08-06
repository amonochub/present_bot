#!/bin/bash
# Скрипт отката развертывания SchoolBot

set -e

echo "🔄 Откат развертывания SchoolBot"
echo "================================"

# Цветовая схема
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфигурация
DEPLOY_DIR="${DEPLOY_DIR:-/opt/schoolbot}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/schoolbot}"
LOG_FILE="${LOG_FILE:-/var/log/schoolbot/rollback.log}"

# Функции для вывода
error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Функция показа помощи
show_help() {
    echo "Использование: $0 [ОПЦИИ]"
    echo ""
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -d, --dir DIR           Директория развертывания"
    echo "  -r, --revisions NUM     Количество коммитов для отката (по умолчанию: 1)"
    echo "  --backup FILE           Восстановить из конкретного бэкапа"
    echo "  --force                 Принудительный откат без подтверждения"
    echo "  --list-backups          Показать доступные бэкапы"
    echo ""
    echo "Примеры:"
    echo "  $0                                    # Откат на 1 коммит назад"
    echo "  $0 -r 3                              # Откат на 3 коммита назад"
    echo "  $0 --backup backup_20241206.tar.gz   # Восстановление из бэкапа"
    echo "  $0 --list-backups                    # Показать доступные бэкапы"
}

# Парсинг аргументов
REVISIONS=1
BACKUP_FILE=""
FORCE_ROLLBACK=false
LIST_BACKUPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dir)
            DEPLOY_DIR="$2"
            shift 2
            ;;
        -r|--revisions)
            REVISIONS="$2"
            shift 2
            ;;
        --backup)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --force)
            FORCE_ROLLBACK=true
            shift
            ;;
        --list-backups)
            LIST_BACKUPS=true
            shift
            ;;
        *)
            error "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
done

# Создание директории для логов
mkdir -p "$(dirname "$LOG_FILE")"

# Логирование начала отката
{
    echo "==============================================="
    echo "Начало отката: $(date)"
    echo "Пользователь: $(whoami)"
    echo "Директория: $DEPLOY_DIR"
    echo "==============================================="
} >> "$LOG_FILE"

# Функция показа доступных бэкапов
list_available_backups() {
    info "Доступные бэкапы:"
    echo ""
    
    if [[ ! -d "$BACKUP_DIR" ]] || [[ -z "$(ls -A "$BACKUP_DIR")" ]]; then
        warn "Бэкапы не найдены в $BACKUP_DIR"
        return
    fi
    
    echo "База данных:"
    find "$BACKUP_DIR" -name "schoolbot_backup_*.sql.gz" -type f -printf "%f\t%TY-%Tm-%Td %TH:%TM\n" | sort -r | head -10
    
    echo ""
    echo "Файлы развертывания:"
    find "$BACKUP_DIR" -name "deployment_backup_*.tar.gz" -type f -printf "%f\t%TY-%Tm-%Td %TH:%TM\n" | sort -r | head -10
}

# Проверка состояния репозитория
check_repository_state() {
    if [[ ! -d "$DEPLOY_DIR/.git" ]]; then
        error "Git репозиторий не найден в $DEPLOY_DIR"
        exit 1
    fi
    
    cd "$DEPLOY_DIR"
    
    # Показать текущий коммит
    local current_commit=$(git rev-parse HEAD)
    local current_message=$(git log -1 --pretty=format:"%s")
    
    info "Текущий коммит: $current_commit"
    info "Сообщение: $current_message"
    
    # Показать коммиты для отката
    info "Коммиты для отката:"
    git log --oneline -n $((REVISIONS + 2))
}

# Подтверждение отката
confirm_rollback() {
    if [[ "$FORCE_ROLLBACK" == true ]]; then
        warn "Принудительный откат без подтверждения"
        return
    fi
    
    echo ""
    warn "ВНИМАНИЕ: Откат приведет к потере текущих изменений!"
    
    if [[ -n "$BACKUP_FILE" ]]; then
        warn "Будет восстановлен бэкап: $BACKUP_FILE"
    else
        warn "Будет выполнен откат на $REVISIONS коммитов назад"
    fi
    
    echo -n "Продолжить? (y/N): "
    read -r confirmation
    
    if [[ "$confirmation" != "y" ]] && [[ "$confirmation" != "Y" ]]; then
        info "Откат отменен"
        exit 0
    fi
}

# Остановка сервисов
stop_services() {
    info "Остановка сервисов..."
    
    cd "$DEPLOY_DIR"
    
    if [[ -f "docker-compose.yml" ]]; then
        docker compose down --timeout 30 || warn "Не удалось корректно остановить сервисы"
    fi
    
    success "Сервисы остановлены"
}

# Откат Git репозитория
rollback_git() {
    info "Откат Git репозитория..."
    
    cd "$DEPLOY_DIR"
    
    # Сохранение текущих изменений в stash
    if ! git diff --quiet || ! git diff --cached --quiet; then
        warn "Сохранение текущих изменений в stash..."
        git add -A
        git stash push -m "Rollback stash $(date)"
    fi
    
    # Выполнение отката
    info "Откат на $REVISIONS коммитов назад..."
    git reset --hard HEAD~$REVISIONS
    
    local new_commit=$(git rev-parse HEAD)
    local new_message=$(git log -1 --pretty=format:"%s")
    
    success "Откат выполнен"
    info "Новый коммит: $new_commit"
    info "Сообщение: $new_message"
}

# Восстановление из бэкапа файлов
restore_from_backup() {
    local backup_file="$1"
    
    info "Восстановление из бэкапа: $backup_file"
    
    # Проверка существования файла
    if [[ ! -f "$backup_file" ]]; then
        error "Файл бэкапа не найден: $backup_file"
        exit 1
    fi
    
    # Создание резервной копии текущего состояния
    local current_backup="$BACKUP_DIR/pre_rollback_$(date +%Y%m%d_%H%M%S).tar.gz"
    info "Создание резервной копии текущего состояния: $current_backup"
    
    tar -czf "$current_backup" -C "$(dirname "$DEPLOY_DIR")" "$(basename "$DEPLOY_DIR")" 2>/dev/null || warn "Не удалось создать резервную копию"
    
    # Восстановление из бэкапа
    info "Извлечение бэкапа..."
    
    # Временная директория для извлечения
    local temp_dir=$(mktemp -d)
    
    if tar -xzf "$backup_file" -C "$temp_dir"; then
        # Замена текущего развертывания
        rm -rf "$DEPLOY_DIR"
        mv "$temp_dir/$(basename "$DEPLOY_DIR")" "$DEPLOY_DIR"
        rmdir "$temp_dir"
        
        success "Файлы восстановлены из бэкапа"
    else
        error "Ошибка извлечения бэкапа"
        rmdir "$temp_dir"
        exit 1
    fi
}

# Восстановление базы данных из бэкапа
restore_database() {
    info "Поиск бэкапа базы данных..."
    
    # Находим последний бэкап БД
    local db_backup=$(find "$BACKUP_DIR" -name "schoolbot_backup_*.sql.gz" -type f | sort -r | head -1)
    
    if [[ -z "$db_backup" ]]; then
        warn "Бэкап базы данных не найден"
        return
    fi
    
    info "Найден бэкап БД: $(basename "$db_backup")"
    
    # Запуск PostgreSQL контейнера (если не запущен)
    cd "$DEPLOY_DIR"
    docker compose up -d postgres
    
    # Ожидание запуска PostgreSQL
    info "Ожидание запуска PostgreSQL..."
    sleep 10
    
    # Восстановление БД
    if [[ -f "./scripts/backup_db.sh" ]]; then
        bash ./scripts/backup_db.sh --restore "$db_backup"
    else
        warn "Скрипт восстановления БД не найден"
    fi
}

# Запуск сервисов после отката
start_services() {
    info "Запуск сервисов после отката..."
    
    cd "$DEPLOY_DIR"
    
    # Пересборка образов (на случай изменений в Dockerfile)
    info "Пересборка образов..."
    docker compose build
    
    # Запуск сервисов
    info "Запуск сервисов..."
    docker compose up -d
    
    success "Сервисы запущены"
}

# Проверка здоровья после отката
health_check() {
    info "Проверка здоровья сервисов после отката..."
    
    local max_attempts=20
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        info "Попытка $attempt/$max_attempts..."
        
        # Проверка запуска контейнеров
        if docker compose ps --format json | jq -r '.[].State' | grep -q "running"; then
            # Проверка health check endpoint (если есть)
            if curl -f http://localhost:8080/health &> /dev/null; then
                success "Сервисы работают корректно после отката"
                return 0
            fi
        fi
        
        sleep 15
        ((attempt++))
    done
    
    warn "Сервисы не прошли проверку здоровья"
    return 1
}

# Основная функция отката
main() {
    local start_time=$(date +%s)
    
    # Проверка параметров
    if [[ "$LIST_BACKUPS" == true ]]; then
        list_available_backups
        exit 0
    fi
    
    # Проверка состояния
    check_repository_state
    
    # Подтверждение
    confirm_rollback
    
    # Выполнение отката
    stop_services
    
    if [[ -n "$BACKUP_FILE" ]]; then
        # Восстановление из конкретного бэкапа
        restore_from_backup "$BACKUP_FILE"
        restore_database
    else
        # Откат Git репозитория
        rollback_git
    fi
    
    # Запуск сервисов
    start_services
    
    # Проверка здоровья
    if health_check; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        success "🎉 Откат выполнен успешно!"
        info "Время выполнения: ${duration} секунд"
        
        # Показать текущее состояние
        cd "$DEPLOY_DIR"
        local current_commit=$(git rev-parse HEAD)
        info "Текущий коммит: $current_commit"
        
        echo ""
        info "Состояние сервисов:"
        docker compose ps
        
        echo ""
        info "Для просмотра логов: docker compose logs -f"
        
    else
        error "Откат выполнен, но сервисы работают некорректно"
        warn "Проверьте логи: docker compose logs"
        exit 1
    fi
}

# Запуск основной функции
main "$@"
