"""enable RLS

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # включаем RLS
    op.execute("ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE psych_requests ENABLE ROW LEVEL SECURITY;")
    
    # policy: владелец = author_id или админ/директор
    op.execute("""
        CREATE POLICY ticket_owner ON tickets
        USING (author_id = current_setting('app.user_id')::int
               OR current_setting('app.role') IN ('admin','director'));
    """)
    op.execute("""
        CREATE POLICY psych_owner ON psych_requests
        USING (from_id = current_setting('app.user_id')::int
               OR current_setting('app.role') = 'psych');
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS ticket_owner ON tickets;")
    op.execute("DROP POLICY IF EXISTS psych_owner ON psych_requests;")
    op.execute("ALTER TABLE tickets DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE psych_requests DISABLE ROW LEVEL SECURITY;") 