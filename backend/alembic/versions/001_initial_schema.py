"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-01-27 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('wallet_address', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='recycler'),
        sa.Column('display_name', sa.String(100)),
        sa.Column('email', sa.String(255)),
        sa.Column('profile_image_url', sa.Text()),
        sa.Column('bio', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('last_seen', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('image_url', sa.Text()),
        sa.Column('image_s3_key', sa.String(255)),
        sa.Column('image_ipfs_cid', sa.String(100)),
        sa.Column('thumbnail_url', sa.Text()),
        sa.Column('thumbnail_ipfs_cid', sa.String(100)),
        sa.Column('latitude', sa.Numeric(10, 7)),
        sa.Column('longitude', sa.Numeric(10, 7)),
        sa.Column('location_accuracy', sa.Numeric(10, 2)),
        sa.Column('ai_waste_type', sa.String(50), index=True),
        sa.Column('ai_confidence', sa.Numeric(5, 4)),
        sa.Column('ai_estimated_weight_kg', sa.Numeric(10, 2)),
        sa.Column('ai_quality_grade', sa.String(1)),
        sa.Column('ai_metadata', sa.JSON()),
        sa.Column('fraud_score', sa.Numeric(5, 4)),
        sa.Column('fraud_flags', sa.JSON()),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending_classification', index=True),
        sa.Column('validator_id', sa.String(36), index=True),
        sa.Column('validator_notes', sa.Text()),
        sa.Column('tokens_minted', sa.Integer()),
        sa.Column('carbon_offset_g', sa.Integer()),
        sa.Column('mint_tx_id', sa.String(100)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('validated_at', sa.DateTime(timezone=True)),
        sa.Column('minted_at', sa.DateTime(timezone=True)),
        sa.Column('device_info', sa.JSON()),
        sa.Column('client_ip', sa.String(45)),
    )

    # Create validators table
    op.create_table(
        'validators',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True),
        sa.Column('stx_staked', sa.Numeric(18, 6), nullable=False, server_default='0'),
        sa.Column('stake_tx_id', sa.String(100)),
        sa.Column('staked_at', sa.DateTime(timezone=True)),
        sa.Column('reputation_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('validations_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('approvals_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rejections_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accuracy_rate', sa.Numeric(5, 4)),
        sa.Column('is_active', sa.Boolean(), server_default='true', index=True),
        sa.Column('suspended_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_validators_reputation', 'validators', ['reputation_score'], postgresql_ops={'reputation_score': 'DESC'})

    # Create rewards table
    op.create_table(
        'rewards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('submission_id', sa.String(36), sa.ForeignKey('submissions.id', ondelete='SET NULL'), index=True),
        sa.Column('waste_tokens', sa.Integer(), nullable=False),
        sa.Column('sbtc_amount', sa.Numeric(18, 8), nullable=False),
        sa.Column('conversion_rate', sa.Numeric(10, 6)),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', index=True),
        sa.Column('claim_tx_id', sa.String(100)),
        sa.Column('claimed_at', sa.DateTime(timezone=True)),
        sa.Column('distributed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('metadata', sa.JSON()),
    )
    op.create_index('idx_rewards_claimable', 'rewards', ['status', 'user_id'], postgresql_where=sa.text("status = 'claimable'"))

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tx_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('tx_type', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', index=True),
        sa.Column('block_height', sa.Integer()),
        sa.Column('block_hash', sa.String(100)),
        sa.Column('confirmations', sa.Integer(), server_default='0'),
        sa.Column('error_code', sa.String(50)),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('broadcasted_at', sa.DateTime(timezone=True)),
        sa.Column('confirmed_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('raw_payload', sa.JSON()),
        sa.Column('raw_response', sa.JSON()),
    )
    op.create_index('idx_transactions_entity', 'transactions', ['entity_type', 'entity_id'])

    # Create fraud_events table
    op.create_table(
        'fraud_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('submission_id', sa.String(36), sa.ForeignKey('submissions.id', ondelete='CASCADE'), index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True),
        sa.Column('fraud_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('confidence', sa.Numeric(5, 4)),
        sa.Column('description', sa.Text()),
        sa.Column('evidence', sa.JSON()),
        sa.Column('is_resolved', sa.Boolean(), server_default='false'),
        sa.Column('resolved_by', sa.String(36)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolution_notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_fraud_events_severity', 'fraud_events', ['severity', 'is_resolved'])


def downgrade() -> None:
    op.drop_table('fraud_events')
    op.drop_table('transactions')
    op.drop_table('rewards')
    op.drop_table('validators')
    op.drop_table('submissions')
    op.drop_table('users')
