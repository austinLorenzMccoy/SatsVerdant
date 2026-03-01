from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas
from app.core.database import get_db
from app.services.submission_service import SubmissionService
from app.services.reward_service import RewardService

router = APIRouter()


@router.get("/global", response_model=schemas.GlobalStats)
async def get_global_stats(db: Session = Depends(get_db)):
    """
    Get platform-wide statistics (public).
    """
    try:
        submission_service = SubmissionService(db)
        stats = submission_service.get_global_stats()

        return schemas.GlobalStats(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get global stats"
        )


@router.get("/user/{wallet_address}", response_model=schemas.UserPublicStats)
async def get_user_public_stats(wallet_address: str, db: Session = Depends(get_db)):
    """
    Get user-specific public statistics.
    """
    try:
        submission_service = SubmissionService(db)
        stats = submission_service.get_user_stats(wallet_address)

        return schemas.UserPublicStats(**stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user stats"
        )
