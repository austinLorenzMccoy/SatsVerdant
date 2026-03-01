from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status
from app import models, schemas
from app.core.config import settings
import uuid
from datetime import datetime, timedelta


class SubmissionService:
    def __init__(self, db: Session):
        self.db = db

    def create_submission(
        self,
        user: models.User,
        submission_data: schemas.SubmissionCreate,
        image_bytes: bytes,
        filename: str
    ) -> models.Submission:
        """
        Create a new waste submission.
        """
        # Generate unique ID for submission
        submission_id = str(uuid.uuid4())

        # Create submission record
        submission = models.Submission(
            id=submission_id,
            user_id=user.id,
            latitude=submission_data.latitude,
            longitude=submission_data.longitude,
            location_accuracy=submission_data.location_accuracy,
            device_info=submission_data.device_info or {},
            status="pending_classification"
        )

        # TODO: Upload image to S3 and set image_s3_key
        # For MVP, we'll store temporarily
        submission.image_s3_key = f"temp/{submission_id}/{filename}"

        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)

        # TODO: Enqueue AI classification job
        # For now, we'll simulate immediate classification
        # self._enqueue_classification_job(submission.id)

        return submission

    def get_submission(self, submission_id: str, user: Optional[models.User] = None) -> models.Submission:
        """
        Get a submission by ID.
        """
        query = self.db.query(models.Submission).filter(models.Submission.id == submission_id)

        if user:
            query = query.filter(models.Submission.user_id == user.id)

        submission = query.first()
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        return submission

    def get_user_submissions(
        self,
        user: models.User,
        page: int = 1,
        per_page: int = 20,
        status_filter: Optional[str] = None,
        waste_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated list of user's submissions.
        """
        query = self.db.query(models.Submission).filter(models.Submission.user_id == user.id)

        if status_filter:
            query = query.filter(models.Submission.status == status_filter)

        if waste_type:
            query = query.filter(models.Submission.ai_waste_type == waste_type)

        total = query.count()
        total_pages = (total + per_page - 1) // per_page

        submissions = (
            query.order_by(desc(models.Submission.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return {
            "data": submissions,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }

    def submit_for_validation(self, submission_id: str, user: models.User, update_data: schemas.SubmissionUpdate) -> models.Submission:
        """
        Submit a classified submission for validation.
        """
        submission = self.get_submission(submission_id, user)

        if submission.status != "classified":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission must be classified before validation"
            )

        if update_data.override_weight_kg:
            submission.ai_estimated_weight_kg = update_data.override_weight_kg

        submission.status = "pending_validation"
        submission.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(submission)

        # TODO: Enqueue validation assignment job

        return submission

    def get_pending_validations(
        self,
        validator: models.Validator,
        page: int = 1,
        per_page: int = 20,
        waste_type: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        Get pending submissions for validation.
        """
        query = (
            self.db.query(models.Submission)
            .filter(
                and_(
                    models.Submission.status == "pending_validation",
                    or_(
                        models.Submission.ai_confidence.is_(None),
                        models.Submission.ai_confidence >= min_confidence
                    )
                )
            )
        )

        if waste_type:
            query = query.filter(models.Submission.ai_waste_type == waste_type)

        total = query.count()
        total_pages = (total + per_page - 1) // per_page

        submissions = (
            query.order_by(models.Submission.created_at)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        # Enhance with user history and fraud indicators
        enhanced_submissions = []
        for submission in submissions:
            enhanced = self._enhance_submission_for_validation(submission, validator)
            enhanced_submissions.append(enhanced)

        return {
            "data": enhanced_submissions,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }

    def approve_submission(
        self,
        submission_id: str,
        validator: models.Validator,
        decision_data: schemas.ValidationDecision
    ) -> models.Submission:
        """
        Approve a submission and prepare for minting.
        """
        submission = self.db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        if submission.status != "pending_validation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission is not pending validation"
            )

        # Update submission
        submission.status = "approved"
        submission.validator_id = validator.user_id
        submission.validated_at = datetime.utcnow()
        submission.validation_notes = decision_data.notes

        if decision_data.override_weight_kg:
            submission.ai_estimated_weight_kg = decision_data.override_weight_kg
        if decision_data.override_quality:
            submission.ai_quality_grade = decision_data.override_quality

        # Update validator stats
        validator.validations_count += 1
        validator.approvals_count += 1
        validator.reputation_score = min(100, validator.reputation_score + 1)  # Small positive reinforcement

        self.db.commit()

        # TODO: Enqueue minting job
        # self._enqueue_minting_job(submission.id)

        return submission

    def reject_submission(
        self,
        submission_id: str,
        validator: models.Validator,
        decision_data: schemas.ValidationDecision
    ) -> models.Submission:
        """
        Reject a submission.
        """
        submission = self.db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        if submission.status != "pending_validation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission is not pending validation"
            )

        # Update submission
        submission.status = "rejected"
        submission.validator_id = validator.user_id
        submission.validated_at = datetime.utcnow()
        submission.validation_notes = decision_data.notes

        # Update validator stats
        validator.validations_count += 1
        validator.rejections_count += 1
        validator.reputation_score = max(0, validator.reputation_score - 1)  # Small negative reinforcement

        self.db.commit()

        return submission

    def get_global_stats(self) -> Dict[str, Any]:
        """
        Get global platform statistics.
        """
        # Total waste recycled
        total_waste = (
            self.db.query(func.sum(models.Submission.ai_estimated_weight_kg))
            .filter(models.Submission.status == "minted")
            .scalar() or 0
        )

        # Total tokens minted
        total_tokens = (
            self.db.query(func.sum(models.Submission.tokens_minted))
            .filter(models.Submission.tokens_minted.isnot(None))
            .scalar() or 0
        )

        # Total carbon offset
        total_carbon = (
            self.db.query(func.sum(models.Submission.carbon_offset_g))
            .filter(models.Submission.carbon_offset_g.isnot(None))
            .scalar() or 0
        ) / 1000  # Convert to kg

        # Active users
        active_recyclers = (
            self.db.query(func.count(models.User.id))
            .filter(models.User.role == "recycler")
            .scalar()
        )

        active_validators = (
            self.db.query(func.count(models.Validator.id))
            .filter(models.Validator.is_active == True)
            .scalar()
        )

        # Recent activity
        last_24h = datetime.utcnow() - timedelta(hours=24)
        submissions_24h = (
            self.db.query(func.count(models.Submission.id))
            .filter(models.Submission.created_at >= last_24h)
            .scalar()
        )

        return {
            "total_waste_recycled_kg": float(total_waste),
            "total_sbtc_distributed": "0.000",  # TODO: Calculate from rewards
            "total_tokens_minted": total_tokens,
            "total_carbon_offset_kg": float(total_carbon),
            "active_recyclers": active_recyclers,
            "active_validators": active_validators,
            "submissions_last_24h": submissions_24h,
            "avg_classification_time_seconds": 28.0,  # TODO: Calculate from actual data
            "avg_validation_time_minutes": 45.0,       # TODO: Calculate from actual data
            "blockchain": {
                "network": settings.STACKS_NETWORK,
                "contract_address": "SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7.waste-tokens"  # TODO: Use actual address
            }
        }

    def get_user_stats(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get public statistics for a user.
        """
        user = (
            self.db.query(models.User)
            .filter(models.User.wallet_address == wallet_address)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Submission stats
        submissions_count = (
            self.db.query(func.count(models.Submission.id))
            .filter(models.Submission.user_id == user.id)
            .scalar()
        )

        # Waste breakdown
        waste_breakdown = {}
        waste_types = ['plastic', 'paper', 'metal', 'organic', 'electronic']
        for waste_type in waste_types:
            count = (
                self.db.query(func.count(models.Submission.id))
                .filter(
                    and_(
                        models.Submission.user_id == user.id,
                        models.Submission.ai_waste_type == waste_type,
                        models.Submission.status == "minted"
                    )
                )
                .scalar()
            )
            waste_breakdown[waste_type] = count

        # Approval rate
        total_validated = (
            self.db.query(func.count(models.Submission.id))
            .filter(
                and_(
                    models.Submission.user_id == user.id,
                    models.Submission.status.in_(["approved", "minted", "rejected"])
                )
            )
            .scalar()
        )

        approved_count = (
            self.db.query(func.count(models.Submission.id))
            .filter(
                and_(
                    models.Submission.user_id == user.id,
                    models.Submission.status.in_(["approved", "minted"])
                )
            )
            .scalar()
        )

        approval_rate = approved_count / total_validated if total_validated > 0 else 0

        # Average confidence
        avg_confidence = (
            self.db.query(func.avg(models.Submission.ai_confidence))
            .filter(
                and_(
                    models.Submission.user_id == user.id,
                    models.Submission.ai_confidence.isnot(None)
                )
            )
            .scalar() or 0
        )

        # TODO: Calculate tokens earned, sBTC earned, carbon offset, rank

        return {
            "wallet_address": wallet_address,
            "submissions_count": submissions_count,
            "tokens_earned": 0,  # TODO
            "sbtc_earned": "0.000",  # TODO
            "carbon_offset_kg": 0.0,  # TODO
            "waste_breakdown": waste_breakdown,
            "approval_rate": float(approval_rate),
            "avg_confidence_score": float(avg_confidence),
            "rank": 0,  # TODO: Calculate ranking
            "joined_at": user.created_at
        }

    def _enhance_submission_for_validation(self, submission: models.Submission, validator: models.Validator) -> Dict[str, Any]:
        """
        Enhance submission data for validator review.
        """
        # Get user history
        user_submissions = (
            self.db.query(models.Submission)
            .filter(models.Submission.user_id == submission.user_id)
            .all()
        )

        total_submissions = len(user_submissions)
        approved_count = sum(1 for s in user_submissions if s.status in ["approved", "minted"])
        approval_rate = approved_count / total_submissions if total_submissions > 0 else 0

        avg_confidence = (
            sum(s.ai_confidence for s in user_submissions if s.ai_confidence) /
            sum(1 for s in user_submissions if s.ai_confidence) if user_submissions else 0
        )

        # Fraud indicators
        fraud_score = submission.fraud_score or 0.0
        fraud_flags = submission.fraud_flags or []

        # Time in queue
        time_in_queue = datetime.utcnow() - submission.created_at
        time_in_queue_minutes = int(time_in_queue.total_seconds() / 60)

        return {
            "id": str(submission.id),
            "image_url": submission.image_url,
            "ai_classification": {
                "waste_type": submission.ai_waste_type,
                "confidence": float(submission.ai_confidence) if submission.ai_confidence else None,
                "estimated_weight_kg": float(submission.ai_estimated_weight_kg) if submission.ai_estimated_weight_kg else None,
                "quality_grade": submission.ai_quality_grade
            },
            "location": {
                "latitude": float(submission.latitude) if submission.latitude else None,
                "longitude": float(submission.longitude) if submission.longitude else None
            } if submission.latitude and submission.longitude else None,
            "user_history": {
                "submissions_count": total_submissions,
                "approval_rate": float(approval_rate),
                "avg_confidence": float(avg_confidence)
            },
            "fraud_indicators": {
                "score": float(fraud_score),
                "flags": fraud_flags
            },
            "created_at": submission.created_at,
            "time_in_queue_minutes": time_in_queue_minutes
        }
