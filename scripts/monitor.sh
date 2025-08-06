#!/bin/bash
# Мониторинг состояния SchoolBot

set -e

echo "📊 Мониторинг состояния SchoolBot"
echo "================================="

# Цветовая схема
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Конфигурация
DEPLOY_DIR="${DEPLOY_DIR:-/opt/schoolbot}"
LOG_FILE="${LOG_FILE:-/var/log/schoolbot/monitor.log}"
ALERT_EMAIL="${ALERT_EMAIL:-admin@example.com}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"

# Функции для вывода
error() {
    echo -e "${RED}❌ $1${NC}"
    log_message "ERROR" "$1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    log_message "INFO" "$1"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log_message "INFO" "$1"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log_message "WARN" "$1"
}

critical() {
    echo -e "${RED}🚨 $1${NC}"
    log_message "CRITICAL" "$1"
    send_alert "CRITICAL" "$1"
}

# Логирование
log_message() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$LOG_FILE"
}

# Отправка уведомлений
send_alert() {
    local level="$1"
    local message="$2"
    
    # Telegram уведомление
    if [[ -n "$TELEGRAM_BOT_TOKEN" ]] && [[ -n "$TELEGRAM_CHAT_ID" ]]; then
        local telegram_message="🚨 SchoolBot Alert [$level]
        
📅 Время: $(date)
🖥️ Сервер: $(hostname)
📍 Сообщение: $message

#schoolbot #alert #$level"
        
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d chat_id="$TELEGRAM_CHAT_ID" \
            -d text="$telegram_message" \
            -d parse_mode="HTML" &>/dev/null || warn "Не удалось отправить Telegram уведомление"
    fi
    
    # Email уведомление (если настроен mail)
    if command -v mail &> /dev/null && [[ -n "$ALERT_EMAIL" ]]; then
        echo "SchoolBot Alert [$level] - $(date)

Сервер: $(hostname)
Сообщение: $message

Проверьте состояние системы: docker compose ps
Логи: docker compose logs --tail=50" | mail -s "SchoolBot Alert [$level]" "$ALERT_EMAIL" &>/dev/null || warn "Не удалось отправить email"
    fi
}

# Функция показа помощи
show_help() {
    echo "Использование: $0 [ОПЦИИ]"
    echo ""
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -d, --dir DIR           Директория развертывания"
    echo "  -c, --continuous        Непрерывный мониторинг"
    echo "  -i, --interval SEC      Интервал проверки в секундах (по умолчанию: 60)"
    echo "  --check-docker          Проверить только Docker контейнеры"
    echo "  --check-health          Проверить только health endpoints"
    echo "  --check-resources       Проверить только системные ресурсы"
    echo "  --check-logs            Проверить логи на ошибки"
    echo "  --summary               Краткий отчет"
    echo ""
    echo "Примеры:"
    echo "  $0                                    # Однократная проверка"
    echo "  $0 -c -i 30                          # Непрерывный мониторинг каждые 30 сек"
    echo "  $0 --check-docker                    # Проверка только Docker"
    echo "  $0 --summary                         # Краткий отчет"
}

# Парсинг аргументов
CONTINUOUS=false
INTERVAL=60
CHECK_DOCKER_ONLY=false
CHECK_HEALTH_ONLY=false
CHECK_RESOURCES_ONLY=false
CHECK_LOGS_ONLY=false
SUMMARY_ONLY=false

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
        -c|--continuous)
            CONTINUOUS=true
            shift
            ;;
        -i|--interval)
            INTERVAL="$2"
            shift 2
            ;;
        --check-docker)
            CHECK_DOCKER_ONLY=true
            shift
            ;;
        --check-health)
            CHECK_HEALTH_ONLY=true
            shift
            ;;
        --check-resources)
            CHECK_RESOURCES_ONLY=true
            shift
            ;;
        --check-logs)
            CHECK_LOGS_ONLY=true
            shift
            ;;
        --summary)
            SUMMARY_ONLY=true
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

# Проверка Docker контейнеров
check_docker_containers() {
    info "Проверка состояния Docker контейнеров..."
    
    if [[ ! -d "$DEPLOY_DIR" ]]; then
        critical "Директория развертывания не найдена: $DEPLOY_DIR"
        return 1
    fi
    
    cd "$DEPLOY_DIR"
    
    # Проверка существования docker-compose.yml
    if [[ ! -f "docker-compose.yml" ]]; then
        critical "Файл docker-compose.yml не найден"
        return 1
    fi
    
    # Получение списка сервисов
    local services=$(docker compose config --services)
    local all_healthy=true
    
    for service in $services; do
        local container_status=$(docker compose ps --format json | jq -r ".[] | select(.Service == \"$service\") | .State" 2>/dev/null)
        
        if [[ "$container_status" == "running" ]]; then
            success "Контейнер $service: работает"
        elif [[ "$container_status" == "exited" ]]; then
            critical "Контейнер $service: остановлен"
            all_healthy=false
        else
            warn "Контейнер $service: неизвестное состояние ($container_status)"
            all_healthy=false
        fi
    done
    
    # Проверка health checks
    local unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.Names}}")
    if [[ -n "$unhealthy_containers" ]]; then
        critical "Неисправные контейнеры: $unhealthy_containers"
        all_healthy=false
    fi
    
    return $([[ "$all_healthy" == true ]] && echo 0 || echo 1)
}

