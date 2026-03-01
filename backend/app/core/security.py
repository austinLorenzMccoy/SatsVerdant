from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app import models

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Create JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and return subject (wallet address).
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject: str = payload.get("sub")
        if subject is None:
            return None
        return subject
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a stored password against one provided by user.
    """
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_wallet(wallet_address: str, db: Session) -> models.User:
    """
    Authenticate wallet address and return or create user.
    """
    user = db.query(models.User).filter(models.User.wallet_address == wallet_address).first()
    if not user:
        # Create new user
        user = models.User(
            wallet_address=wallet_address,
            role="recycler"  # Default role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update last seen
        user.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(user)

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        subject = verify_token(token)
        if subject is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # For wallet-based auth, subject is the wallet address
    user = db.query(models.User).filter(models.User.wallet_address == subject).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_validator(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> models.Validator:
    """
    Get current user's validator profile.
    Raises 403 if user is not a validator.
    """
    validator = db.query(models.Validator).filter(
        models.Validator.user_id == current_user.id
    ).first()
    
    if not validator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a validator"
        )
    if not validator.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Validator account is suspended"
        )
    return validator


def verify_wallet_signature(wallet_address: str, message: str, signature: str) -> bool:
    """
    Verify that a signature was created by the owner of a wallet address.
    This is a simplified version - in production, you'd use proper cryptographic verification.
    """
    # For MVP, we'll do basic validation
    # In production, this should use proper ECDSA verification for Stacks transactions

    # Placeholder implementation - always return True for MVP
    # TODO: Implement proper signature verification using stacks.js or similar
    return True


def generate_wallet_challenge(wallet_address: str) -> str:
    """
    Generate a unique challenge message for wallet signature.
    """
    timestamp = int(datetime.utcnow().timestamp())
    challenge = f"Sign this message to authenticate with SatsVerdant: {wallet_address}:{timestamp}"
    return challenge


def create_wallet_token(wallet_address: str) -> str:
    """
    Create JWT token for authenticated wallet.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        subject=wallet_address,
        expires_delta=access_token_expires
    )
