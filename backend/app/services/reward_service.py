from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from fastapi import HTTPException, status
from app import models, schemas
from app.core.config import settings
from decimal import Decimal
import uuid
from datetime import datetime


class RewardService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_rewards(
        self,
        user: models.User,
        page: int = 1,
        per_page: int = 20,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated list of user's rewards.
        """
        query = self.db.query(models.Reward).filter(models.Reward.user_id == user.id)

        if status_filter:
            if status_filter == "claimable":
                query = query.filter(models.Reward.status == "claimable")
            elif status_filter == "claimed":
                query = query.filter(models.Reward.status == "claimed")
            elif status_filter == "all":
                pass  # No filter
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status filter"
                )

        total = query.count()
        total_pages = (total + per_page - 1) // per_page

        rewards = (
            query.order_by(desc(models.Reward.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return {
            "data": rewards,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }

    def get_reward_summary(self, user: models.User) -> schemas.RewardSummary:
        """
        Get summary of user's rewards.
        """
        # Total earned
        total_earned = (
            self.db.query(
                func.sum(models.Reward.waste_tokens),
                func.sum(models.Reward.sbtc_amount)
            )
            .filter(models.Reward.user_id == user.id)
            .first()
        )

        total_tokens = total_earned[0] or 0
        total_sbtc = total_earned[1] or Decimal('0')

        # Claimable rewards
        claimable = (
            self.db.query(
                func.sum(models.Reward.waste_tokens),
                func.sum(models.Reward.sbtc_amount)
            )
            .filter(
                and_(
                    models.Reward.user_id == user.id,
                    models.Reward.status == "claimable"
                )
            )
            .first()
        )

        claimable_tokens = claimable[0] or 0
        claimable_sbtc = claimable[1] or Decimal('0')

        # Claimed rewards
        claimed = (
            self.db.query(func.sum(models.Reward.sbtc_amount))
            .filter(
                and_(
                    models.Reward.user_id == user.id,
                    models.Reward.status == "claimed"
                )
            )
            .scalar() or Decimal('0')
        )

        # Pending rewards count
        pending_count = (
            self.db.query(func.count(models.Reward.id))
            .filter(
                and_(
                    models.Reward.user_id == user.id,
                    models.Reward.status == "pending"
                )
            )
            .scalar()
        )

        return schemas.RewardSummary(
            total_earned_sbtc=str(total_sbtc),
            total_earned_tokens=total_tokens,
            claimable_sbtc=str(claimable_sbtc),
            claimable_tokens=claimable_tokens,
            claimed_sbtc=str(claimed),
            pending_rewards=pending_count
        )

    def claim_reward(self, reward_id: str, user: models.User) -> models.Reward:
        """
        Claim a specific reward.
        """
        reward = (
            self.db.query(models.Reward)
            .filter(
                and_(
                    models.Reward.id == reward_id,
                    models.Reward.user_id == user.id
                )
            )
            .first()
        )

        if not reward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reward not found"
            )

        if reward.status != "claimable":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reward status is {reward.status}, not claimable"
            )

        # Update reward status
        reward.status = "claimed"
        reward.claimed_at = datetime.utcnow()
        # TODO: Set claim_tx_id after blockchain transaction

        self.db.commit()
        self.db.refresh(reward)

        # TODO: Trigger blockchain claim transaction
        # self._enqueue_reward_claim_transaction(reward.id)

        return reward

    def batch_claim_rewards(self, user: models.User) -> Dict[str, Any]:
        """
        Claim all claimable rewards for a user.
        """
        claimable_rewards = (
            self.db.query(models.Reward)
            .filter(
                and_(
                    models.Reward.user_id == user.id,
                    models.Reward.status == "claimable"
                )
            )
            .all()
        )

        if not claimable_rewards:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No claimable rewards found"
            )

        claimed_rewards = []
        total_tokens = 0
        total_sbtc = Decimal('0')

        for reward in claimable_rewards:
            reward.status = "claimed"
            reward.claimed_at = datetime.utcnow()
            claimed_rewards.append(reward)
            total_tokens += reward.waste_tokens
            total_sbtc += reward.sbtc_amount

        self.db.commit()

        # TODO: Create batch claim transaction

        return {
            "claimed_count": len(claimed_rewards),
            "total_sbtc": str(total_sbtc),
            "total_tokens": total_tokens,
            "claimed_rewards": [str(r.id) for r in claimed_rewards]
        }

    def create_reward(
        self,
        user_id: str,
        submission_id: str,
        waste_tokens: int,
        conversion_rate: Optional[float] = None
    ) -> models.Reward:
        """
        Create a new reward record.
        """
        if conversion_rate is None:
            conversion_rate = 100000.0  # Default: 1000 tokens = 0.1 sBTC

        # Calculate sBTC amount
        sbtc_amount = Decimal(str(waste_tokens)) / Decimal(str(conversion_rate))

        reward = models.Reward(
            user_id=user_id,
            submission_id=submission_id,
            waste_tokens=waste_tokens,
            sbtc_amount=sbtc_amount,
            conversion_rate=Decimal(str(conversion_rate)),
            status="claimable"
        )

        self.db.add(reward)
        self.db.commit()
        self.db.refresh(reward)

        return reward

    def calculate_reward_amount(
        self,
        waste_type: str,
        weight_kg: float,
        quality_grade: str
    ) -> int:
        """
        Calculate token reward based on waste type, weight, and quality.
        """
        # Base multiplier per waste type (tokens per kg)
        base_multipliers = {
            "plastic": 100,
            "paper": 80,
            "metal": 120,
            "organic": 60,
            "electronic": 200  # Higher value for e-waste
        }

        # Quality grade multipliers
        quality_multipliers = {
            "A": 1.0,
            "B": 0.8,
            "C": 0.6,
            "D": 0.4
        }

        base_multiplier = base_multipliers.get(waste_type, 100)
        quality_multiplier = quality_multipliers.get(quality_grade, 1.0)

        # Calculate tokens
        tokens = int(weight_kg * base_multiplier * quality_multiplier)

        # Minimum reward
        return max(tokens, 10)

    def get_reward_estimate(
        self,
        waste_type: str,
        weight_kg: float,
        quality_grade: str,
        conversion_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Estimate reward for a submission.
        """
        tokens = self.calculate_reward_amount(waste_type, weight_kg, quality_grade)

        if conversion_rate is None:
            conversion_rate = 100000.0

        sbtc_amount = Decimal(str(tokens)) / Decimal(str(conversion_rate))

        return {
            "waste_tokens": tokens,
            "sbtc_amount": str(sbtc_amount),
            "conversion_rate": conversion_rate
        }

    def get_total_rewards_distributed(self) -> Decimal:
        """
        Get total sBTC rewards distributed across the platform.
        """
        total = (
            self.db.query(func.sum(models.Reward.sbtc_amount))
            .filter(models.Reward.status == "claimed")
            .scalar() or Decimal('0')
        )
        return total

    def get_pending_rewards_count(self, user: models.User) -> int:
        """
        Get count of pending rewards for a user.
        """
        count = (
            self.db.query(func.count(models.Reward.id))
            .filter(
                and_(
                    models.Reward.user_id == user.id,
                    models.Reward.status == "pending"
                )
            )
            .scalar()
        )
        return count

    def update_reward_status(
        self,
        reward_id: str,
        new_status: str,
        tx_id: Optional[str] = None
    ) -> models.Reward:
        """
        Update reward status (used by background jobs).
        """
        reward = self.db.query(models.Reward).filter(models.Reward.id == reward_id).first()

        if not reward:
            return None

        reward.status = new_status
        if tx_id:
            reward.claim_tx_id = tx_id
        if new_status == "claimed":
            reward.claimed_at = datetime.utcnow()
        elif new_status == "distributed":
            reward.distributed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(reward)

        return reward

    def get_reward_stats(self) -> Dict[str, Any]:
        """
        Get platform-wide reward statistics.
        """
        total_distributed = self.get_total_rewards_distributed()

        total_claimable = (
            self.db.query(func.sum(models.Reward.sbtc_amount))
            .filter(models.Reward.status == "claimable")
            .scalar() or Decimal('0')
        )

        total_pending = (
            self.db.query(func.sum(models.Reward.sbtc_amount))
            .filter(models.Reward.status == "pending")
            .scalar() or Decimal('0')
        )

        # Average reward per submission
        avg_reward = (
            self.db.query(func.avg(models.Reward.sbtc_amount))
            .filter(models.Reward.status.in_(["claimable", "claimed"]))
            .scalar() or Decimal('0')
        )

        return {
            "total_distributed_sbtc": str(total_distributed),
            "total_claimable_sbtc": str(total_claimable),
            "total_pending_sbtc": str(total_pending),
            "average_reward_sbtc": str(avg_reward),
            "total_reward_records": self.db.query(func.count(models.Reward.id)).scalar()
        }
