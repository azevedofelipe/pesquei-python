"""Create catch table

Revision ID: 5755f31a0452
Revises: 
Create Date: 2026-08-17 19:01:52.378726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5755f31a0452'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'catch',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('species', sa.String(50), nullable=False),
        sa.Column('weight', sa.Float, nullable=False),
        sa.Column('length', sa.Float, nullable=False),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('date_caught', sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('catch')
