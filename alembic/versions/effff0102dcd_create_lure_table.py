"""create lure table

Revision ID: effff0102dcd
Revises: 5755f31a0452
Create Date: 2026-08-24 22:41:24.328620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'effff0102dcd'
down_revision: Union[str, Sequence[str], None] = '5755f31a0452'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'lure',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=True),
        sa.Column('weight', sa.Numeric(6, 2), nullable=True),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('color', sa.String(100), nullable=True),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('size', sa.Numeric(6, 2), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('lure')
