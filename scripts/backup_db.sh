#!/bin/bash
# Автоматическое резервное копирование базы данных SchoolBot

set -e

# Конфигурация
BACKUP_DIR="${BACKUP_DIR:-/var/backups/schoolbot}"
CONTAINER_NAME="${CONTAINER_NAME:-present-bot-postgres}"
DB_NAME="${DB_NAME:-schoolbot}"
DB_USER="${DB_USER:-schoolbot}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Цветовая схема
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции для вывода
error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Функция показа помощи
show_help() {
    echo "Использование: $0 [ОПЦИИ]"
    echo ""
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -d, --dir DIR           Директория для бэкапов (по умолчанию: /var/backups/schoolbot)"
    echo "  -c, --container NAME    Имя контейнера PostgreSQL (по умолчанию: present-bot-postgres)"
    echo "  -n, --db-name NAME      Имя базы данных (по умолчанию: schoolbot)"
    echo "  -u, --db-user USER      Пользователь БД (по умолчанию: schoolbot)"
    echo "  -r, --retention DAYS    Дни хранения бэкапов (по умолчанию: 7)"
    echo "  --restore FILE          Восстановить БД из файла"
    echo "  --list                  Показать список доступных бэкапов"
    echo "  --cleanup               Удалить старые бэкапы"
    echo ""
    echo "Примеры:"
    echo "  $0                                    # Создать бэкап"
    echo "  $0 --restore backup_20241206.sql.gz  # Восстановить из бэкапа"
    echo "  $0 --list                             # Показать список бэкапов"
    echo "  $0 --cleanup                          # Очистить старые бэкапы"
}

# Парсинг аргументов командной строки
RESTORE_FILE=""
LIST_BACKUPS=false
CLEANUP_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -c|--container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -n|--db-name)
            DB_NAME="$2"
            shift 2
            ;;
        -u|--db-user)
            DB_USER="$2"
            shift 2
            ;;
        -r|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --restore)
            RESTORE_FILE="$2"
            shift 2
            ;;
        --list)
            LIST_BACKUPS=true
            shift
            ;;
        --cleanup)
            CLEANUP_ONLY=true
            shift
            ;;
        *)
            error "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
done

# Проверка существования Docker контейнера
check_container() {
    if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        error "Контейнер '$CONTAINER_NAME' не запущен"
        echo ""
        info "Доступные контейнеры:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        exit 1
    fi
    success "Контейнер '$CONTAINER_NAME' найден и запущен"
}

# Создание директории для бэкапов
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        info "Создание директории для бэкапов: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
        chmod 750 "$BACKUP_DIR"
    fi
    success "Директория для бэкапов готова: $BACKUP_DIR"
}

# Функция для создания бэкапа
create_backup() {
    local DATE=$(date +%Y%m%d_%H%M%S)
    local BACKUP_FILE="$BACKUP_DIR/schoolbot_backup_$DATE.sql"
    local COMPRESSED_FILE="$BACKUP_FILE.gz"
    
    info "Создание бэкапа базы данных..."
    info "Контейнер: $CONTAINER_NAME"
    info "База данных: $DB_NAME"
    info "Пользователь: $DB_USER"
    info "Файл: $COMPRESSED_FILE"
    
    # Создание дампа
    if docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --verbose > "$BACKUP_FILE" 2>/dev/null; then
        success "Дамп базы данных создан: $BACKUP_FILE"
        
        # Сжатие файла
        info "Сжатие бэкапа..."
        if gzip "$BACKUP_FILE"; then
            success "Бэкап сжат: $COMPRESSED_FILE"
            
            # Информация о размере файла
            local SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
            success "Размер сжатого бэкапа: $SIZE"
            
            # Проверка целостности
            info "Проверка целостности архива..."
            if gunzip -t "$COMPRESSED_FILE" 2>/dev/null; then
                success "Архив корректен"
            else
                error "Архив поврежден!"
                rm -f "$COMPRESSED_FILE"
                exit 1
            fi
            
        else
            error "Ошибка сжатия бэкапа"
            rm -f "$BACKUP_FILE"
            exit 1
        fi
    else
        error "Ошибка создания дампа базы данных"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
    
    info "Бэкап успешно создан: $COMPRESSED_FILE"
}

