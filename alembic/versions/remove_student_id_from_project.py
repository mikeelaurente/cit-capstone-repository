"""Remove student_id from projects and make user_id NOT NULL

Revision ID: remove_student_id
Revises: add_user_id_to_project
Create Date: 2025-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'remove_student_id'
down_revision = 'add_user_id_to_project'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, migrate any student_id to user_id for existing projects
    connection = op.get_bind()
    
    # Check if student_id column exists before trying to migrate
    inspector_obj = inspect(connection)
    columns = [col['name'] for col in inspector_obj.get_columns('projects')]
    
    if 'student_id' in columns:
        # Get all projects that have student_id but no user_id
        result = connection.execute(sa.text("""
            SELECT p.id, s.user_id 
            FROM projects p 
            JOIN students s ON p.student_id = s.id 
            WHERE p.user_id IS NULL
        """))
        
        rows = result.fetchall()
        for row in rows:
            project_id, user_id = row
            connection.execute(sa.text("""
                UPDATE projects SET user_id = :user_id WHERE id = :project_id
            """), {"user_id": user_id, "project_id": project_id})
        
        connection.commit()
        
        # SQLite doesn't support dropping columns directly in batch mode
        # We need to recreate the table
        with op.batch_alter_table('projects', schema=None) as batch_op:
            # Make user_id NOT NULL since all projects must have an uploader
            batch_op.alter_column('user_id',
                       existing_type=sa.Integer(),
                       nullable=False)
            # Drop the foreign key constraint for student_id
            batch_op.drop_constraint('fk_projects_student_id', type_='foreignkey')
            # Drop the student_id column
            batch_op.drop_column('student_id')


def downgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        # Re-add the student_id column
        batch_op.add_column(sa.Column('student_id', sa.Integer(), nullable=True))
        # Re-add the foreign key constraint
        batch_op.create_foreign_key('fk_projects_student_id', 'students', ['student_id'], ['id'], ondelete='CASCADE')
        # Revert user_id back to nullable
        batch_op.alter_column('user_id',
                   existing_type=sa.Integer(),
                   nullable=True)
