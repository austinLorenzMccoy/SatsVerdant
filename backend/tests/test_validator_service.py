import pytest
from app.services.validator_service import ValidatorService
from app import models, schemas
from decimal import Decimal


class TestValidatorService:
    """Test ValidatorService."""

    def test_create_validator(self, db_session, test_user):
        """Test creating a validator."""
        service = ValidatorService(db_session)

        validator_data = schemas.ValidatorCreate(
            stx_staked=Decimal("1000.0"),
            stake_tx_id="0x1234567890abcdef"
        )

        validator = service.create_validator(test_user, validator_data)

        assert validator.id is not None
        assert validator.user_id == test_user.id
        assert validator.stx_staked == 1000.0
        assert validator.reputation_score == 100
        assert validator.is_active is True

    def test_create_validator_already_exists(self, db_session, test_validator):
        """Test creating validator when one already exists."""
        service = ValidatorService(db_session)

        validator_data = schemas.ValidatorCreate(
            stx_staked=Decimal("500.0"),
            stake_tx_id="0xabcdef1234567890"
        )

        with pytest.raises(Exception):  # HTTPException
            service.create_validator(test_validator.user, validator_data)

    def test_get_validator(self, db_session, test_validator):
        """Test getting a validator."""
        service = ValidatorService(db_session)

        validator = service.get_validator(str(test_validator.id))
        assert validator.id == test_validator.id

    def test_get_validator_not_found(self, db_session):
        """Test getting non-existent validator."""
        service = ValidatorService(db_session)

        with pytest.raises(Exception):  # HTTPException
            service.get_validator("non-existent-id")

    def test_get_validator_by_user(self, db_session, test_validator):
        """Test getting validator by user."""
        service = ValidatorService(db_session)

        validator = service.get_validator_by_user(test_validator.user)
        assert validator.id == test_validator.id

    def test_get_validator_by_user_not_validator(self, db_session, test_user):
        """Test getting validator for non-validator user."""
        service = ValidatorService(db_session)

        with pytest.raises(Exception):  # HTTPException
            service.get_validator_by_user(test_user)

    def test_get_validators(self, db_session, test_validator):
        """Test getting validators list."""
        service = ValidatorService(db_session)

        result = service.get_validators()
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == str(test_validator.id)
        assert result["data"][0]["stx_staked"] == "1000.000000"
        assert result["pagination"]["total"] == 1

    def test_update_validator_reputation(self, db_session, test_validator):
        """Test updating validator reputation."""
        service = ValidatorService(db_session)
        admin_user = models.User(wallet_address="STADMIN...", role="admin")
        db_session.add(admin_user)
        db_session.commit()

        updated = service.update_validator_reputation(str(test_validator.id), 95, admin_user)

        assert updated.reputation_score == 95

    def test_update_validator_reputation_not_admin(self, db_session, test_validator, test_user):
        """Test updating reputation without admin rights."""
        service = ValidatorService(db_session)

        with pytest.raises(Exception):  # HTTPException
            service.update_validator_reputation(str(test_validator.id), 95, test_user)

    def test_suspend_validator(self, db_session, test_validator):
        """Test suspending a validator."""
        service = ValidatorService(db_session)
        admin_user = models.User(wallet_address="STADMIN...", role="admin")
        db_session.add(admin_user)
        db_session.commit()

        suspended = service.suspend_validator(str(test_validator.id), "Poor performance", admin_user)

        assert suspended.is_active is False

    def test_reactivate_validator(self, db_session, test_validator):
        """Test reactivating a validator."""
        service = ValidatorService(db_session)
        admin_user = models.User(wallet_address="STADMIN...", role="admin")
        db_session.add(admin_user)
        db_session.commit()

        # First suspend
        test_validator.is_active = False
        db_session.commit()

        # Then reactivate
        reactivated = service.reactivate_validator(str(test_validator.id), admin_user)

        assert reactivated.is_active is True

    def test_unstake_validator(self, db_session, test_validator):
        """Test unstaking a validator."""
        service = ValidatorService(db_session)

        unstaked = service.unstake_validator(test_validator.user)

        assert unstaked.is_active is False

    def test_get_validator_stats(self, db_session, test_validator):
        """Test getting validator statistics."""
        service = ValidatorService(db_session)

        stats = service.get_validator_stats(test_validator)

        assert stats["validator_id"] == str(test_validator.id)
        assert stats["validations_completed"] == 0
        assert stats["is_active"] is True
        assert "recent_validations" in stats
