"""add seen_intro field to users table

Revision ID: 006
Revises: 005_add_indexes
Create Date: 2024-01-15 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Проверяем, существует ли уже колонка seen_intro
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'seen_intro'
    """))
    
    if not result.fetchone():
        # Добавляем поле seen_intro в таблицу users
        op.add_column(
            "users", sa.Column("seen_intro", sa.Boolean(), nullable=False, server_default="false")
        )


def downgrade() -> None:
    # Удаляем поле seen_intro из таблицы users
    op.drop_column("users", "seen_intro")
