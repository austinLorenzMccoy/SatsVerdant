import pytest
from app.core.security import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password,
    generate_wallet_challenge,
    create_wallet_token
)


class TestSecurity:
    """Test security utilities."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        subject = "test@example.com"
        token = create_access_token(subject)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self):
        """Test verifying a valid token."""
        subject = "test@example.com"
        token = create_access_token(subject)
        decoded_subject = verify_token(token)
        assert decoded_subject == subject

    def test_verify_token_invalid(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.jwt.token"
        decoded_subject = verify_token(invalid_token)
        assert decoded_subject is None

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert hashed != password

        # Verify correct password
        assert verify_password(password, hashed)

        # Verify incorrect password
        assert not verify_password("wrongpassword", hashed)

    def test_generate_wallet_challenge(self):
        """Test wallet challenge generation."""
        wallet_address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        challenge = generate_wallet_challenge(wallet_address)
        assert isinstance(challenge, str)
        assert wallet_address in challenge
        assert len(challenge) > 0

    def test_create_wallet_token(self):
        """Test wallet JWT token creation."""
        wallet_address = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
        token = create_wallet_token(wallet_address)
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify the token contains the wallet address
        decoded = verify_token(token)
        assert decoded == wallet_address
