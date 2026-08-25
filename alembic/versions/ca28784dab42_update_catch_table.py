"""Update catch table, swap location for lat and long and add the lure_id foreign key and notes and depth for the catch log

Revision ID: ca28784dab42
Revises: effff0102dcd
Create Date: 2026-08-24 22:52:37.467406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca28784dab42'
down_revision: Union[str, Sequence[str], None] = 'effff0102dcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'catch',
        sa.Column('latitude', sa.Numeric(9, 6), nullable=True)
    )
    op.add_column(
        'catch',
        sa.Column('longitude', sa.Numeric(9, 6), nullable=True)
    )
    op.add_column(
        'catch',
        sa.Column(
            'lure_id',
            sa.Integer,
            sa.ForeignKey('lure.id'),
            nullable=True
        )
    )
    op.add_column(
        'catch',
        sa.Column('depth', sa.Numeric(6, 2), nullable=True)
    )
    op.add_column(
        'catch',
        sa.Column('notes', sa.Text, nullable=True)
    )

    op.drop_column('catch', 'location')

    op.alter_column(
        'catch',
        'species',
        existing_type=sa.String(50),
        nullable=True
    )
    op.alter_column(
        'catch',
        'weight',
        existing_type=sa.Float(),
        type_=sa.Numeric(6, 2),
        nullable=True
    )
    op.alter_column(
        'catch',
        'length',
        existing_type=sa.Float(),
        type_=sa.Numeric(6, 2),
        nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'catch',
        sa.Column('location', sa.String(100), nullable=True)
    )

    op.drop_column('catch', 'notes')
    op.drop_column('catch', 'depth')
    op.drop_column('catch', 'lure_id')
    op.drop_column('catch', 'longitude')
    op.drop_column('catch', 'latitude')

    op.alter_column(
        'catch',
        'species',
        existing_type=sa.String(50),
        nullable=False
    )
    op.alter_column(
        'catch',
        'weight',
        existing_type=sa.Numeric(6, 2),
        type_=sa.Float(),
        nullable=False
    )
    op.alter_column(
        'catch',
        'length',
        existing_type=sa.Numeric(6, 2),
        type_=sa.Float(),
        nullable=False
    )