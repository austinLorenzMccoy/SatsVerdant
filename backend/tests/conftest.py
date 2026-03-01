import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def test_db():
    """
    Create test database and tables.
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """
    Create a fresh database session for each test.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create test client with database session override.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """
    Create a test user.
    """
    from app import models
    user = models.User(
        wallet_address="ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
        role="recycler"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_validator(db_session, test_user):
    """
    Create a test validator.
    """
    from app import models
    validator = models.Validator(
        user_id=test_user.id,
        stx_staked=1000.0,
        reputation_score=100,
        is_active=True
    )
    db_session.add(validator)
    db_session.commit()
    db_session.refresh(validator)
    return validator


@pytest.fixture
def auth_headers(client, test_user):
    """
    Create authentication headers for test user.
    """
    # Create a test token
    from app.core.security import create_wallet_token
    token = create_wallet_token(test_user.wallet_address)
    return {"Authorization": f"Bearer {token}"}
