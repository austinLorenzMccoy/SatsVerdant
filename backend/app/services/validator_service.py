from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status
from app import models, schemas
from app.core.config import settings
import uuid


class ValidatorService:
    def __init__(self, db: Session):
        self.db = db

    def create_validator(
        self,
        user: models.User,
        validator_data: schemas.ValidatorCreate
    ) -> models.Validator:
        """
        Register a user as a validator.
        """
        # Check if user already has a validator account
        existing_validator = (
            self.db.query(models.Validator)
            .filter(models.Validator.user_id == user.id)
            .first()
        )

        if existing_validator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a validator"
            )

        # Verify minimum stake
        if validator_data.stx_staked < settings.STACKS_MIN_STAKE_AMOUNT:  # Assuming we add this to settings
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum stake amount is {settings.STACKS_MIN_STAKE_AMOUNT} STX"
            )

        # Create validator record
        validator = models.Validator(
            user_id=user.id,
            stx_staked=float(validator_data.stx_staked),
            stake_tx_id=validator_data.stake_tx_id,
            staked_at=None,  # Will be set when transaction confirms
            reputation_score=100,
            is_active=False  # Will be activated when stake confirms
        )

        self.db.add(validator)
        self.db.commit()
        self.db.refresh(validator)

        # TODO: Verify stake transaction and activate validator
        # For MVP, we'll activate immediately
        validator.is_active = True
        validator.staked_at = validator.created_at
        self.db.commit()

        return validator

    def get_validator(self, validator_id: str) -> models.Validator:
        """
        Get validator by ID.
        """
        validator = (
            self.db.query(models.Validator)
            .filter(models.Validator.id == validator_id)
            .first()
        )

        if not validator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validator not found"
            )

        return validator

    def get_validator_by_user(self, user: models.User) -> models.Validator:
        """
        Get validator for a user.
        """
        validator = (
            self.db.query(models.Validator)
            .filter(models.Validator.user_id == user.id)
            .first()
        )

        if not validator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a validator"
            )

        return validator

    def get_validators(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "reputation_score",
        order: str = "desc",
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Get paginated list of validators.
        """
        query = self.db.query(models.Validator)

        if active_only:
            query = query.filter(models.Validator.is_active == True)

        # Sorting
        sort_column = getattr(models.Validator, sort_by, models.Validator.reputation_score)
        if order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        total = query.count()
        total_pages = (total + per_page - 1) // per_page

        validators = (
            query.options(self.db.joinedload(models.Validator.user))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        # Convert to public schema
        validator_data = []
        for validator in validators:
            validator_data.append({
                "id": str(validator.id),
                "wallet_address": validator.user.wallet_address,
                "stx_staked": f"{validator.stx_staked:.6f}",
                "reputation_score": validator.reputation_score,
                "validations_count": validator.validations_count,
                "accuracy_rate": float(validator.accuracy_rate) if validator.accuracy_rate else None,
                "is_active": validator.is_active,
                "created_at": validator.created_at
            })

        return {
            "data": validator_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }

    def update_validator_reputation(
        self,
        validator_id: str,
        new_score: int,
        admin_user: models.User
    ) -> models.Validator:
        """
        Update validator reputation score (admin only).
        """
        if admin_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update reputation scores"
            )

        validator = self.get_validator(validator_id)

        # Clamp score between 0 and 100
        new_score = max(0, min(100, new_score))
        validator.reputation_score = new_score

        # Update accuracy rate
        if validator.validations_count > 0:
            validator.accuracy_rate = validator.approvals_count / validator.validations_count

        self.db.commit()
        self.db.refresh(validator)

        return validator

    def suspend_validator(
        self,
        validator_id: str,
        reason: str,
        admin_user: models.User
    ) -> models.Validator:
        """
        Suspend a validator (admin only).
        """
        if admin_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can suspend validators"
            )

        validator = self.get_validator(validator_id)

        validator.is_active = False
        validator.suspended_until = None  # Permanent suspension for MVP

        self.db.commit()
        self.db.refresh(validator)

        return validator

    def reactivate_validator(
        self,
        validator_id: str,
        admin_user: models.User
    ) -> models.Validator:
        """
        Reactivate a suspended validator (admin only).
        """
        if admin_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can reactivate validators"
            )

        validator = self.get_validator(validator_id)

        validator.is_active = True
        validator.suspended_until = None

        self.db.commit()
        self.db.refresh(validator)

        return validator

    def unstake_validator(self, user: models.User) -> models.Validator:
        """
        Unstake and remove validator status.
        """
        validator = self.get_validator_by_user(user)

        if not validator.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Validator is already inactive"
            )

        # TODO: Handle STX unstaking on blockchain
        # For MVP, we'll just deactivate
        validator.is_active = False

        self.db.commit()
        self.db.refresh(validator)

        return validator

    def get_validator_stats(self, validator: models.Validator) -> Dict[str, Any]:
        """
        Get detailed statistics for a validator.
        """
        # Recent validations
        recent_validations = (
            self.db.query(models.Submission)
            .filter(models.Submission.validator_id == validator.user_id)
            .order_by(desc(models.Submission.validated_at))
            .limit(10)
            .all()
        )

        # Approval rate over time
        approval_trends = []  # TODO: Implement time-based approval tracking

        return {
            "validator_id": str(validator.id),
            "validations_completed": validator.validations_count,
            "approvals_count": validator.approvals_count,
            "rejections_count": validator.rejections_count,
            "accuracy_rate": float(validator.accuracy_rate) if validator.accuracy_rate else None,
            "reputation_score": validator.reputation_score,
            "stx_staked": float(validator.stx_staked),
            "is_active": validator.is_active,
            "recent_validations": [
                {
                    "id": str(sub.id),
                    "waste_type": sub.ai_waste_type,
                    "status": sub.status,
                    "validated_at": sub.validated_at
                }
                for sub in recent_validations
            ],
            "approval_trends": approval_trends
        }

    def calculate_validator_rankings(self) -> List[Dict[str, Any]]:
        """
        Calculate validator rankings based on performance metrics.
        """
        validators = (
            self.db.query(models.Validator)
            .filter(models.Validator.is_active == True)
            .options(self.db.joinedload(models.Validator.user))
            .all()
        )

        # Calculate composite score
        rankings = []
        for validator in validators:
            if validator.validations_count == 0:
                score = 0
            else:
                # Weighted score: 60% accuracy, 30% volume, 10% stake
                accuracy_score = float(validator.accuracy_rate or 0) * 60
                volume_score = min(validator.validations_count / 100, 1) * 30  # Cap at 100 validations
                stake_score = min(validator.stx_staked / 10000, 1) * 10  # Cap at 10k STX
                score = accuracy_score + volume_score + stake_score

            rankings.append({
                "validator_id": str(validator.id),
                "wallet_address": validator.user.wallet_address,
                "score": score,
                "accuracy_rate": float(validator.accuracy_rate) if validator.accuracy_rate else 0,
                "validations_count": validator.validations_count,
                "stx_staked": float(validator.stx_staked),
                "reputation_score": validator.reputation_score
            })

        # Sort by score descending
        rankings.sort(key=lambda x: x["score"], reverse=True)

        # Add rank
        for i, ranking in enumerate(rankings):
            ranking["rank"] = i + 1

        return rankings
