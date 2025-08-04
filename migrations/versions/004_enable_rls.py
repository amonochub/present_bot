"""enable RLS

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # Проверяем существование таблиц перед включением RLS
    connection = op.get_bind()
    
    # Проверяем существование таблицы tickets
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tickets'
        );
    """))
    
    if result.scalar():
        # включаем RLS для tickets
        op.execute("ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;")
        
        # policy: владелец = user_id или админ/директор
        op.execute(
            """
            CREATE POLICY ticket_owner ON tickets
            USING (user_id = current_setting('app.user_id')::int
                   OR current_setting('app.role') IN ('admin','director'));
        """
        )
    
    # Проверяем существование таблицы psych_requests
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'psych_requests'
        );
    """))
    
    if result.scalar():
        # включаем RLS для psych_requests
        op.execute("ALTER TABLE psych_requests ENABLE ROW LEVEL SECURITY;")
        
        # policy: владелец = from_id или психолог
        op.execute(
            """
            CREATE POLICY psych_owner ON psych_requests
            USING (from_id = current_setting('app.user_id')::int
                   OR current_setting('app.role') = 'psych');
        """
        )


def downgrade():
    connection = op.get_bind()
    
    # Проверяем существование таблицы tickets
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tickets'
        );
    """))
    
    if result.scalar():
        op.execute("DROP POLICY IF EXISTS ticket_owner ON tickets;")
        op.execute("ALTER TABLE tickets DISABLE ROW LEVEL SECURITY;")
    
    # Проверяем существование таблицы psych_requests
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'psych_requests'
        );
    """))
    
    if result.scalar():
        op.execute("DROP POLICY IF EXISTS psych_owner ON psych_requests;")
        op.execute("ALTER TABLE psych_requests DISABLE ROW LEVEL SECURITY;")
