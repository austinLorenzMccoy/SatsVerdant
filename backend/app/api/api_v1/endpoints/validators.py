from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user, get_current_validator
from app.services.validator_service import ValidatorService

router = APIRouter()


@router.post("/", response_model=schemas.Validator)
async def create_validator(
    validator_data: schemas.ValidatorCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register as a validator by staking STX.
    """
    try:
        # Check if user already has a validator account
        existing = (
            db.query(models.Validator)
            .filter(models.Validator.user_id == current_user.id)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a validator"
            )

        validator_service = ValidatorService(db)
        validator = validator_service.create_validator(current_user, validator_data)

        return schemas.Validator.from_orm(validator)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create validator"
        )


@router.get("/", response_model=schemas.PaginatedResponse)
async def get_validators(
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "reputation_score",
    order: str = "desc",
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get paginated list of validators (public leaderboard).
    """
    try:
        validator_service = ValidatorService(db)
        result = validator_service.get_validators(
            page, per_page, sort_by, order, active_only
        )

        return schemas.PaginatedResponse(
            data=result["data"],
            pagination=result["pagination"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get validators"
        )


@router.get("/me", response_model=schemas.Validator)
async def get_my_validator_profile(
    current_validator: models.Validator = Depends(get_current_validator)
):
    """
    Get current user's validator profile.
    """
    return schemas.Validator.from_orm(current_validator)


@router.delete("/me")
async def unstake_validator(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unstake and remove validator status.
    """
    try:
        validator_service = ValidatorService(db)
        validator = validator_service.unstake_validator(current_user)

        return {"message": "Validator unstaked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unstake validator"
        )


@router.get("/queue", response_model=schemas.PaginatedResponse)
async def get_validation_queue(
    page: int = 1,
    per_page: int = 20,
    waste_type: Optional[str] = None,
    min_confidence: float = 0.7,
    current_validator: models.Validator = Depends(get_current_validator),
    db: Session = Depends(get_db)
):
    """
    Get pending submissions for validation.
    """
    try:
        from app.services.submission_service import SubmissionService
        submission_service = SubmissionService(db)

        result = submission_service.get_pending_validations(
            current_validator, page, per_page, waste_type, min_confidence
        )

        return schemas.PaginatedResponse(
            data=result["data"],
            pagination=result["pagination"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get validation queue"
        )


@router.post("/submissions/{submission_id}/approve", response_model=schemas.Submission)
async def approve_submission(
    submission_id: str,
    decision_data: schemas.ValidationDecision,
    current_validator: models.Validator = Depends(get_current_validator),
    db: Session = Depends(get_db)
):
    """
    Approve a submission.
    """
    try:
        from app.services.submission_service import SubmissionService
        submission_service = SubmissionService(db)

        submission = submission_service.approve_submission(
            submission_id, current_validator, decision_data
        )

        return schemas.Submission.from_orm(submission)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve submission"
        )


@router.post("/submissions/{submission_id}/reject", response_model=schemas.Submission)
async def reject_submission(
    submission_id: str,
    decision_data: schemas.ValidationDecision,
    current_validator: models.Validator = Depends(get_current_validator),
    db: Session = Depends(get_db)
):
    """
    Reject a submission.
    """
    try:
        from app.services.submission_service import SubmissionService
        submission_service = SubmissionService(db)

        submission = submission_service.reject_submission(
            submission_id, current_validator, decision_data
        )

        return schemas.Submission.from_orm(submission)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject submission"
        )


@router.get("/stats")
async def get_validator_stats(
    current_validator: models.Validator = Depends(get_current_validator),
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for current validator.
    """
    try:
        validator_service = ValidatorService(db)
        stats = validator_service.get_validator_stats(current_validator)

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get validator stats"
        )
