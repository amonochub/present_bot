"""Оптимизация производительности - добавление индексов

Revision ID: 007
Revises: 006
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавить индексы для оптимизации производительности"""
    
    connection = op.get_bind()
    
    # Индексы для таблицы users
    op.create_index('ix_users_tg_id_role', 'users', ['tg_id', 'role'])
    op.create_index('ix_users_role_active', 'users', ['role', 'is_active'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # Индексы для таблицы notes (используем teacher_id вместо user_id)
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'notes'
        );
    """))
    
    if result.scalar():
        op.create_index('ix_notes_teacher_id_created', 'notes', ['teacher_id', 'created_at'])
        op.create_index('ix_notes_content_search', 'notes', ['content'])
    
    # Индексы для таблицы tickets
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tickets'
        );
    """))
    
    if result.scalar():
        op.create_index('ix_tickets_status_created', 'tickets', ['status', 'created_at'])
        op.create_index('ix_tickets_user_id_status', 'tickets', ['user_id', 'status'])
        op.create_index('ix_tickets_priority_status', 'tickets', ['priority', 'status'])
        op.create_index('ix_tickets_created_at', 'tickets', ['created_at'])
    
    # Индексы для таблицы tasks
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tasks'
        );
    """))
    
    if result.scalar():
        op.create_index('ix_tasks_status_priority', 'tasks', ['status', 'priority'])
        op.create_index('ix_tasks_deadline_status', 'tasks', ['deadline', 'status'])
        op.create_index('ix_tasks_created_at', 'tasks', ['created_at'])
    
    # Индексы для таблицы psych_requests
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'psych_requests'
        );
    """))
    
    if result.scalar():
        op.create_index('ix_psych_requests_status_created', 'psych_requests', ['status', 'created_at'])
        op.create_index('ix_psych_requests_user_id_status', 'psych_requests', ['user_id', 'status'])
    
    # Индексы для таблицы media_requests
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'media_requests'
        );
    """))
    
    if result.scalar():
        op.create_index('ix_media_requests_user_id_status', 'media_requests', ['user_id', 'status'])
        op.create_index('ix_media_requests_type_status', 'media_requests', ['request_type', 'status'])
        op.create_index('ix_media_requests_created_at', 'media_requests', ['created_at'])
    
    # Индексы для таблицы broadcasts
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'broadcasts'
        );
    """))
    
    if result.scalar():
        op.create_index('ix_broadcasts_status_scheduled', 'broadcasts', ['status', 'scheduled_at'])
        op.create_index('ix_broadcasts_created_at', 'broadcasts', ['created_at'])
    
    # Индексы для таблицы notifications
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'notifications'
        );
    """))
    
    if result.scalar():
        op.create_index('ix_notifications_user_id_read', 'notifications', ['user_id', 'is_read'])
        op.create_index('ix_notifications_type_created', 'notifications', ['type', 'created_at'])
        op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    
    # Составные индексы для сложных запросов
    op.create_index('ix_users_role_active_created', 'users', ['role', 'is_active', 'created_at'])
    
    # Частичные индексы для оптимизации
    # Только активные пользователи
    op.execute("""
        CREATE INDEX ix_users_active_only 
        ON users (tg_id, role) 
        WHERE is_active = true
    """)
    
    # Только открытые заявки (если таблица tickets существует)
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tickets'
        );
    """))
    
    if result.scalar():
        op.execute("""
            CREATE INDEX ix_tickets_open_only 
            ON tickets (user_id, priority, created_at) 
            WHERE status = 'open'
        """)
    
    # Только активные задачи (если таблица tasks существует)
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tasks'
        );
    """))
    
    if result.scalar():
        op.execute("""
            CREATE INDEX ix_tasks_pending_only 
            ON tasks (deadline, priority) 
            WHERE status = 'pending'
        """)
    
    # Только непрочитанные уведомления (если таблица notifications существует)
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'notifications'
        );
    """))
    
    if result.scalar():
        op.execute("""
            CREATE INDEX ix_notifications_unread_only 
            ON notifications (user_id, type, created_at) 
            WHERE is_read = false
        """)


def downgrade() -> None:
    """Удалить индексы"""
    connection = op.get_bind()
    
    # Удаляем индексы для таблицы users
    op.drop_index('ix_users_tg_id_role')
    op.drop_index('ix_users_role_active')
    op.drop_index('ix_users_username')
    op.drop_index('ix_users_created_at')
    op.drop_index('ix_users_role_active_created')
    op.drop_index('ix_users_active_only')
    
    # Удаляем индексы для таблицы notes
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'notes'
        );
    """))
    
    if result.scalar():
        op.drop_index('ix_notes_teacher_id_created')
        op.drop_index('ix_notes_content_search')
    
    # Удаляем индексы для таблицы tickets
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tickets'
        );
    """))
    
    if result.scalar():
        op.drop_index('ix_tickets_status_created')
        op.drop_index('ix_tickets_user_id_status')
        op.drop_index('ix_tickets_priority_status')
        op.drop_index('ix_tickets_created_at')
        op.drop_index('ix_tickets_open_only')
    
    # Удаляем индексы для таблицы tasks
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tasks'
        );
    """))
    
    if result.scalar():
        op.drop_index('ix_tasks_status_priority')
        op.drop_index('ix_tasks_deadline_status')
        op.drop_index('ix_tasks_created_at')
        op.drop_index('ix_tasks_pending_only')
    
    # Удаляем индексы для таблицы psych_requests
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'psych_requests'
        );
    """))
    
    if result.scalar():
        op.drop_index('ix_psych_requests_status_created')
        op.drop_index('ix_psych_requests_user_id_status')
    
    # Удаляем индексы для таблицы media_requests
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'media_requests'
        );
    """))
    
    if result.scalar():
        op.drop_index('ix_media_requests_user_id_status')
        op.drop_index('ix_media_requests_type_status')
        op.drop_index('ix_media_requests_created_at')
    
    # Удаляем индексы для таблицы broadcasts
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'broadcasts'
        );
    """))
    
    if result.scalar():
        op.drop_index('ix_broadcasts_status_scheduled')
        op.drop_index('ix_broadcasts_created_at')
    
    # Удаляем индексы для таблицы notifications
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'notifications'
        );
    """))
    
    if result.scalar():
        op.drop_index('ix_notifications_user_id_read')
        op.drop_index('ix_notifications_type_created')
        op.drop_index('ix_notifications_created_at')
        op.drop_index('ix_notifications_unread_only') 