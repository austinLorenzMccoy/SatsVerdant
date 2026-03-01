import pytest
from app.services.reward_service import RewardService
from app import models
from decimal import Decimal
from uuid import uuid4


class TestRewardService:
    """Test RewardService."""

    def test_get_user_rewards(self, db_session, test_user):
        """Test getting user rewards."""
        service = RewardService(db_session)

        # Create some rewards
        for i in range(2):
            reward = models.Reward(
                user_id=test_user.id,
                submission_id=str(uuid4()),
                waste_tokens=50,
                sbtc_amount=Decimal("0.0005"),
                status="claimable" if i == 0 else "pending"
            )
            db_session.add(reward)
        db_session.commit()

        # Get rewards
        result = service.get_user_rewards(test_user)
        assert len(result["data"]) == 2
        assert result["pagination"]["total"] == 2

        # Get only claimable
        result = service.get_user_rewards(test_user, status="claimable")
        assert len(result["data"]) == 1

    def test_get_reward_summary(self, db_session, test_user):
        """Test getting reward summary."""
        service = RewardService(db_session)

        # Create rewards
        reward1 = models.Reward(
            user_id=test_user.id,
            waste_tokens=50,
            sbtc_amount=Decimal("0.0005"),
            status="claimable"
        )
        reward2 = models.Reward(
            user_id=test_user.id,
            waste_tokens=100,
            sbtc_amount=Decimal("0.001"),
            status="claimed"
        )
        db_session.add(reward1)
        db_session.add(reward2)
        db_session.commit()

        summary = service.get_reward_summary(test_user)

        assert summary.total_earned_tokens == 150
        assert summary.total_earned_sbtc == "0.0015"
        assert summary.claimable_tokens == 50
        assert summary.claimable_sbtc == "0.0005"
        assert summary.claimed_sbtc == "0.001"
        assert summary.pending_rewards == 0

    def test_claim_reward(self, db_session, test_user):
        """Test claiming a reward."""
        service = RewardService(db_session)

        # Create claimable reward
        reward = models.Reward(
            user_id=test_user.id,
            submission_id=str(uuid4()),
            waste_tokens=50,
            sbtc_amount=Decimal("0.0005"),
            status="claimable"
        )
        db_session.add(reward)
        db_session.commit()

        # Claim reward
        claimed = service.claim_reward(str(reward.id), test_user)

        assert claimed.status == "claimed"
        assert claimed.claimed_at is not None

    def test_claim_reward_not_found(self, db_session, test_user):
        """Test claiming non-existent reward."""
        service = RewardService(db_session)

        with pytest.raises(Exception):  # HTTPException
            service.claim_reward(str(uuid4()), test_user)

    def test_claim_reward_not_claimable(self, db_session, test_user):
        """Test claiming non-claimable reward."""
        service = RewardService(db_session)

        # Create pending reward
        reward = models.Reward(
            user_id=test_user.id,
            waste_tokens=50,
            sbtc_amount=Decimal("0.0005"),
            status="pending"
        )
        db_session.add(reward)
        db_session.commit()

        with pytest.raises(Exception):  # HTTPException
            service.claim_reward(str(reward.id), test_user)

    def test_batch_claim_rewards(self, db_session, test_user):
        """Test batch claiming rewards."""
        service = RewardService(db_session)

        # Create multiple claimable rewards
        for i in range(3):
            reward = models.Reward(
                user_id=test_user.id,
                waste_tokens=50,
                sbtc_amount=Decimal("0.0005"),
                status="claimable"
            )
            db_session.add(reward)
        db_session.commit()

        # Batch claim
        result = service.batch_claim_rewards(test_user)

        assert result["claimed_count"] == 3
        assert result["total_tokens"] == 150
        assert result["total_sbtc"] == "0.0015"

    def test_batch_claim_no_rewards(self, db_session, test_user):
        """Test batch claiming with no claimable rewards."""
        service = RewardService(db_session)

        with pytest.raises(Exception):  # HTTPException
            service.batch_claim_rewards(test_user)

    def test_create_reward(self, db_session, test_user):
        """Test creating a reward."""
        service = RewardService(db_session)

        submission_id = str(uuid4())
        reward = service.create_reward(
            user_id=str(test_user.id),
            submission_id=submission_id,
            waste_tokens=75,
            conversion_rate=100000.0
        )

        assert reward.id is not None
        assert reward.user_id == test_user.id
        assert reward.submission_id == submission_id
        assert reward.waste_tokens == 75
        assert reward.sbtc_amount == Decimal("0.00075")
        assert reward.status == "claimable"

    def test_calculate_reward_amount(self, db_session):
        """Test reward amount calculation."""
        service = RewardService(db_session)

        # Test different waste types and qualities
        assert service.calculate_reward_amount("plastic", 1.0, "A") == 100
        assert service.calculate_reward_amount("metal", 1.0, "A") == 120
        assert service.calculate_reward_amount("plastic", 1.0, "C") == 60
        assert service.calculate_reward_amount("plastic", 0.1, "A") == 10  # Minimum

    def test_get_reward_estimate(self, db_session):
        """Test reward estimation."""
        service = RewardService(db_session)

        estimate = service.get_reward_estimate("plastic", 1.5, "A")

        assert estimate["waste_tokens"] == 150
        assert estimate["sbtc_amount"] == "0.0015"
        assert estimate["conversion_rate"] == 100000.0

    def test_update_reward_status(self, db_session, test_user):
        """Test updating reward status."""
        service = RewardService(db_session)

        # Create reward
        reward = models.Reward(
            user_id=test_user.id,
            waste_tokens=50,
            sbtc_amount=Decimal("0.0005"),
            status="pending"
        )
        db_session.add(reward)
        db_session.commit()

        # Update status
        updated = service.update_reward_status(str(reward.id), "claimable")

        assert updated.status == "claimable"

    def test_get_total_rewards_distributed(self, db_session, test_user):
        """Test getting total distributed rewards."""
        service = RewardService(db_session)

        # Create claimed rewards
        reward1 = models.Reward(
            user_id=test_user.id,
            waste_tokens=50,
            sbtc_amount=Decimal("0.0005"),
            status="claimed"
        )
        reward2 = models.Reward(
            user_id=test_user.id,
            waste_tokens=100,
            sbtc_amount=Decimal("0.001"),
            status="claimed"
        )
        db_session.add(reward1)
        db_session.add(reward2)
        db_session.commit()

        total = service.get_total_rewards_distributed()
        assert total == Decimal("0.0015")
