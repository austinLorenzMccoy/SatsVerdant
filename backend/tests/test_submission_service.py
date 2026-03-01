import pytest
from app.services.submission_service import SubmissionService
from app import models, schemas
from decimal import Decimal
from uuid import uuid4


class TestSubmissionService:
    """Test SubmissionService."""

    def test_create_submission(self, db_session, test_user):
        """Test creating a submission."""
        service = SubmissionService(db_session)

        submission_data = schemas.SubmissionCreate(
            latitude=Decimal("52.3676"),
            longitude=Decimal("4.9041"),
            location_accuracy=Decimal("10.5"),
            notes="Plastic bottles"
        )

        image_bytes = b"fake image data"
        filename = "test.jpg"

        submission = service.create_submission(
            test_user, submission_data, image_bytes, filename
        )

        assert submission.id is not None
        assert submission.user_id == test_user.id
        assert submission.latitude == Decimal("52.3676")
        assert submission.longitude == Decimal("4.9041")
        assert submission.location_accuracy == Decimal("10.5")
        assert submission.notes == "Plastic bottles"
        assert submission.status == "pending_classification"

    def test_get_submission_own(self, db_session, test_user):
        """Test getting own submission."""
        service = SubmissionService(db_session)

        # Create submission
        submission = models.Submission(
            user_id=test_user.id,
            status="pending_classification"
        )
        db_session.add(submission)
        db_session.commit()

        # Get submission
        retrieved = service.get_submission(str(submission.id), test_user)
        assert retrieved.id == submission.id
        assert retrieved.user_id == test_user.id

    def test_get_submission_not_found(self, db_session, test_user):
        """Test getting non-existent submission."""
        service = SubmissionService(db_session)

        with pytest.raises(Exception):  # HTTPException
            service.get_submission(str(uuid4()), test_user)

    def test_get_user_submissions(self, db_session, test_user):
        """Test getting user's submissions."""
        service = SubmissionService(db_session)

        # Create multiple submissions
        for i in range(3):
            submission = models.Submission(
                user_id=test_user.id,
                status="classified" if i % 2 == 0 else "pending_validation"
            )
            db_session.add(submission)
        db_session.commit()

        # Get all submissions
        result = service.get_user_submissions(test_user)
        assert len(result["data"]) == 3
        assert result["pagination"]["total"] == 3

        # Get only classified submissions
        result = service.get_user_submissions(test_user, status="classified")
        assert len(result["data"]) == 2

    def test_submit_for_validation(self, db_session, test_user):
        """Test submitting for validation."""
        service = SubmissionService(db_session)

        # Create classified submission
        submission = models.Submission(
            user_id=test_user.id,
            status="classified",
            ai_waste_type="plastic",
            ai_confidence=Decimal("0.85")
        )
        db_session.add(submission)
        db_session.commit()

        # Submit for validation
        update_data = schemas.SubmissionUpdate(confirmed_classification=True)
        updated = service.submit_for_validation(str(submission.id), test_user, update_data)

        assert updated.status == "pending_validation"

    def test_submit_for_validation_not_classified(self, db_session, test_user):
        """Test submitting unclassified submission."""
        service = SubmissionService(db_session)

        # Create unclassified submission
        submission = models.Submission(
            user_id=test_user.id,
            status="pending_classification"
        )
        db_session.add(submission)
        db_session.commit()

        # Try to submit for validation
        update_data = schemas.SubmissionUpdate(confirmed_classification=True)
        with pytest.raises(Exception):  # HTTPException
            service.submit_for_validation(str(submission.id), test_user, update_data)

    def test_get_pending_validations(self, db_session, test_validator):
        """Test getting pending validations."""
        service = SubmissionService(db_session)

        # Create pending submissions
        for i in range(2):
            submission = models.Submission(
                user_id=test_validator.user_id,  # Different user
                status="pending_validation",
                ai_waste_type="plastic",
                ai_confidence=Decimal("0.85")
            )
            db_session.add(submission)
        db_session.commit()

        # Get pending validations
        result = service.get_pending_validations(test_validator)
        assert len(result["data"]) == 2

    def test_approve_submission(self, db_session, test_validator):
        """Test approving a submission."""
        service = SubmissionService(db_session)

        # Create pending submission
        submission = models.Submission(
            user_id=test_validator.user_id,  # Different user
            status="pending_validation"
        )
        db_session.add(submission)
        db_session.commit()

        # Approve submission
        decision_data = schemas.ValidationDecision(
            decision="approved",
            notes="Good submission"
        )
        approved = service.approve_submission(str(submission.id), test_validator, decision_data)

        assert approved.status == "approved"
        assert approved.validator_id == test_validator.user_id

        # Check validator stats updated
        db_session.refresh(test_validator)
        assert test_validator.validations_count == 1
        assert test_validator.approvals_count == 1

    def test_reject_submission(self, db_session, test_validator):
        """Test rejecting a submission."""
        service = SubmissionService(db_session)

        # Create pending submission
        submission = models.Submission(
            user_id=test_validator.user_id,  # Different user
            status="pending_validation"
        )
        db_session.add(submission)
        db_session.commit()

        # Reject submission
        decision_data = schemas.ValidationDecision(
            decision="rejected",
            notes="Poor quality"
        )
        rejected = service.reject_submission(str(submission.id), test_validator, decision_data)

        assert rejected.status == "rejected"
        assert rejected.validator_id == test_validator.user_id

        # Check validator stats updated
        db_session.refresh(test_validator)
        assert test_validator.validations_count == 1
        assert test_validator.rejections_count == 1

    def test_get_global_stats(self, db_session):
        """Test getting global statistics."""
        service = SubmissionService(db_session)

        # Create some test data
        user = models.User(wallet_address="ST2...", role="recycler")
        db_session.add(user)

        submission = models.Submission(
            user_id=user.id,
            status="minted",
            ai_estimated_weight_kg=Decimal("1.5"),
            tokens_minted=150,
            carbon_offset_g=750
        )
        db_session.add(submission)
        db_session.commit()

        stats = service.get_global_stats()

        assert "total_waste_recycled_kg" in stats
        assert "total_tokens_minted" in stats
        assert "active_recyclers" in stats
        assert stats["total_tokens_minted"] == 150

    def test_get_user_stats(self, db_session, test_user):
        """Test getting user statistics."""
        service = SubmissionService(db_session)

        # Create submissions
        for i in range(2):
            submission = models.Submission(
                user_id=test_user.id,
                status="approved",
                ai_waste_type="plastic" if i == 0 else "paper"
            )
            db_session.add(submission)
        db_session.commit()

        stats = service.get_user_stats(test_user.wallet_address)

        assert stats["submissions_count"] == 2
        assert stats["approval_rate"] == 1.0  # 2/2 approved
        assert len(stats["waste_breakdown"]) == 5  # All waste types
        assert stats["waste_breakdown"]["plastic"] == 1
        assert stats["waste_breakdown"]["paper"] == 1
