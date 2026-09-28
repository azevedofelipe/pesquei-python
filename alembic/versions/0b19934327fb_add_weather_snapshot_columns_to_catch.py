"""Add weather snapshot columns to catch

Revision ID: 0b19934327fb
Revises: e25a6a259344
Create Date: 2026-09-28 18:52:47.338517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b19934327fb'
down_revision: Union[str, Sequence[str], None] = 'e25a6a259344'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('catch', sa.Column('temperature', sa.Numeric(5, 2), nullable=True))
    op.add_column('catch', sa.Column('conditions', sa.String(100), nullable=True))
    op.add_column('catch', sa.Column('sunrise', sa.DateTime(), nullable=True))
    op.add_column('catch', sa.Column('sunset', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('catch', 'sunset')
    op.drop_column('catch', 'sunrise')
    op.drop_column('catch', 'conditions')
    op.drop_column('catch', 'temperature')
