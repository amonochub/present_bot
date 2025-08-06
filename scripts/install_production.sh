#!/bin/bash
# Скрипт установки SchoolBot на production сервер

set -e

echo "🚀 Установка SchoolBot на production сервер"
echo "==========================================="

# Цветовая схема
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфигурация
INSTALL_DIR="/opt/schoolbot"
SERVICE_USER="schoolbot"
SERVICE_GROUP="schoolbot"
LOG_DIR="/var/log/schoolbot"
BACKUP_DIR="/var/backups/schoolbot"
REPO_URL="https://github.com/amonochub/present_bot.git"

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

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Этот скрипт должен быть запущен от имени root"
        echo "Запустите: sudo $0"
        exit 1
    fi
    success "Права root подтверждены"
}

# Определение ОС
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
        success "Обнаружена ОС: $PRETTY_NAME"
    else
        error "Не удалось определить операционную систему"
        exit 1
    fi
}

# Обновление системы
update_system() {
    info "Обновление системы..."
    
    case $OS in
        ubuntu|debian)
            apt update && apt upgrade -y
            ;;
        centos|rhel|fedora)
            yum update -y || dnf update -y
            ;;
        *)
            warn "Неизвестная ОС, пропуск обновления"
            ;;
    esac
    
    success "Система обновлена"
}

# Установка зависимостей
install_dependencies() {
    info "Установка необходимых пакетов..."
    
    case $OS in
        ubuntu|debian)
            apt install -y \
                curl \
                wget \
                git \
                ca-certificates \
                gnupg \
                lsb-release \
                unzip \
                jq \
                htop \
                nano \
                fail2ban \
                ufw \
                cron \
                logrotate \
                bc \
                mailutils
            ;;
        centos|rhel|fedora)
            yum install -y curl wget git ca-certificates gnupg unzip jq htop nano fail2ban firewalld cronie logrotate bc mailx || \
            dnf install -y curl wget git ca-certificates gnupg unzip jq htop nano fail2ban firewalld cronie logrotate bc mailx
            ;;
        *)
            error "Установка зависимостей для $OS не поддерживается"
            exit 1
            ;;
    esac
    
    success "Зависимости установлены"
}

# Установка Docker
install_docker() {
    info "Установка Docker..."
    
    if command -v docker &> /dev/null; then
        info "Docker уже установлен: $(docker --version)"
        return
    fi
    
    # Установка Docker по официальному скрипту
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Запуск и автозапуск Docker
    systemctl enable docker
    systemctl start docker
    
    success "Docker установлен и запущен"
}

# Создание пользователя сервиса
create_service_user() {
    info "Создание пользователя сервиса..."
    
    # Создание группы
    if ! getent group $SERVICE_GROUP &>/dev/null; then
        groupadd $SERVICE_GROUP
        success "Группа $SERVICE_GROUP создана"
    fi
    
    # Создание пользователя
    if ! getent passwd $SERVICE_USER &>/dev/null; then
        useradd -r -g $SERVICE_GROUP -d $INSTALL_DIR -s /bin/bash $SERVICE_USER
        success "Пользователь $SERVICE_USER создан"
    fi
    
    # Добавление в группу docker
    usermod -aG docker $SERVICE_USER
    success "Пользователь $SERVICE_USER добавлен в группу docker"
}

# Создание директорий
create_directories() {
    info "Создание структуры директорий..."
    
    # Основные директории
    mkdir -p $INSTALL_DIR
    mkdir -p $LOG_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p /etc/schoolbot
    
    # Установка прав доступа
    chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
    chown -R $SERVICE_USER:$SERVICE_GROUP $LOG_DIR
    chown -R $SERVICE_USER:$SERVICE_GROUP $BACKUP_DIR
    
    # Права только для владельца на конфиденциальные директории
    chmod 750 $INSTALL_DIR
    chmod 750 $LOG_DIR
    chmod 750 $BACKUP_DIR
    
    success "Структура директорий создана"
}

# Клонирование репозитория
clone_repository() {
    info "Клонирование репозитория..."
    
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        info "Репозиторий уже существует, выполняется обновление..."
        cd $INSTALL_DIR
        sudo -u $SERVICE_USER git pull
    else
        # Клонирование от имени сервисного пользователя
        sudo -u $SERVICE_USER git clone $REPO_URL $INSTALL_DIR
    fi
    
    success "Репозиторий готов"
}

# Настройка firewall
configure_firewall() {
    info "Настройка firewall..."
    
    case $OS in
        ubuntu|debian)
            # UFW
            ufw --force enable
            ufw default deny incoming
            ufw default allow outgoing
            ufw allow 22/tcp comment 'SSH'
            ufw allow 80/tcp comment 'HTTP'
            ufw allow 443/tcp comment 'HTTPS'
            # Не открываем порты БД и Redis для внешнего доступа
            success "UFW настроен"
            ;;
        centos|rhel|fedora)
            # firewalld
            systemctl enable firewalld
            systemctl start firewalld
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --reload
            success "firewalld настроен"
            ;;
    esac
}

