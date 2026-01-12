"""add_project_status

Revision ID: 4322e98b9495
Revises: 2bd705379fdb
Create Date: 2026-01-12 21:33:40.939439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4322e98b9495'
down_revision: Union[str, Sequence[str], None] = '2bd705379fdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('projects', sa.Column('status', sa.String(), nullable=False, server_default='pending'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('projects', 'status')
