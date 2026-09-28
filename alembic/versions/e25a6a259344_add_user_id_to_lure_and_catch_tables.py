"""Add user_id to lure and catch tables

Revision ID: e25a6a259344
Revises: 449add81a608
Create Date: 2026-09-28 01:57:17.589457

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e25a6a259344'
down_revision: Union[str, Sequence[str], None] = '449add81a608'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('lure', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key('lure_user_id_fkey', 'lure', 'user', ['user_id'], ['id'])

    op.add_column('catch', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key('catch_user_id_fkey', 'catch', 'user', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('catch_user_id_fkey', 'catch', type_='foreignkey')
    op.drop_column('catch', 'user_id')

    op.drop_constraint('lure_user_id_fkey', 'lure', type_='foreignkey')
    op.drop_column('lure', 'user_id')
