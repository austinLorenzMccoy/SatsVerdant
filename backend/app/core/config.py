from typing import List, Optional
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_SECRET_KEY: str = "your-jwt-secret-key-here"
    ALGORITHM: str = "HS256"
    SERVER_NAME: str = "SatsVerdant"
    SERVER_HOST: AnyHttpUrl = "http://localhost"
    PROJECT_NAME: str = "SatsVerdant Backend"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "Waste Tokenization Platform on Stacks"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Next.js dev server
        "https://satsverdant.com",
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./satsverdant.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    UPLOAD_RATE_LIMIT_PER_DAY: int = 5

    # Stacks Blockchain
    STACKS_NETWORK: str = "testnet"  # or "mainnet"
    STACKS_API_URL: str = "https://stacks-node-api.testnet.stacks.co"
    STACKS_CONTRACT_DEPLOYER: str = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
    STACKS_MIN_STAKE_AMOUNT: float = 500.0  # Minimum STX to stake as validator

    # IPFS
    IPFS_PINATA_API_KEY: str = "your-pinata-api-key"
    IPFS_PINATA_SECRET_KEY: str = "your-pinata-secret"
    IPFS_GATEWAY_URL: str = "https://gateway.pinata.cloud/ipfs/"

    # Google Cloud Storage
    GCP_PROJECT_ID: str = "your-gcp-project-id"
    GCP_STORAGE_BUCKET: str = "satsverdant-temp-uploads"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # ML Model Paths
    MODEL_PATH: str = "./app/ml/models/waste_classifier_v1.h5"
    WEIGHT_ESTIMATOR_MODEL: str = "./app/ml/models/weight_estimator.h5"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Email (optional)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "/app/email-templates/build"
    EMAILS_ENABLED: bool = False
    EMAIL_TEST_USER: str = "test@example.com"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
