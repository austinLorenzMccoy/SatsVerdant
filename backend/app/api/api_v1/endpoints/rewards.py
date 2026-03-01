from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.reward_service import RewardService

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse)
async def get_user_rewards(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of user's rewards.
    """
    try:
        reward_service = RewardService(db)
        result = reward_service.get_user_rewards(current_user, page, per_page, status)

        rewards_data = [
            schemas.Reward.from_orm(reward) for reward in result["data"]
        ]

        return schemas.PaginatedResponse(
            data=rewards_data,
            pagination=result["pagination"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rewards"
        )


@router.get("/summary", response_model=schemas.RewardSummary)
async def get_reward_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary of user's rewards.
    """
    try:
        reward_service = RewardService(db)
        summary = reward_service.get_reward_summary(current_user)

        return summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reward summary"
        )


@router.post("/{reward_id}/claim", response_model=schemas.Reward)
async def claim_reward(
    reward_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Claim a specific reward.
    """
    try:
        reward_service = RewardService(db)
        reward = reward_service.claim_reward(reward_id, current_user)

        return schemas.Reward.from_orm(reward)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to claim reward"
        )


@router.post("/claim-all")
async def claim_all_rewards(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Batch claim all claimable rewards.
    """
    try:
        reward_service = RewardService(db)
        result = reward_service.batch_claim_rewards(current_user)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to claim rewards"
        )


@router.get("/estimate")
async def estimate_reward(
    waste_type: str,
    weight_kg: float,
    quality_grade: str = "A",
    db: Session = Depends(get_db)
):
    """
    Estimate reward for a potential submission.
    """
    try:
        reward_service = RewardService(db)
        estimate = reward_service.get_reward_estimate(waste_type, weight_kg, quality_grade)

        return estimate

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate reward"
        )
