import pytest
from app import models, schemas
from datetime import datetime
from decimal import Decimal


class TestUserModel:
    """Test User model."""

    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = models.User(
            wallet_address="ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
            role="recycler"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.wallet_address == "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        assert user.role == "recycler"
        assert user.created_at is not None

    def test_user_unique_wallet(self, db_session):
        """Test wallet address uniqueness."""
        user1 = models.User(
            wallet_address="ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
            role="recycler"
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create duplicate
        user2 = models.User(
            wallet_address="ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
            role="recycler"
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestSubmissionModel:
    """Test Submission model."""

    def test_submission_creation(self, db_session, test_user):
        """Test creating a submission."""
        submission = models.Submission(
            user_id=test_user.id,
            status="pending_classification"
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert submission.id is not None
        assert submission.user_id == test_user.id
        assert submission.status == "pending_classification"
        assert submission.created_at is not None
        assert submission.updated_at is not None

    def test_submission_with_location(self, db_session, test_user):
        """Test submission with GPS coordinates."""
        submission = models.Submission(
            user_id=test_user.id,
            latitude=Decimal("52.3676"),
            longitude=Decimal("4.9041"),
            location_accuracy=Decimal("10.5"),
            status="pending_classification"
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)

        assert submission.latitude == Decimal("52.3676")
        assert submission.longitude == Decimal("4.9041")
        assert submission.location_accuracy == Decimal("10.5")


class TestValidatorModel:
    """Test Validator model."""

    def test_validator_creation(self, db_session, test_user):
        """Test creating a validator."""
        validator = models.Validator(
            user_id=test_user.id,
            stx_staked=1000.0,
            reputation_score=100
        )
        db_session.add(validator)
        db_session.commit()
        db_session.refresh(validator)

        assert validator.id is not None
        assert validator.user_id == test_user.id
        assert validator.stx_staked == 1000.0
        assert validator.reputation_score == 100
        assert validator.validations_count == 0
        assert validator.approvals_count == 0
        assert validator.rejections_count == 0
        assert validator.is_active is True


class TestRewardModel:
    """Test Reward model."""

    def test_reward_creation(self, db_session, test_user):
        """Test creating a reward."""
        from uuid import uuid4
        submission_id = str(uuid4())

        reward = models.Reward(
            user_id=test_user.id,
            submission_id=submission_id,
            waste_tokens=50,
            sbtc_amount=Decimal("0.0005"),
            conversion_rate=Decimal("100000.0")
        )
        db_session.add(reward)
        db_session.commit()
        db_session.refresh(reward)

        assert reward.id is not None
        assert reward.user_id == test_user.id
        assert reward.submission_id == submission_id
        assert reward.waste_tokens == 50
        assert reward.sbtc_amount == Decimal("0.0005")
        assert reward.status == "pending"


class TestSchemas:
    """Test Pydantic schemas."""

    def test_user_schema(self):
        """Test User schema validation."""
        user_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
            "role": "recycler",
            "created_at": datetime.utcnow()
        }
        user = schemas.User(**user_data)
        assert user.wallet_address == "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        assert user.role == "recycler"

    def test_submission_create_schema(self):
        """Test SubmissionCreate schema."""
        submission_data = {
            "latitude": 52.3676,
            "longitude": 4.9041,
            "location_accuracy": 10.5,
            "notes": "Plastic bottles"
        }
        submission = schemas.SubmissionCreate(**submission_data)
        assert submission.latitude == Decimal("52.3676")
        assert submission.longitude == Decimal("4.9041")
        assert submission.notes == "Plastic bottles"

    def test_validator_create_schema(self):
        """Test ValidatorCreate schema."""
        validator_data = {
            "stx_staked": 1000.0,
            "stake_tx_id": "0x1234567890abcdef"
        }
        validator = schemas.ValidatorCreate(**validator_data)
        assert validator.stx_staked == Decimal("1000.0")
        assert validator.stake_tx_id == "0x1234567890abcdef"

    def test_reward_schema(self):
        """Test Reward schema."""
        reward_data = {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "waste_tokens": 50,
            "sbtc_amount": "0.0005",
            "status": "claimable",
            "created_at": datetime.utcnow()
        }
        reward = schemas.Reward(**reward_data)
        assert reward.waste_tokens == 50
        assert reward.sbtc_amount == "0.0005"
        assert reward.status == "claimable"
