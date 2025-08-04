"""Оптимизация производительности - добавление индексов

Revision ID: 007
Revises: 006
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавить индексы для оптимизации производительности"""
    
    # Индексы для таблицы users
    op.create_index('ix_users_tg_id_role', 'users', ['tg_id', 'role'])
    op.create_index('ix_users_role_active', 'users', ['role', 'is_active'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # Индексы для таблицы notes
    op.create_index('ix_notes_user_id_created', 'notes', ['user_id', 'created_at'])
    op.create_index('ix_notes_title_search', 'notes', ['title'])
    op.create_index('ix_notes_content_search', 'notes', ['content'])
    
    # Индексы для таблицы tickets
    op.create_index('ix_tickets_status_created', 'tickets', ['status', 'created_at'])
    op.create_index('ix_tickets_user_id_status', 'tickets', ['user_id', 'status'])
    op.create_index('ix_tickets_priority_status', 'tickets', ['priority', 'status'])
    op.create_index('ix_tickets_created_at', 'tickets', ['created_at'])
    
    # Индексы для таблицы tasks
    op.create_index('ix_tasks_status_priority', 'tasks', ['status', 'priority'])
    op.create_index('ix_tasks_assigned_to_status', 'tasks', ['assigned_to_id', 'status'])
    op.create_index('ix_tasks_author_status', 'tasks', ['author_id', 'status'])
    op.create_index('ix_tasks_deadline_status', 'tasks', ['deadline', 'status'])
    op.create_index('ix_tasks_created_at', 'tasks', ['created_at'])
    
    # Индексы для таблицы psych_requests
    op.create_index('ix_psych_requests_status_created', 'psych_requests', ['status', 'created_at'])
    op.create_index('ix_psych_requests_user_id_status', 'psych_requests', ['user_id', 'status'])
    op.create_index('ix_psych_requests_anonymous_status', 'psych_requests', ['is_anonymous', 'status'])
    
    # Индексы для таблицы media_requests
    op.create_index('ix_media_requests_user_id_status', 'media_requests', ['user_id', 'status'])
    op.create_index('ix_media_requests_type_status', 'media_requests', ['request_type', 'status'])
    op.create_index('ix_media_requests_created_at', 'media_requests', ['created_at'])
    
    # Индексы для таблицы broadcasts
    op.create_index('ix_broadcasts_status_scheduled', 'broadcasts', ['status', 'scheduled_at'])
    op.create_index('ix_broadcasts_created_at', 'broadcasts', ['created_at'])
    
    # Индексы для таблицы notifications
    op.create_index('ix_notifications_user_id_read', 'notifications', ['user_id', 'is_read'])
    op.create_index('ix_notifications_type_created', 'notifications', ['type', 'created_at'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    
    # Составные индексы для сложных запросов
    op.create_index('ix_users_role_active_created', 'users', ['role', 'is_active', 'created_at'])
    op.create_index('ix_tickets_status_priority_created', 'tickets', ['status', 'priority', 'created_at'])
    op.create_index('ix_tasks_status_deadline_priority', 'tasks', ['status', 'deadline', 'priority'])
    
    # Частичные индексы для оптимизации
    # Только активные пользователи
    op.execute("""
        CREATE INDEX ix_users_active_only 
        ON users (tg_id, role) 
        WHERE is_active = true
    """)
    
    # Только открытые заявки
    op.execute("""
        CREATE INDEX ix_tickets_open_only 
        ON tickets (user_id, priority, created_at) 
        WHERE status = 'open'
    """)
    
    # Только активные задачи
    op.execute("""
        CREATE INDEX ix_tasks_pending_only 
        ON tasks (assigned_to_id, priority, deadline) 
        WHERE status = 'pending'
    """)
    
    # Только непрочитанные уведомления
    op.execute("""
        CREATE INDEX ix_notifications_unread_only 
        ON notifications (user_id, type, created_at) 
        WHERE is_read = false
    """)


def downgrade() -> None:
    """Удалить индексы"""
    
    # Удаляем составные индексы
    op.drop_index('ix_users_role_active_created', table_name='users')
    op.drop_index('ix_tickets_status_priority_created', table_name='tickets')
    op.drop_index('ix_tasks_status_deadline_priority', table_name='tasks')
    
    # Удаляем частичные индексы
    op.execute("DROP INDEX IF EXISTS ix_users_active_only")
    op.execute("DROP INDEX IF EXISTS ix_tickets_open_only")
    op.execute("DROP INDEX IF EXISTS ix_tasks_pending_only")
    op.execute("DROP INDEX IF EXISTS ix_notifications_unread_only")
    
    # Удаляем обычные индексы
    op.drop_index('ix_users_tg_id_role', table_name='users')
    op.drop_index('ix_users_role_active', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_created_at', table_name='users')
    
    op.drop_index('ix_notes_user_id_created', table_name='notes')
    op.drop_index('ix_notes_title_search', table_name='notes')
    op.drop_index('ix_notes_content_search', table_name='notes')
    
    op.drop_index('ix_tickets_status_created', table_name='tickets')
    op.drop_index('ix_tickets_user_id_status', table_name='tickets')
    op.drop_index('ix_tickets_priority_status', table_name='tickets')
    op.drop_index('ix_tickets_created_at', table_name='tickets')
    
    op.drop_index('ix_tasks_status_priority', table_name='tasks')
    op.drop_index('ix_tasks_assigned_to_status', table_name='tasks')
    op.drop_index('ix_tasks_author_status', table_name='tasks')
    op.drop_index('ix_tasks_deadline_status', table_name='tasks')
    op.drop_index('ix_tasks_created_at', table_name='tasks')
    
    op.drop_index('ix_psych_requests_status_created', table_name='psych_requests')
    op.drop_index('ix_psych_requests_user_id_status', table_name='psych_requests')
    op.drop_index('ix_psych_requests_anonymous_status', table_name='psych_requests')
    
    op.drop_index('ix_media_requests_user_id_status', table_name='media_requests')
    op.drop_index('ix_media_requests_type_status', table_name='media_requests')
    op.drop_index('ix_media_requests_created_at', table_name='media_requests')
    
    op.drop_index('ix_broadcasts_status_scheduled', table_name='broadcasts')
    op.drop_index('ix_broadcasts_created_at', table_name='broadcasts')
    
    op.drop_index('ix_notifications_user_id_read', table_name='notifications')
    op.drop_index('ix_notifications_type_created', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications') 