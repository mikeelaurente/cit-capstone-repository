"""Add analytics table for tracking searches and views

Revision ID: add_analytics_table
Revises: add_category_to_project
Create Date: 2026-01-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_analytics_table'
down_revision = 'add_category_to_project'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics table
    op.create_table(
        'analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('search_query', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for query performance
    op.create_index(op.f('ix_analytics_project_id'), 'analytics', ['project_id'], unique=False)
    op.create_index(op.f('ix_analytics_event_type'), 'analytics', ['event_type'], unique=False)
    op.create_index(op.f('ix_analytics_created_at'), 'analytics', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_analytics_created_at'), table_name='analytics')
    op.drop_index(op.f('ix_analytics_event_type'), table_name='analytics')
    op.drop_index(op.f('ix_analytics_project_id'), table_name='analytics')
    
    # Drop table
    op.drop_table('analytics')