# Настройка fail2ban
configure_fail2ban() {
    info "Настройка fail2ban..."
    
    # Создание локальной конфигурации
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
backend = systemd

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF
    
    systemctl enable fail2ban
    systemctl start fail2ban
    
    success "fail2ban настроен"
}

# Установка systemd сервиса
install_systemd_service() {
    info "Установка systemd сервиса..."
    
    # Копирование сервисного файла
    cp $INSTALL_DIR/systemd/schoolbot.service /etc/systemd/system/
    
    # Перезагрузка systemd и включение сервиса
    systemctl daemon-reload
    systemctl enable schoolbot
    
    success "Systemd сервис установлен"
}

# Настройка logrotate
configure_logrotate() {
    info "Настройка ротации логов..."
    
    cat > /etc/logrotate.d/schoolbot << 'EOF'
/var/log/schoolbot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 schoolbot schoolbot
    postrotate
        systemctl reload schoolbot > /dev/null 2>&1 || true
    endscript
}
EOF
    
    success "Logrotate настроен"
}

# Настройка cron задач
configure_cron() {
    info "Настройка cron задач..."
    
    # Создание crontab для пользователя schoolbot
    cat > /tmp/schoolbot_crontab << 'EOF'
# Backup database daily at 2 AM
0 2 * * * /opt/schoolbot/scripts/backup_db.sh

# Monitor system health every 5 minutes
*/5 * * * * /opt/schoolbot/scripts/monitor.sh --summary >> /var/log/schoolbot/health.log 2>&1

# Clean old Docker images weekly
0 3 * * 0 /usr/bin/docker system prune -f

# Rotate logs daily
0 4 * * * /usr/sbin/logrotate /etc/logrotate.d/schoolbot
EOF
    
    # Установка crontab
    sudo -u $SERVICE_USER crontab /tmp/schoolbot_crontab
    rm /tmp/schoolbot_crontab
    
    success "Cron задачи настроены"
}

# Создание конфигурационного файла
create_env_template() {
    info "Создание шаблона конфигурации..."
    
    if [[ ! -f "$INSTALL_DIR/.env" ]]; then
        sudo -u $SERVICE_USER cp $INSTALL_DIR/env.example $INSTALL_DIR/.env
        
        # Генерация безопасных паролей
        local db_password=$(openssl rand -base64 32)
        local admin_secret=$(openssl rand -hex 16)
        
        # Обновление .env с безопасными значениями
        sudo -u $SERVICE_USER sed -i "s/DB_PASS=.*/DB_PASS=${db_password}/" $INSTALL_DIR/.env
        sudo -u $SERVICE_USER sed -i "s/ENV=.*/ENV=prod/" $INSTALL_DIR/.env
        
        warn "ВАЖНО: Настройте следующие переменные в $INSTALL_DIR/.env:"
        warn "- TELEGRAM_TOKEN (получите у @BotFather)"
        warn "- ADMIN_IDS (ваш Telegram ID от @userinfobot)"
        warn "- GLITCHTIP_DSN (опционально, для мониторинга)"
        
        success "Шаблон конфигурации создан"
    else
        info "Конфигурация .env уже существует"
    fi
}

# Установка дополнительных инструментов мониторинга
install_monitoring_tools() {
    info "Установка инструментов мониторинга..."
    
    # Установка netdata (опционально)
    if [[ ! -f /usr/sbin/netdata ]]; then
        warn "Установить Netdata для мониторинга? (y/N)"
        read -r install_netdata
        
        if [[ "$install_netdata" == "y" ]] || [[ "$install_netdata" == "Y" ]]; then
            bash <(curl -Ss https://my-netdata.io/kickstart.sh) --stable-channel --disable-telemetry
            success "Netdata установлен (доступен на порту 19999)"
        fi
    fi
}

# Настройка SSL (Let's Encrypt)
setup_ssl() {
    info "Настройка SSL сертификатов..."
    
    warn "Настроить SSL сертификаты Let's Encrypt? (y/N)"
    read -r setup_ssl_answer
    
    if [[ "$setup_ssl_answer" == "y" ]] || [[ "$setup_ssl_answer" == "Y" ]]; then
        echo -n "Введите доменное имя: "
        read -r domain_name
        
        if [[ -n "$domain_name" ]]; then
            # Установка Certbot
            case $OS in
                ubuntu|debian)
                    apt install -y certbot
                    ;;
                centos|rhel|fedora)
                    yum install -y certbot || dnf install -y certbot
                    ;;
            esac
            
            # Получение сертификата
            certbot certonly --standalone -d "$domain_name" --non-interactive --agree-tos -m admin@"$domain_name"
            
            # Настройка автообновления
            echo "0 2 * * * certbot renew --quiet" | crontab -
            
            success "SSL сертификат настроен для $domain_name"
        fi
    fi
}

