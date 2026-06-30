"""add_auth_fields_and_tables

Revision ID: 5eeb72756f53
Revises: 
Create Date: 2026-06-29 05:18:16.928147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5eeb72756f53'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Seed mock customer_fetch_sessions row to satisfy transactions foreign key
    op.execute("INSERT INTO customer_fetch_sessions (id, biller_id, fetch_ref_id, customer_params, status, created_at) VALUES ('979dbe10-4972-4fa0-9c88-9b9a39710000', 'HDFC00000NAT01', 'MOCK-FETCH-REF-001', '{\"mobile\": \"9876543210\"}'::json, 'SUCCESS', '2026-06-29 00:00:00') ON CONFLICT (id) DO NOTHING;")

    # 1. Create balances table
    op.create_table('balances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('currency', sa.String(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_balances_currency'), 'balances', ['currency'], unique=False)
    op.create_index(op.f('ix_balances_id'), 'balances', ['id'], unique=False)

    # 2. Add columns to transactions table
    op.add_column('transactions', sa.Column('sender_id', sa.UUID(), nullable=True))
    op.add_column('transactions', sa.Column('recipient_id', sa.UUID(), nullable=True))
    op.add_column('transactions', sa.Column('source_currency', sa.String(), nullable=True))
    op.add_column('transactions', sa.Column('target_currency', sa.String(), nullable=True))
    op.add_column('transactions', sa.Column('source_amount', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('target_amount', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('tx_hash', sa.String(), nullable=True))
    op.add_column('transactions', sa.Column('timestamp', sa.Float(), nullable=True))

    op.create_index(op.f('ix_transactions_tx_hash'), 'transactions', ['tx_hash'], unique=True)
    op.create_foreign_key(None, 'transactions', 'users', ['sender_id'], ['id'])
    op.create_foreign_key(None, 'transactions', 'users', ['recipient_id'], ['id'])

    # 3. Add columns to users table
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('username', sa.String(), nullable=True))
    op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
    op.add_column('users', sa.Column('preferred_currency', sa.String(), nullable=True, server_default='USDT'))

    # 4. Set unique values dynamically for the pre-existing users so that we can create UNIQUE indices
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id, first_name, last_name FROM users"))
    users = result.fetchall()
    
    for u in users:
        u_id = u[0]
        first_name = u[1]
        last_name = u[2]
        
        username = first_name.lower()
        email = f"{username}@example.com"
        
        pref_curr = 'USDT'
        if username == 'priya':
            pref_curr = 'USDC'
        elif username == 'sanjay':
            pref_curr = 'ETH'
        elif username == 'varun':
            pref_curr = 'SOL'
            
        connection.execute(sa.text(
            "UPDATE users SET email = :email, username = :username, preferred_currency = :pref_curr WHERE id = :id"
        ), {"email": email, "username": username, "pref_curr": pref_curr, "id": u_id})
        
        # 5. Populate initial balances for these users so they have starting assets
        connection.execute(sa.text("INSERT INTO balances (user_id, currency, amount) VALUES (:id, 'USDT', 10000.0)"), {"id": u_id})
        connection.execute(sa.text("INSERT INTO balances (user_id, currency, amount) VALUES (:id, 'USDC', 10000.0)"), {"id": u_id})
        connection.execute(sa.text("INSERT INTO balances (user_id, currency, amount) VALUES (:id, 'ETH', 10.0)"), {"id": u_id})
        connection.execute(sa.text("INSERT INTO balances (user_id, currency, amount) VALUES (:id, 'SOL', 100.0)"), {"id": u_id})

    # 6. Create unique indexes on email and username since now all values are unique and non-null
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    # 1. Drop indices
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    
    # 2. Drop columns from users
    op.drop_column('users', 'preferred_currency')
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'username')
    op.drop_column('users', 'email')

    # 3. Drop columns and foreign keys from transactions
    op.drop_constraint(None, 'transactions', type_='foreignkey')
    op.drop_constraint(None, 'transactions', type_='foreignkey')
    op.drop_index(op.f('ix_transactions_tx_hash'), table_name='transactions')
    
    op.drop_column('transactions', 'timestamp')
    op.drop_column('transactions', 'tx_hash')
    op.drop_column('transactions', 'target_amount')
    op.drop_column('transactions', 'source_amount')
    op.drop_column('transactions', 'target_currency')
    op.drop_column('transactions', 'source_currency')
    op.drop_column('transactions', 'recipient_id')
    op.drop_column('transactions', 'sender_id')

    # 4. Drop balances table
    op.drop_index(op.f('ix_balances_id'), table_name='balances')
    op.drop_index(op.f('ix_balances_currency'), table_name='balances')
    op.drop_table('balances')
