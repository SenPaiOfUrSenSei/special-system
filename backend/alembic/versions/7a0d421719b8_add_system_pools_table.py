"""add_system_pools_table

Revision ID: 7a0d421719b8
Revises: 4484feb04090
Create Date: 2026-06-29 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a0d421719b8'
down_revision: Union[str, Sequence[str], None] = '4484feb04090'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create system_pools table
    op.create_table(
        'system_pools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('tracked_balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('exposure', sa.Float(), nullable=False, server_default='0.0'),
        sa.PrimaryKeyConstraint('id')
    )
    # Create index on currency
    op.create_index(op.f('ix_system_pools_currency'), 'system_pools', ['currency'], unique=True)
    op.create_index(op.f('ix_system_pools_id'), 'system_pools', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_system_pools_id'), table_name='system_pools')
    op.drop_index(op.f('ix_system_pools_currency'), table_name='system_pools')
    op.drop_table('system_pools')
