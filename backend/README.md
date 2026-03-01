# SatsVerdant Backend - MVP

## Overview

SatsVerdant is a waste tokenization platform built on the Stacks blockchain. This backend API powers waste submission, AI classification, validator verification, and sBTC reward distribution.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite (MVP) / PostgreSQL (Production)
- **Cache/Queue**: Redis
- **Background Jobs**: Celery
- **Storage**: Google Cloud Storage
- **IPFS**: Pinata pinning service
- **Blockchain**: Stacks (via Hiro API)
- **ML/AI**: TensorFlow, OpenCV, scikit-learn

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       ├── api.py              # API router
│   │       └── endpoints/          # API endpoints
│   │           ├── auth.py         # Authentication
│   │           ├── submissions.py  # Waste submissions
│   │           ├── validators.py   # Validator management
│   │           ├── rewards.py      # Rewards & claims
│   │           └── stats.py        # Statistics
│   ├── blockchain/
│   │   └── __init__.py            # Stacks RPC client & contract wrappers
│   ├── core/
│   │   ├── config.py              # Settings & configuration
│   │   ├── database.py            # Database connection
│   │   ├── security.py            # Auth & JWT
│   │   ├── ipfs.py                # IPFS client (Pinata)
│   │   └── storage.py             # GCP Storage client
│   ├── db/
│   │   └── init_db.py             # Database initialization
│   ├── ml/
│   │   └── __init__.py            # ML models (classifier, estimator, grader, fraud)
│   ├── models/
│   │   └── __init__.py            # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── __init__.py            # Pydantic validation schemas
│   ├── services/
│   │   ├── submission_service.py  # Submission business logic
│   │   ├── validator_service.py   # Validator business logic
│   │   └── reward_service.py      # Reward business logic
│   ├── workers/
│   │   ├── __init__.py            # Celery app
│   │   └── tasks.py               # Background tasks
│   └── main.py                    # FastAPI application
├── alembic/                       # Database migrations
├── tests/                         # Test suite
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container definition
├── .env.example                   # Environment variables template
└── alembic.ini                    # Alembic configuration
```

## Setup

### Prerequisites

- Python 3.11+
- Redis (for Celery)
- Google Cloud account (for storage)
- Pinata account (for IPFS)

### Installation

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -m app.db.init_db
   ```

6. **Run migrations** (if using PostgreSQL)
   ```bash
   alembic upgrade head
   ```

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Celery Workers

In a separate terminal:

```bash
celery -A app.workers worker --loglevel=info
```

### Redis

Ensure Redis is running:

```bash
redis-server
```

## Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=sqlite:///./satsverdant.db

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Stacks Blockchain
STACKS_NETWORK=testnet
STACKS_API_URL=https://stacks-node-api.testnet.stacks.co
STACKS_CONTRACT_DEPLOYER=ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM

# IPFS (Pinata)
IPFS_PINATA_API_KEY=your-pinata-api-key
IPFS_PINATA_SECRET_KEY=your-pinata-secret

# Google Cloud Storage
GCP_PROJECT_ID=your-gcp-project-id
GCP_STORAGE_BUCKET=satsverdant-temp-uploads
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/challenge` - Generate wallet signature challenge
- `POST /api/v1/auth/verify` - Verify signature and get JWT token
- `GET /api/v1/auth/me` - Get current user profile

### Submissions

- `POST /api/v1/submissions/` - Create new waste submission
- `GET /api/v1/submissions/` - List user's submissions
- `GET /api/v1/submissions/{id}` - Get submission details
- `POST /api/v1/submissions/{id}/submit` - Submit for validation

### Validators

- `POST /api/v1/validators/` - Register as validator
- `GET /api/v1/validators/` - List validators (leaderboard)
- `GET /api/v1/validators/me` - Get validator profile
- `GET /api/v1/validators/queue` - Get validation queue
- `POST /api/v1/validators/submissions/{id}/approve` - Approve submission
- `POST /api/v1/validators/submissions/{id}/reject` - Reject submission

### Rewards

- `GET /api/v1/rewards/` - List user's rewards
- `GET /api/v1/rewards/summary` - Get reward summary
- `POST /api/v1/rewards/{id}/claim` - Claim specific reward
- `POST /api/v1/rewards/claim-all` - Batch claim all rewards
- `GET /api/v1/rewards/estimate` - Estimate reward for submission

### Statistics

- `GET /api/v1/stats/global` - Platform-wide statistics
- `GET /api/v1/stats/user/{wallet_address}` - User public statistics

## Testing

Run the test suite:

```bash
pytest --cov=app --cov-report=html tests/
```

View coverage report:

```bash
open htmlcov/index.html
```

## Database Schema

### Core Tables

- **users** - User accounts (wallet-based)
- **submissions** - Waste submissions with AI classification
- **validators** - Validator profiles with staking info
- **rewards** - Token rewards and sBTC claims
- **transactions** - Blockchain transaction tracking
- **fraud_events** - Fraud detection events

See `docs/SatsVerdant_Backend_PRD_MVP.md` for detailed schema.

## Background Jobs

Celery tasks handle:

1. **classify_submission** - AI waste classification
2. **pin_to_ipfs** - Pin images to IPFS
3. **mint_tokens** - Mint waste tokens on Stacks
4. **confirm_transaction** - Monitor blockchain confirmations
5. **calculate_and_create_reward** - Create reward records
6. **distribute_reward** - Distribute sBTC rewards

## Deployment

### Docker

Build and run with Docker:

```bash
docker build -t satsverdant-backend .
docker run -p 8000:8000 --env-file .env satsverdant-backend
```

### Production Checklist

- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure GCP service account credentials
- [ ] Set up Pinata API keys
- [ ] Configure Stacks mainnet RPC
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Set up database backups
- [ ] Deploy Celery workers with supervisor/systemd

## Security

- Wallet-based authentication (signature verification)
- JWT tokens for session management
- Rate limiting on API endpoints
- Fraud detection on submissions
- Input validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)

## ML Models

The MVP includes placeholder ML models. For production:

1. Train waste classification model (see `docs/SatsVerdant_AI_ML_PRD_MVP.md`)
2. Train weight estimation model
3. Implement quality grading algorithm
4. Deploy fraud detection system

Model files should be placed in `app/ml/models/`.

## Contributing

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update documentation
4. Run tests before committing

## License

[Your License Here]

## Support

For issues and questions, please refer to the documentation in `/docs/`.
