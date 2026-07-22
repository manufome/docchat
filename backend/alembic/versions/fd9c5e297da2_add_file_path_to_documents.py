"""add file_path to documents

Revision ID: fd9c5e297da2
Revises: 5a9b7b39cc86
Create Date: 2026-07-22 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd9c5e297da2'
down_revision = '5a9b7b39cc86'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'documents',
        sa.Column('file_path', sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('documents', 'file_path')
