"""add_student_tables

Revision ID: 2bd705379fdb
Revises: 13df810a474a
Create Date: 2026-01-12 17:54:07.853363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bd705379fdb'
down_revision: Union[str, Sequence[str], None] = '13df810a474a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create students table
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('student_number', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('year', sa.String(), nullable=False),
        sa.Column('is_verified', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_students_student_number'), 'students', ['student_number'], unique=True)
    op.create_index(op.f('ix_students_email'), 'students', ['email'], unique=True)
    
    # Create email_verifications table
    op.create_table(
        'email_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create password_resets table
    op.create_table(
        'password_resets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_token'), 'password_resets', ['token'], unique=True)
    
    # Create submissions table
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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('submissions')
    op.drop_index(op.f('ix_password_resets_token'), table_name='password_resets')
    op.drop_table('password_resets')
    op.drop_table('email_verifications')
    op.drop_index(op.f('ix_students_email'), table_name='students')
    op.drop_index(op.f('ix_students_student_number'), table_name='students')
    op.drop_table('students')
