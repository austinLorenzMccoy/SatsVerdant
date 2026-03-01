from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.submission_service import SubmissionService
from app.core.config import settings
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=schemas.Submission)
async def create_submission(
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    location_accuracy: Optional[float] = Form(None),
    device_info: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    image: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new waste submission with image upload.
    """
    try:
        # Validate file type
        if not image.content_type in ["image/jpeg", "image/png", "image/heic", "image/heif"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, HEIC allowed."
            )

        # Validate file size (10MB max)
        file_size = len(await image.read())
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 10MB."
            )

        # Reset file pointer
        await image.seek(0)

        # Parse device_info JSON
        device_data = None
        if device_info:
            import json
            try:
                device_data = json.loads(device_info)
            except json.JSONDecodeError:
                device_data = {}

        # Create submission data
        submission_data = schemas.SubmissionCreate(
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            device_info=device_data,
            notes=notes
        )

        # Generate filename
        file_extension = image.filename.split(".")[-1] if "." in image.filename else "jpg"
        filename = f"{uuid.uuid4()}.{file_extension}"

        # Read image bytes
        image_bytes = await image.read()

        # Create submission
        submission_service = SubmissionService(db)
        submission = submission_service.create_submission(
            current_user,
            submission_data,
            image_bytes,
            filename
        )

        # TODO: Enqueue classification job
        # For MVP, simulate immediate classification
        _simulate_classification(submission, db)

        return schemas.Submission.from_orm(submission)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create submission"
        )


@router.get("/", response_model=schemas.PaginatedResponse)
async def get_user_submissions(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    waste_type: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of user's submissions.
    """
    try:
        submission_service = SubmissionService(db)
        result = submission_service.get_user_submissions(
            current_user, page, per_page, status, waste_type
        )

        # Convert to response schema
        submissions_data = [
            schemas.Submission.from_orm(sub) for sub in result["data"]
        ]

        return schemas.PaginatedResponse(
            data=submissions_data,
            pagination=result["pagination"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get submissions"
        )


@router.get("/{submission_id}", response_model=schemas.SubmissionWithUser)
async def get_submission(
    submission_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed submission information.
    """
    try:
        submission_service = SubmissionService(db)
        submission = submission_service.get_submission(submission_id, current_user)

        # Get user info
        user = db.query(models.User).filter(models.User.id == submission.user_id).first()

        return schemas.SubmissionWithUser(
            **schemas.Submission.from_orm(submission).dict(),
            user=schemas.User.from_orm(user)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get submission"
        )


@router.post("/{submission_id}/submit", response_model=schemas.Submission)
async def submit_for_validation(
    submission_id: str,
    update_data: schemas.SubmissionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a classified submission for validation.
    """
    try:
        submission_service = SubmissionService(db)
        submission = submission_service.submit_for_validation(
            submission_id, current_user, update_data
        )

        return schemas.Submission.from_orm(submission)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit for validation"
        )


def _simulate_classification(submission: models.Submission, db: Session):
    """
    Simulate AI classification for MVP.
    In production, this would be handled by a background job.
    """
    import random
    from datetime import datetime

    # Simulate classification delay
    import time
    time.sleep(1)  # Simulate processing time

    # Random classification results for MVP
    waste_types = ["plastic", "paper", "metal", "organic", "electronic"]
    qualities = ["A", "B", "C", "D"]

    submission.ai_waste_type = random.choice(waste_types)
    submission.ai_confidence = round(random.uniform(0.7, 0.95), 4)
    submission.ai_estimated_weight_kg = round(random.uniform(0.1, 2.0), 2)
    submission.ai_quality_grade = random.choice(qualities)
    submission.status = "classified"

    db.commit()