# Проверка health endpoints
check_health_endpoints() {
    info "Проверка health endpoints..."
    
    local endpoints=(
        "http://localhost:8080/health:Bot Health Check"
    )
    
    local all_healthy=true
    
    for endpoint_info in "${endpoints[@]}"; do
        local endpoint=$(echo "$endpoint_info" | cut -d: -f1)
        local name=$(echo "$endpoint_info" | cut -d: -f2)
        
        if curl -f -s --connect-timeout 10 --max-time 30 "$endpoint" &>/dev/null; then
            success "$name: доступен"
        else
            critical "$name: недоступен ($endpoint)"
            all_healthy=false
        fi
    done
    
    return $([[ "$all_healthy" == true ]] && echo 0 || echo 1)
}

# Проверка системных ресурсов
check_system_resources() {
    info "Проверка системных ресурсов..."
    
    local issues_found=false
    
    # Проверка места на диске
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        critical "Мало места на диске: ${disk_usage}% использовано"
        issues_found=true
    elif [[ $disk_usage -gt 80 ]]; then
        warn "Место на диске заканчивается: ${disk_usage}% использовано"
    else
        success "Место на диске: ${disk_usage}% использовано"
    fi
    
    # Проверка оперативной памяти
    if command -v free &> /dev/null; then
        local mem_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
        local mem_available=$(free -h | awk 'NR==2{print $7}')
        
        if (( $(echo "$mem_usage > 90" | bc -l) )); then
            critical "Мало оперативной памяти: ${mem_usage}% использовано"
            issues_found=true
        elif (( $(echo "$mem_usage > 80" | bc -l) )); then
            warn "Оперативная память заканчивается: ${mem_usage}% использовано"
        else
            success "Оперативная память: ${mem_usage}% использовано (доступно: $mem_available)"
        fi
    fi
    
    # Проверка загрузки CPU
    if command -v uptime &> /dev/null; then
        local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
        local cpu_cores=$(nproc)
        local load_percentage=$(echo "scale=1; $load_avg * 100 / $cpu_cores" | bc)
        
        if (( $(echo "$load_percentage > 80" | bc -l) )); then
            warn "Высокая загрузка CPU: ${load_percentage}% (load average: $load_avg)"
        else
            success "Загрузка CPU: ${load_percentage}% (load average: $load_avg)"
        fi
    fi
    
    # Проверка Docker ресурсов
    if command -v docker &> /dev/null; then
        local docker_disk=$(docker system df --format "table {{.Type}}\t{{.Size}}" | grep "Total" | awk '{print $2}')
        info "Использование Docker: $docker_disk"
        
        # Проверка неиспользуемых ресурсов
        local unused_images=$(docker images -f "dangling=true" -q | wc -l)
        local unused_volumes=$(docker volume ls -f "dangling=true" -q | wc -l)
        
        if [[ $unused_images -gt 10 ]] || [[ $unused_volumes -gt 5 ]]; then
            warn "Много неиспользуемых Docker ресурсов (образы: $unused_images, тома: $unused_volumes)"
            info "Рекомендуется очистка: docker system prune -f"
        fi
    fi
    
    return $([[ "$issues_found" == false ]] && echo 0 || echo 1)
}

# Проверка логов на ошибки
check_logs_for_errors() {
    info "Проверка логов на ошибки..."
    
    if [[ ! -d "$DEPLOY_DIR" ]]; then
        warn "Директория развертывания не найдена"
        return 1
    fi
    
    cd "$DEPLOY_DIR"
    
    # Получение логов за последние 5 минут
    local recent_logs=$(docker compose logs --since 5m 2>/dev/null)
    
    # Поиск критических ошибок
    local error_patterns=(
        "ERROR"
        "CRITICAL"
        "FATAL"
        "Exception"
        "Traceback"
        "Failed"
        "Connection refused"
        "Timeout"
    )
    
    local errors_found=false
    
    for pattern in "${error_patterns[@]}"; do
        local error_count=$(echo "$recent_logs" | grep -c "$pattern" || true)
        if [[ $error_count -gt 0 ]]; then
            warn "Найдено ошибок с паттерном '$pattern': $error_count"
            errors_found=true
        fi
    done
    
    # Проверка специфических ошибок SchoolBot
    local bot_errors=$(echo "$recent_logs" | grep -E "(telegram.*error|database.*error|redis.*error)" -i || true)
    if [[ -n "$bot_errors" ]]; then
        critical "Найдены критические ошибки бота:"
        echo "$bot_errors" | head -5
        errors_found=true
    fi
    
    if [[ "$errors_found" == false ]]; then
        success "Критические ошибки в логах не найдены"
    fi
    
    return $([[ "$errors_found" == false ]] && echo 0 || echo 1)
}

