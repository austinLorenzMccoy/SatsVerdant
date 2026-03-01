from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, DECIMAL, JSON, ForeignKey, Index, text, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_address = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    email = Column(String(255))
    role = Column(String(20), nullable=False, default="recycler")
    created_at = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime)
    metadata = Column(JSON, default=dict)

    # Relationships
    submissions = relationship("Submission", back_populates="user")
    rewards = relationship("Reward", back_populates="user")
    validator = relationship("Validator", back_populates="user", uselist=False)

    __table_args__ = (
        Index("idx_users_wallet", "wallet_address"),
        Index("idx_users_role", "role"),
    )


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Image data
    image_s3_key = Column(String(255))
    image_ipfs_cid = Column(String(100))
    image_url = Column(Text)
    thumbnail_url = Column(Text)

    # Location
    latitude = Column(DECIMAL(10, 7))
    longitude = Column(DECIMAL(10, 7))
    location_accuracy = Column(DECIMAL(10, 2))  # meters

    # AI Classification
    ai_waste_type = Column(String(50))
    ai_confidence = Column(DECIMAL(5, 4))
    ai_estimated_weight_kg = Column(DECIMAL(10, 2))
    ai_quality_grade = Column(String(1))
    ai_metadata = Column(JSON, default=dict)

    # Status workflow
    status = Column(String(50), nullable=False, default="pending_classification")
    validator_id = Column(String(36), ForeignKey("users.id"), index=True)
    validated_at = Column(DateTime)
    validation_notes = Column(Text)

    # Minting
    mint_tx_id = Column(String(100))
    tokens_minted = Column(Integer)
    carbon_offset_g = Column(Integer)
    minted_at = Column(DateTime)

    # Fraud detection
    fraud_score = Column(DECIMAL(5, 4))
    fraud_flags = Column(JSON, default=list)
    duplicate_of = Column(String(36), ForeignKey("submissions.id"))

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Metadata
    device_info = Column(JSON, default=dict)
    client_ip = Column(String(45))

    # Relationships
    user = relationship("User", back_populates="submissions")
    rewards = relationship("Reward", back_populates="submission")

    __table_args__ = (
        Index("idx_submissions_user", "user_id"),
        Index("idx_submissions_status", "status"),
        Index("idx_submissions_validator", "validator_id"),
        Index("idx_submissions_created", "created_at"),
        Index("idx_submissions_type", "ai_waste_type"),
    )


class Validator(Base):
    __tablename__ = "validators"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Staking
    stx_staked = Column(DECIMAL(18, 6), nullable=False, default=0)
    stake_tx_id = Column(String(100))
    staked_at = Column(DateTime)

    # Performance
    reputation_score = Column(Integer, nullable=False, default=100)
    validations_count = Column(Integer, nullable=False, default=0)
    approvals_count = Column(Integer, nullable=False, default=0)
    rejections_count = Column(Integer, nullable=False, default=0)
    accuracy_rate = Column(DECIMAL(5, 4))

    # Status
    is_active = Column(Boolean, default=True)
    suspended_until = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="validator")

    __table_args__ = (
        Index("idx_validators_user", "user_id"),
        Index("idx_validators_active", "is_active"),
        Index("idx_validators_reputation", "reputation_score"),
    )


class Reward(Base):
    __tablename__ = "rewards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="SET NULL"), index=True)

    # Reward details
    waste_tokens = Column(Integer, nullable=False)
    sbtc_amount = Column(DECIMAL(18, 8), nullable=False)
    conversion_rate = Column(DECIMAL(10, 6))

    # Status
    status = Column(String(20), nullable=False, default="pending")

    # Transaction
    claim_tx_id = Column(String(100))
    claimed_at = Column(DateTime)
    distributed_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Metadata
    metadata = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="rewards")
    submission = relationship("Submission", back_populates="rewards")

    __table_args__ = (
        Index("idx_rewards_user", "user_id"),
        Index("idx_rewards_submission", "submission_id"),
        Index("idx_rewards_status", "status"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Transaction details
    tx_id = Column(String(100), unique=True, nullable=False, index=True)
    tx_type = Column(String(50), nullable=False)

    # Related entities
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)

    # Status
    status = Column(String(20), nullable=False, default="pending")

    # Blockchain data
    block_height = Column(Integer)
    block_hash = Column(String(100))
    confirmations = Column(Integer, default=0)

    # Error handling
    error_code = Column(String(50))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    broadcasted_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Raw data
    raw_payload = Column(JSON)
    raw_response = Column(JSON)

    __table_args__ = (
        Index("idx_transactions_tx_id", "tx_id"),
        Index("idx_transactions_entity", "entity_type", "entity_id"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_user", "user_id"),
        Index("idx_transactions_created", "created_at"),
    )


class FraudEvent(Base):
    __tablename__ = "fraud_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Fraud detection
    fraud_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="medium")
    confidence = Column(DECIMAL(5, 4))

    # Details
    description = Column(Text)
    evidence = Column(JSON, default=dict)

    # Actions
    action_taken = Column(Text)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(36), ForeignKey("users.id"))

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_fraud_events_submission", "submission_id"),
        Index("idx_fraud_events_user", "user_id"),
        Index("idx_fraud_events_type", "fraud_type"),
        Index("idx_fraud_events_resolved", "resolved"),
    )
