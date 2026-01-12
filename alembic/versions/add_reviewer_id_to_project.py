"""Add reviewer_id to projects table

Revision ID: add_reviewer_id_to_project
Revises: remove_student_id
Create Date: 2025-01-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_reviewer_id_to_project'
down_revision = 'remove_student_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reviewer_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_projects_reviewer_id', 'users', ['reviewer_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint('fk_projects_reviewer_id', type_='foreignkey')
        batch_op.drop_column('reviewer_id')