# Проверка базы данных
check_database() {
    info "Проверка состояния базы данных..."
    
    cd "$DEPLOY_DIR"
    
    # Проверка подключения к PostgreSQL
    if docker compose exec -T postgres pg_isready -U schoolbot &>/dev/null; then
        success "PostgreSQL: подключение доступно"
    else
        critical "PostgreSQL: подключение недоступно"
        return 1
    fi
    
    # Проверка основных таблиц
    local table_count=$(docker compose exec -T postgres psql -U schoolbot -d schoolbot -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    
    if [[ $table_count -gt 0 ]]; then
        success "База данных: найдено $table_count таблиц"
    else
        critical "База данных: таблицы не найдены"
        return 1
    fi
    
    return 0
}

# Проверка Redis
check_redis() {
    info "Проверка состояния Redis..."
    
    cd "$DEPLOY_DIR"
    
    if docker compose exec -T redis redis-cli ping &>/dev/null; then
        success "Redis: подключение доступно"
        
        # Проверка использования памяти
        local redis_memory=$(docker compose exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        info "Redis память: $redis_memory"
    else
        critical "Redis: подключение недоступно"
        return 1
    fi
    
    return 0
}

# Генерация краткого отчета
generate_summary() {
    echo ""
    echo -e "${PURPLE}📋 Краткий отчет о состоянии SchoolBot${NC}"
    echo "========================================"
    
    # Время работы системы
    echo -e "${BLUE}⏱️  Время работы сервера:${NC} $(uptime -p)"
    
    # Версия развертывания
    if [[ -d "$DEPLOY_DIR/.git" ]]; then
        cd "$DEPLOY_DIR"
        local current_commit=$(git rev-parse --short HEAD)
        local last_update=$(git log -1 --format="%cr")
        echo -e "${BLUE}📦 Версия:${NC} $current_commit (обновлено $last_update)"
    fi
    
    # Состояние сервисов
    echo -e "${BLUE}🐳 Docker сервисы:${NC}"
    if [[ -d "$DEPLOY_DIR" ]] && [[ -f "$DEPLOY_DIR/docker-compose.yml" ]]; then
        cd "$DEPLOY_DIR"
        docker compose ps --format "table {{.Service}}\t{{.State}}\t{{.Status}}"
    fi
    
    # Системные ресурсы
    echo -e "${BLUE}💻 Системные ресурсы:${NC}"
    local disk_usage=$(df / | awk 'NR==2 {print $5}')
    echo "  Диск: $disk_usage использовано"
    
    if command -v free &> /dev/null; then
        local mem_usage=$(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
        echo "  RAM: $mem_usage использовано"
    fi
    
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo "  CPU: load average $load_avg"
    
    # Последние ошибки
    echo -e "${BLUE}📊 Статистика логов (последний час):${NC}"
    if [[ -f "$LOG_FILE" ]]; then
        local recent_errors=$(tail -100 "$LOG_FILE" | grep -c "ERROR\|CRITICAL" || echo "0")
        local recent_warnings=$(tail -100 "$LOG_FILE" | grep -c "WARN" || echo "0")
        echo "  Ошибки: $recent_errors"
        echo "  Предупреждения: $recent_warnings"
    fi
}

# Основная функция мониторинга
run_monitoring() {
    local overall_status=0
    
    # Выполнение проверок в зависимости от флагов
    if [[ "$CHECK_DOCKER_ONLY" == true ]]; then
        check_docker_containers || overall_status=1
    elif [[ "$CHECK_HEALTH_ONLY" == true ]]; then
        check_health_endpoints || overall_status=1
    elif [[ "$CHECK_RESOURCES_ONLY" == true ]]; then
        check_system_resources || overall_status=1
    elif [[ "$CHECK_LOGS_ONLY" == true ]]; then
        check_logs_for_errors || overall_status=1
    elif [[ "$SUMMARY_ONLY" == true ]]; then
        generate_summary
        return 0
    else
        # Полная проверка
        check_docker_containers || overall_status=1
        check_database || overall_status=1
        check_redis || overall_status=1
        check_health_endpoints || overall_status=1
        check_system_resources || overall_status=1
        check_logs_for_errors || overall_status=1
    fi
    
    echo ""
    if [[ $overall_status -eq 0 ]]; then
        success "🎉 Все проверки пройдены успешно!"
    else
        critical "🚨 Обнаружены проблемы в системе!"
    fi
    
    return $overall_status
}

# Основная функция
main() {
    log_message "INFO" "Запуск мониторинга (PID: $$)"
    
    if [[ "$CONTINUOUS" == true ]]; then
        info "Запуск непрерывного мониторинга (интервал: ${INTERVAL}с)"
        info "Для остановки нажмите Ctrl+C"
        
        # Обработка сигнала завершения
        trap 'info "Остановка мониторинга"; exit 0' SIGINT SIGTERM
        
        while true; do
            echo ""
            echo "$(date): Выполнение проверки..."
            run_monitoring
            
            echo "Следующая проверка через ${INTERVAL} секунд..."
            sleep "$INTERVAL"
        done
    else
        run_monitoring
        generate_summary
    fi
}

# Запуск основной функции
main "$@"
