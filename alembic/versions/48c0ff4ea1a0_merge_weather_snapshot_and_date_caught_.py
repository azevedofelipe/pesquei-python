"""merge weather-snapshot and date_caught-timezone-fix heads

Revision ID: 48c0ff4ea1a0
Revises: 0b19934327fb, b671f9a295a9
Create Date: 2026-09-28 19:38:18.022984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48c0ff4ea1a0'
down_revision: Union[str, Sequence[str], None] = ('0b19934327fb', 'b671f9a295a9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
