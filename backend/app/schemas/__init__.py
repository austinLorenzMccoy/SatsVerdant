from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


class UserBase(BaseModel):
    wallet_address: str = Field(..., description="Stacks wallet address")
    display_name: Optional[str] = Field(None, description="Optional display name")
    email: Optional[str] = Field(None, description="Optional email address")
    role: str = Field("recycler", description="User role: recycler, validator, admin")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None


class User(UserBase):
    id: str
    created_at: datetime
    last_seen: Optional[datetime]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    submissions_count: int
    tokens_earned: int
    sbtc_earned: str
    carbon_offset_kg: float


class UserWithStats(User):
    stats: UserStats


class WalletChallenge(BaseModel):
    wallet_address: str = Field(..., description="Stacks wallet address")


class WalletChallengeResponse(BaseModel):
    challenge: str = Field(..., description="Message to sign")
    expires_at: datetime = Field(..., description="Challenge expiration time")


class WalletVerify(BaseModel):
    wallet_address: str = Field(..., description="Stacks wallet address")
    signature: str = Field(..., description="Signature of the challenge")
    challenge: str = Field(..., description="The challenge message that was signed")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class SubmissionBase(BaseModel):
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="GPS longitude")
    location_accuracy: Optional[Decimal] = Field(None, ge=0, description="Location accuracy in meters")
    device_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Device information")
    notes: Optional[str] = Field(None, description="Optional user notes")


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionUpdate(BaseModel):
    confirmed_classification: bool = Field(..., description="User confirms AI classification")
    override_weight_kg: Optional[Decimal] = Field(None, ge=0, description="Manual weight override")


class Submission(SubmissionBase):
    id: str
    user_id: str
    image_url: Optional[str]
    thumbnail_url: Optional[str]
    ai_waste_type: Optional[str]
    ai_confidence: Optional[Decimal]
    ai_estimated_weight_kg: Optional[Decimal]
    ai_quality_grade: Optional[str]
    status: str
    validator_id: Optional[str]
    validated_at: Optional[datetime]
    validation_notes: Optional[str]
    mint_tx_id: Optional[str]
    tokens_minted: Optional[int]
    carbon_offset_g: Optional[int]
    minted_at: Optional[datetime]
    fraud_score: Optional[Decimal]
    fraud_flags: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmissionWithUser(Submission):
    user: User


class SubmissionQueueItem(BaseModel):
    id: str
    image_url: Optional[str]
    ai_classification: Dict[str, Any]
    location: Optional[Dict[str, Any]]
    user_history: Dict[str, Any]
    fraud_indicators: Dict[str, Any]
    created_at: datetime
    time_in_queue_minutes: int


class ValidationDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$", description="Validation decision")
    notes: str = Field(..., description="Validation notes")
    override_weight_kg: Optional[Decimal] = Field(None, ge=0)
    override_quality: Optional[str] = Field(None, pattern="^[A-D]$")


class ValidatorBase(BaseModel):
    stx_staked: Decimal = Field(..., ge=0, description="STX amount staked")


class ValidatorCreate(ValidatorBase):
    stake_tx_id: str = Field(..., description="Proof of stake transaction")


class Validator(ValidatorBase):
    id: str
    user_id: str
    stake_tx_id: Optional[str]
    staked_at: Optional[datetime]
    reputation_score: int
    validations_count: int
    approvals_count: int
    rejections_count: int
    accuracy_rate: Optional[Decimal]
    is_active: bool
    suspended_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    user: User

    class Config:
        from_attributes = True


class ValidatorPublic(BaseModel):
    id: str
    wallet_address: str
    stx_staked: str
    reputation_score: int
    validations_count: int
    accuracy_rate: Optional[Decimal]
    is_active: bool
    created_at: datetime


class RewardBase(BaseModel):
    pass


class RewardClaim(BaseModel):
    reward_id: str


class Reward(RewardBase):
    id: str
    user_id: str
    submission_id: Optional[str]
    waste_tokens: int
    sbtc_amount: str
    status: str
    claim_tx_id: Optional[str]
    claimed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RewardSummary(BaseModel):
    total_earned_sbtc: str
    total_earned_tokens: int
    claimable_sbtc: str
    claimable_tokens: int
    claimed_sbtc: str
    pending_rewards: int


class TransactionBase(BaseModel):
    tx_id: str
    tx_type: str
    entity_type: str
    entity_id: str
    status: str
    block_height: Optional[int]
    block_hash: Optional[str]
    confirmations: int
    error_code: Optional[str]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    broadcasted_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    updated_at: datetime


class Transaction(TransactionBase):
    id: str
    user_id: Optional[str]

    class Config:
        from_attributes = True


class GlobalStats(BaseModel):
    total_waste_recycled_kg: float
    total_sbtc_distributed: str
    total_tokens_minted: int
    total_carbon_offset_kg: float
    active_recyclers: int
    active_validators: int
    submissions_last_24h: int
    avg_classification_time_seconds: float
    avg_validation_time_minutes: float
    blockchain: Dict[str, Any]


class UserPublicStats(BaseModel):
    wallet_address: str
    submissions_count: int
    tokens_earned: int
    sbtc_earned: str
    carbon_offset_kg: float
    waste_breakdown: Dict[str, int]
    approval_rate: float
    avg_confidence_score: float
    rank: int
    joined_at: datetime


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    data: List[Any]
    pagination: Dict[str, Any]
