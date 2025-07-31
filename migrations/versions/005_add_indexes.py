"""add indexes

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tasks_deadline", "tasks", ["deadline"])


def downgrade():
    op.drop_index("ix_tickets_status")
    op.drop_index("ix_tasks_deadline")
