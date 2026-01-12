"""Merge Submission model into Project model

Revision ID: merge_submission_into_project
Revises: drop_password_from_student
Create Date: 2026-01-12 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_submission_into_project'
down_revision: Union[str, None] = 'drop_password_from_student'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns from Submission to Project
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('student_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('admin_notes', sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            'fk_projects_student_id',
            'students',
            ['student_id'], ['id'],
            ondelete='CASCADE'
        )
    
    # Drop the submissions table
    op.drop_table('submissions')


def downgrade() -> None:
    # Recreate the submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Remove columns from Project
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint('fk_projects_student_id', type_='foreignkey')
        batch_op.drop_column('student_id')
        batch_op.drop_column('reviewed_at')
        batch_op.drop_column('admin_notes')
