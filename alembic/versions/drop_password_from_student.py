"""Drop password column from students table

Revision ID: drop_password_from_student
Revises: add_user_id_to_student
Create Date: 2026-01-12 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'drop_password_from_student'
down_revision: Union[str, None] = 'add_user_id_to_student'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.drop_column('password')


def downgrade() -> None:
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password', sa.String(), nullable=True))