# Создание скрипта для быстрого управления
create_management_script() {
    info "Создание скрипта управления..."
    
    cat > /usr/local/bin/schoolbot << 'EOF'
#!/bin/bash
# SchoolBot Management Script

INSTALL_DIR="/opt/schoolbot"
SERVICE_USER="schoolbot"

case "$1" in
    start)
        echo "Запуск SchoolBot..."
        systemctl start schoolbot
        ;;
    stop)
        echo "Остановка SchoolBot..."
        systemctl stop schoolbot
        ;;
    restart)
        echo "Перезапуск SchoolBot..."
        systemctl restart schoolbot
        ;;
    status)
        systemctl status schoolbot
        ;;
    logs)
        journalctl -u schoolbot -f
        ;;
    update)
        echo "Обновление SchoolBot..."
        cd $INSTALL_DIR
        sudo -u $SERVICE_USER git pull
        systemctl restart schoolbot
        ;;
    backup)
        echo "Создание резервной копии..."
        sudo -u $SERVICE_USER $INSTALL_DIR/scripts/backup_db.sh
        ;;
    monitor)
        sudo -u $SERVICE_USER $INSTALL_DIR/scripts/monitor.sh
        ;;
    config)
        nano $INSTALL_DIR/.env
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update|backup|monitor|config}"
        exit 1
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/schoolbot
    
    success "Скрипт управления создан (/usr/local/bin/schoolbot)"
}

# Финальная проверка
final_check() {
    info "Выполнение финальной проверки..."
    
    # Проверка сервисов
    if systemctl is-enabled docker &>/dev/null; then
        success "Docker: включен для автозапуска"
    else
        warn "Docker: не настроен для автозапуска"
    fi
    
    if systemctl is-enabled schoolbot &>/dev/null; then
        success "SchoolBot: включен для автозапуска"
    else
        warn "SchoolBot: не настроен для автозапуска"
    fi
    
    # Проверка прав доступа
    if [[ -O $INSTALL_DIR ]] || [[ $(stat -c %U $INSTALL_DIR) == $SERVICE_USER ]]; then
        success "Права доступа: корректные"
    else
        warn "Права доступа: требуют проверки"
    fi
    
    # Проверка конфигурации
    if [[ -f "$INSTALL_DIR/.env" ]]; then
        success "Конфигурация: файл .env найден"
        
        # Проверка ключевых параметров
        if grep -q "TELEGRAM_TOKEN=your_telegram_token_here" $INSTALL_DIR/.env; then
            warn "TELEGRAM_TOKEN: требует настройки"
        else
            success "TELEGRAM_TOKEN: настроен"
        fi
    else
        error "Конфигурация: файл .env не найден"
    fi
}

# Показ итоговой информации
show_final_info() {
    echo ""
    echo -e "${GREEN}🎉 Установка SchoolBot завершена!${NC}"
    echo "=================================="
    
    echo -e "${BLUE}📁 Директории:${NC}"
    echo "  Установка: $INSTALL_DIR"
    echo "  Логи: $LOG_DIR"
    echo "  Резервные копии: $BACKUP_DIR"
    echo ""
    
    echo -e "${BLUE}🔧 Управление:${NC}"
    echo "  Запуск: schoolbot start"
    echo "  Остановка: schoolbot stop"
    echo "  Статус: schoolbot status"
    echo "  Логи: schoolbot logs"
    echo "  Обновление: schoolbot update"
    echo "  Конфигурация: schoolbot config"
    echo ""
    
    echo -e "${BLUE}⚙️ Следующие шаги:${NC}"
    echo "  1. Настройте конфигурацию: nano $INSTALL_DIR/.env"
    echo "  2. Добавьте TELEGRAM_TOKEN от @BotFather"
    echo "  3. Добавьте ADMIN_IDS от @userinfobot"
    echo "  4. Запустите бота: schoolbot start"
    echo "  5. Проверьте статус: schoolbot status"
    echo ""
    
    echo -e "${BLUE}🔗 Полезные ссылки:${NC}"
    echo "  Документация: https://github.com/amonochub/present_bot"
    echo "  Статус системы: systemctl status schoolbot"
    echo "  Логи приложения: journalctl -u schoolbot -f"
    
    if command -v netdata &>/dev/null; then
        echo "  Мониторинг: http://$(hostname -I | awk '{print $1}'):19999"
    fi
    
    echo ""
    warn "НЕ ЗАБУДЬТЕ настроить .env файл перед запуском!"
}

# Основная функция установки
main() {
    echo "Установка SchoolBot на production сервер"
    echo "Это займет несколько минут..."
    echo ""
    
    # Выполнение всех этапов установки
    check_root
    detect_os
    update_system
    install_dependencies
    install_docker
    create_service_user
    create_directories
    clone_repository
    configure_firewall
    configure_fail2ban
    install_systemd_service
    configure_logrotate
    configure_cron
    create_env_template
    install_monitoring_tools
    setup_ssl
    create_management_script
    final_check
    show_final_info
    
    echo ""
    success "🚀 Установка завершена! Система готова к настройке и запуску."
}

# Запуск установки
main "$@"
