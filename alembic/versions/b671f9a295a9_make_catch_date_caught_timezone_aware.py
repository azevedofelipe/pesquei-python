"""Make catch date_caught timezone-aware

Revision ID: b671f9a295a9
Revises: e25a6a259344
Create Date: 2026-09-28 18:49:22.719498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b671f9a295a9'
down_revision: Union[str, Sequence[str], None] = 'e25a6a259344'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    `catch.date_caught` was a naive `TIMESTAMP` with no stated timezone
    convention, which caused values to silently shift by the server's local
    UTC offset when round-tripped through Postgres. Existing values are
    treated as already being UTC wall-clock times (the convention the
    backend now stores/reads consistently), so they're reinterpreted with
    `AT TIME ZONE 'UTC'` rather than relying on the session's `timezone` GUC.
    """
    op.alter_column(
        'catch',
        'date_caught',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="date_caught AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'catch',
        'date_caught',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        nullable=False,
        postgresql_using="date_caught AT TIME ZONE 'UTC'",
    )
