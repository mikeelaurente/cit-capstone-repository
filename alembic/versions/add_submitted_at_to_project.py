"""Add submitted_at column to projects table

Revision ID: add_submitted_at_to_project
Revises: add_reviewer_id_to_project
Create Date: 2025-01-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_submitted_at_to_project'
down_revision = 'add_reviewer_id_to_project'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('submitted_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))


def downgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('submitted_at')
