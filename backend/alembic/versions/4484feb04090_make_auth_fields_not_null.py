"""make_auth_fields_not_null

Revision ID: 4484feb04090
Revises: 5eeb72756f53
Create Date: 2026-06-29 05:21:31.634549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4484feb04090'
down_revision: Union[str, Sequence[str], None] = '5eeb72756f53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update existing 3 users to have a default password hash (hash of "password123") so NOT NULL constraint is satisfied
    op.execute("UPDATE users SET hashed_password = '$2b$12$mEeEkMprrra8r8Y86exdEuKaCUmCR1h4iL91O307zLhDLb.gat1KO' WHERE hashed_password IS NULL")

    # 2. Make columns non-nullable
    op.alter_column('users', 'email', existing_type=sa.String(), nullable=False)
    op.alter_column('users', 'username', existing_type=sa.String(), nullable=False)
    op.alter_column('users', 'hashed_password', existing_type=sa.String(), nullable=False)
    op.alter_column('users', 'preferred_currency', existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    op.alter_column('users', 'email', existing_type=sa.String(), nullable=True)
    op.alter_column('users', 'username', existing_type=sa.String(), nullable=True)
    op.alter_column('users', 'hashed_password', existing_type=sa.String(), nullable=True)
    op.alter_column('users', 'preferred_currency', existing_type=sa.String(), nullable=True)
