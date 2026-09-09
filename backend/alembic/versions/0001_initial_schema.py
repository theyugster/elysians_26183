"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-03-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'vasp_registry',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('exchange_name', sa.String(length=120), nullable=False),
        sa.Column('hot_wallet_address', sa.String(length=100), nullable=False),
        sa.Column('network', sa.String(length=20), nullable=False),
        sa.Column('jurisdiction', sa.String(length=100), nullable=False),
        sa.Column('is_compliant', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vasp_registry_hot_wallet_address'), 'vasp_registry', ['hot_wallet_address'], unique=True)

    op.create_table(
        'wallets',
        sa.Column('address', sa.String(length=100), nullable=False),
        sa.Column('network', sa.String(length=20), nullable=False),
        sa.Column('cluster_type', sa.String(length=50), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('heuristic_breakdown', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('address')
    )
    op.create_index(op.f('ix_wallets_address'), 'wallets', ['address'], unique=False)

    op.create_table(
        'transactions',
        sa.Column('tx_hash', sa.String(length=100), nullable=False),
        sa.Column('network', sa.String(length=20), nullable=False),
        sa.Column('from_address', sa.String(length=100), nullable=False),
        sa.Column('to_address', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('token', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('latency_seconds', sa.Integer(), nullable=False),
        sa.Column('gas_sponsor', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['from_address'], ['wallets.address']),
        sa.ForeignKeyConstraint(['to_address'], ['wallets.address']),
        sa.PrimaryKeyConstraint('tx_hash')
    )
    op.create_index(op.f('ix_transactions_tx_hash'), 'transactions', ['tx_hash'], unique=False)

    op.create_table(
        'requisitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dossier_id', sa.String(length=64), nullable=False),
        sa.Column('officer_id', sa.String(length=100), nullable=False),
        sa.Column('target_wallet', sa.String(length=100), nullable=False),
        sa.Column('terminal_exchange', sa.String(length=120), nullable=False),
        sa.Column('sha256_audit_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requisitions_dossier_id'), 'requisitions', ['dossier_id'], unique=True)

def downgrade():
    op.drop_table('requisitions')
    op.drop_table('transactions')
    op.drop_table('wallets')
    op.drop_table('vasp_registry')
