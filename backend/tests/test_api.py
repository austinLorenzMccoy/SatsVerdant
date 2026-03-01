import pytest
from app.core.security import create_wallet_token


class TestAuthAPI:
    """Test authentication API endpoints."""

    def test_create_wallet_challenge(self, client):
        """Test creating wallet challenge."""
        response = client.post("/api/v1/auth/challenge", json={
            "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        })

        assert response.status_code == 200
        data = response.json()
        assert "challenge" in data
        assert "expires_at" in data
        assert "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM" in data["challenge"]

    def test_verify_wallet_signature(self, client, db_session):
        """Test verifying wallet signature."""
        # Create challenge first
        challenge_response = client.post("/api/v1/auth/challenge", json={
            "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        })
        challenge_data = challenge_response.json()

        # Verify signature (simplified for testing)
        response = client.post("/api/v1/auth/verify", json={
            "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
            "signature": "test_signature",
            "challenge": challenge_data["challenge"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_get_current_user(self, client, auth_headers, test_user):
        """Test getting current user profile."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["wallet_address"] == test_user.wallet_address
        assert data["role"] == test_user.role
        assert "stats" in data

    def test_get_current_user_no_auth(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestSubmissionsAPI:
    """Test submissions API endpoints."""

    def test_create_submission(self, client, auth_headers):
        """Test creating a submission."""
        # Create test image file
        from io import BytesIO
        image_data = BytesIO(b"fake image content")
        image_data.name = "test.jpg"

        response = client.post(
            "/api/v1/submissions/",
            headers=auth_headers,
            files={"image": ("test.jpg", image_data, "image/jpeg")},
            data={
                "latitude": "52.3676",
                "longitude": "4.9041",
                "location_accuracy": "10.5",
                "notes": "Plastic bottles"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending_classification"
        assert data["latitude"] == 52.3676

    def test_create_submission_no_image(self, client, auth_headers):
        """Test creating submission without image."""
        response = client.post("/api/v1/submissions/", headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_create_submission_unauthorized(self, client):
        """Test creating submission without authentication."""
        response = client.post("/api/v1/submissions/")

        assert response.status_code == 401

    def test_get_user_submissions(self, client, auth_headers, db_session, test_user):
        """Test getting user's submissions."""
        # Create a test submission
        from app import models
        submission = models.Submission(
            user_id=test_user.id,
            status="classified",
            ai_waste_type="plastic"
        )
        db_session.add(submission)
        db_session.commit()

        response = client.get("/api/v1/submissions/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "classified"

    def test_get_submission(self, client, auth_headers, db_session, test_user):
        """Test getting a specific submission."""
        # Create a test submission
        from app import models
        submission = models.Submission(
            user_id=test_user.id,
            status="approved",
            ai_waste_type="plastic",
            ai_confidence=0.85
        )
        db_session.add(submission)
        db_session.commit()

        response = client.get(f"/api/v1/submissions/{submission.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(submission.id)
        assert data["status"] == "approved"
        assert data["ai_waste_type"] == "plastic"

    def test_get_submission_not_found(self, client, auth_headers):
        """Test getting non-existent submission."""
        response = client.get("/api/v1/submissions/non-existent-id", headers=auth_headers)

        assert response.status_code == 404

    def test_submit_for_validation(self, client, auth_headers, db_session, test_user):
        """Test submitting for validation."""
        # Create classified submission
        from app import models
        submission = models.Submission(
            user_id=test_user.id,
            status="classified",
            ai_waste_type="plastic"
        )
        db_session.add(submission)
        db_session.commit()

        response = client.post(
            f"/api/v1/submissions/{submission.id}/submit",
            headers=auth_headers,
            json={"confirmed_classification": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_validation"


class TestValidatorsAPI:
    """Test validators API endpoints."""

    def test_get_validators(self, client, test_validator):
        """Test getting validators list."""
        response = client.get("/api/v1/validators/")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) >= 1

    def test_create_validator(self, client, auth_headers, test_user):
        """Test creating a validator."""
        response = client.post(
            "/api/v1/validators/",
            headers=auth_headers,
            json={
                "stx_staked": "500.0",
                "stake_tx_id": "0x1234567890abcdef"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["stx_staked"] == 500.0
        assert data["is_active"] is True

    def test_get_validator_stats(self, client, auth_headers, test_validator):
        """Test getting validator stats."""
        response = client.get("/api/v1/validators/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_validator.id)
        assert "validations_completed" in data
        assert "reputation_score" in data


class TestRewardsAPI:
    """Test rewards API endpoints."""

    def test_get_user_rewards(self, client, auth_headers, db_session, test_user):
        """Test getting user rewards."""
        # Create test rewards
        from app import models
        reward = models.Reward(
            user_id=test_user.id,
            waste_tokens=50,
            sbtc_amount=0.0005,
            status="claimable"
        )
        db_session.add(reward)
        db_session.commit()

        response = client.get("/api/v1/rewards/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["waste_tokens"] == 50

    def test_claim_reward(self, client, auth_headers, db_session, test_user):
        """Test claiming a reward."""
        # Create claimable reward
        from app import models
        reward = models.Reward(
            user_id=test_user.id,
            waste_tokens=50,
            sbtc_amount=0.0005,
            status="claimable"
        )
        db_session.add(reward)
        db_session.commit()

        response = client.post(
            f"/api/v1/rewards/{reward.id}/claim",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "claimed"

    def test_get_reward_estimate(self, client):
        """Test reward estimation."""
        response = client.get("/api/v1/rewards/estimate?waste_type=plastic&weight_kg=1.0&quality_grade=A")

        assert response.status_code == 200
        data = response.json()
        assert "waste_tokens" in data
        assert "sbtc_amount" in data
        assert data["waste_tokens"] == 100  # 1.0kg * 100 tokens/kg for plastic grade A


class TestStatsAPI:
    """Test statistics API endpoints."""

    def test_get_global_stats(self, client):
        """Test getting global statistics."""
        response = client.get("/api/v1/stats/global")

        assert response.status_code == 200
        data = response.json()
        assert "total_waste_recycled_kg" in data
        assert "total_tokens_minted" in data
        assert "active_recyclers" in data

    def test_get_user_public_stats(self, client, test_user):
        """Test getting user public statistics."""
        response = client.get(f"/api/v1/stats/user/{test_user.wallet_address}")

        assert response.status_code == 200
        data = response.json()
        assert data["wallet_address"] == test_user.wallet_address
        assert "submissions_count" in data
        assert "waste_breakdown" in data


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