# Функция восстановления из бэкапа
restore_backup() {
    local restore_file="$1"
    
    # Проверка существования файла
    if [[ ! -f "$restore_file" ]]; then
        error "Файл бэкапа не найден: $restore_file"
        exit 1
    fi
    
    info "Восстановление базы данных из: $restore_file"
    
    # Определение типа файла (сжатый или нет)
    if [[ "$restore_file" == *.gz ]]; then
        info "Восстановление из сжатого архива..."
        
        # Проверка целостности архива
        if ! gunzip -t "$restore_file" 2>/dev/null; then
            error "Архив поврежден: $restore_file"
            exit 1
        fi
        
        # Восстановление
        if gunzip -c "$restore_file" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"; then
            success "База данных восстановлена из сжатого архива"
        else
            error "Ошибка восстановления из сжатого архива"
            exit 1
        fi
    else
        info "Восстановление из обычного SQL файла..."
        if docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$restore_file"; then
            success "База данных восстановлена из SQL файла"
        else
            error "Ошибка восстановления из SQL файла"
            exit 1
        fi
    fi
}

# Функция показа списка бэкапов
list_backups() {
    info "Доступные бэкапы в $BACKUP_DIR:"
    echo ""
    
    if [[ ! -d "$BACKUP_DIR" ]] || [[ -z "$(ls -A "$BACKUP_DIR")" ]]; then
        warn "Бэкапы не найдены"
        return
    fi
    
    # Заголовок таблицы
    printf "%-30s %-12s %-20s\n" "Файл" "Размер" "Дата создания"
    printf "%-30s %-12s %-20s\n" "----" "------" "-------------"
    
    # Список файлов с информацией
    find "$BACKUP_DIR" -name "schoolbot_backup_*.sql*" -type f -printf "%f\t%s\t%TY-%Tm-%Td %TH:%TM\n" | \
    sort -r | \
    while IFS=$'\t' read -r filename size date; do
        # Конвертация размера в человекочитаемый формат
        if [[ $size -gt 1073741824 ]]; then
            size_human="$(( size / 1073741824 ))GB"
        elif [[ $size -gt 1048576 ]]; then
            size_human="$(( size / 1048576 ))MB"
        elif [[ $size -gt 1024 ]]; then
            size_human="$(( size / 1024 ))KB"
        else
            size_human="${size}B"
        fi
        
        printf "%-30s %-12s %-20s\n" "$filename" "$size_human" "$date"
    done
}

# Функция очистки старых бэкапов
cleanup_old_backups() {
    info "Очистка бэкапов старше $RETENTION_DAYS дней..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        warn "Директория бэкапов не существует: $BACKUP_DIR"
        return
    fi
    
    # Поиск и удаление старых файлов
    local deleted_count=0
    while IFS= read -r -d '' file; do
        info "Удаляется старый бэкап: $(basename "$file")"
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR" -name "schoolbot_backup_*.sql*" -type f -mtime +$RETENTION_DAYS -print0)
    
    if [[ $deleted_count -eq 0 ]]; then
        success "Старые бэкапы не найдены"
    else
        success "Удалено $deleted_count старых бэкапов"
    fi
    
    # Показать оставшиеся бэкапы
    local remaining_count=$(find "$BACKUP_DIR" -name "schoolbot_backup_*.sql*" -type f | wc -l)
    info "Осталось бэкапов: $remaining_count"
}

# Основная логика
main() {
    echo "🗄️ SchoolBot Database Backup Manager"
    echo "====================================="
    
    # Проверка аргументов
    if [[ "$LIST_BACKUPS" == true ]]; then
        list_backups
        exit 0
    fi
    
    if [[ "$CLEANUP_ONLY" == true ]]; then
        cleanup_old_backups
        exit 0
    fi
    
    if [[ -n "$RESTORE_FILE" ]]; then
        warn "ВНИМАНИЕ: Восстановление перезапишет текущую базу данных!"
        echo -n "Продолжить? (y/N): "
        read -r confirmation
        if [[ "$confirmation" != "y" ]] && [[ "$confirmation" != "Y" ]]; then
            info "Операция отменена"
            exit 0
        fi
        
        check_container
        restore_backup "$RESTORE_FILE"
        exit 0
    fi
    
    # Обычное создание бэкапа
    check_container
    create_backup_dir
    create_backup
    cleanup_old_backups
    
    # Итоговая информация
    echo ""
    success "🎉 Операция бэкапа завершена успешно!"
    info "Для восстановления используйте: $0 --restore <файл>"
    info "Для просмотра бэкапов: $0 --list"
}

# Запуск основной функции
main "$@"
