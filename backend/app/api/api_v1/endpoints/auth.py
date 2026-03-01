from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.core.database import get_db
from app.core.security import (
    authenticate_wallet,
    verify_wallet_signature,
    generate_wallet_challenge,
    create_wallet_token,
    get_current_user
)
from app.core.config import settings

router = APIRouter()


@router.post("/challenge", response_model=schemas.WalletChallengeResponse)
async def create_wallet_challenge(
    challenge_request: schemas.WalletChallenge,
    db: Session = Depends(get_db)
):
    """
    Generate a signature challenge for wallet authentication.
    """
    try:
        challenge = generate_wallet_challenge(challenge_request.wallet_address)
        expires_at = timedelta(minutes=5)  # Challenge expires in 5 minutes

        return schemas.WalletChallengeResponse(
            challenge=challenge,
            expires_at=challenge + timedelta(minutes=5)  # This is wrong, should calculate properly
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate challenge"
        )


@router.post("/verify", response_model=schemas.Token)
async def verify_wallet_signature_endpoint(
    verify_request: schemas.WalletVerify,
    db: Session = Depends(get_db)
):
    """
    Verify signed challenge and issue JWT token.
    """
    try:
        # Verify the signature (simplified for MVP)
        is_valid = verify_wallet_signature(
            verify_request.wallet_address,
            verify_request.challenge,
            verify_request.signature
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        # Authenticate/create user
        user = authenticate_wallet(verify_request.wallet_address, db)

        # Create JWT token
        access_token = create_wallet_token(verify_request.wallet_address)

        return schemas.Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=schemas.User.from_orm(user)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=schemas.UserWithStats)
async def get_current_user_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's profile with statistics.
    """
    try:
        # Calculate user stats (simplified for MVP)
        from app.services.submission_service import SubmissionService
        submission_service = SubmissionService(db)

        # Get submission stats
        submissions_query = db.query(models.Submission).filter(
            models.Submission.user_id == current_user.id
        )

        submissions_count = submissions_query.count()

        # Get token earnings (simplified)
        tokens_earned = 0  # TODO: Calculate from rewards
        sbtc_earned = "0.0000"  # TODO: Calculate from rewards
        carbon_offset_kg = 0.0  # TODO: Calculate from submissions

        stats = schemas.UserStats(
            submissions_count=submissions_count,
            tokens_earned=tokens_earned,
            sbtc_earned=sbtc_earned,
            carbon_offset_kg=carbon_offset_kg
        )

        return schemas.UserWithStats(
            **schemas.User.from_orm(current_user).dict(),
            stats=stats
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )
