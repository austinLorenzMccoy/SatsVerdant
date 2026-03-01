# SatsVerdant Backend - Quick Start Guide

## ✅ Setup Complete!

Your backend is now configured with:
- ✅ Poetry dependency management
- ✅ Virtual environment (`.venv/`)
- ✅ Environment variables (`.env`)
- ✅ Groq API integration (free tier)
- ✅ All core dependencies installed

---

## 🚀 Start the Backend

### Option 1: Using Make (Recommended)

```bash
# Start development server
make run

# Or run tests
make test

# Format code
make format

# See all commands
make help
```

### Option 2: Using Poetry

```bash
# Activate virtual environment
poetry shell

# Start server
uvicorn app.main:app --reload

# Or run directly
poetry run uvicorn app.main:app --reload
```

### Option 3: Manual

```bash
# Activate venv
source .venv/bin/activate

# Start server
uvicorn app.main:app --reload
```

---

## 🌐 Access the API

Once running, access:

- **API Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/v1/health

---

## 📋 Common Commands

```bash
# Install new dependency
poetry add package-name

# Install dev dependency
poetry add -D package-name

# Update dependencies
poetry update

# Run tests
poetry run pytest

# Format code
poetry run black app tests
poetry run isort app tests

# Type checking
poetry run mypy app

# Database migrations
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "description"

# Export to requirements.txt (for Docker)
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

---

## 🔧 Configuration

### Environment Variables

Edit `.env` file to configure:

**Required:**
- `GROQ_API_KEY` - Your Groq API key (already set ✅)
- `SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `JWT_SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

**Optional (for full features):**
- `IPFS_PINATA_API_KEY` - For IPFS storage
- `GCP_PROJECT_ID` - For Google Cloud Storage
- `REDIS_URL` - For caching (default: localhost)

### Database

**SQLite (Default - No setup needed):**
```env
DATABASE_URL=sqlite:///./satsverdant.db
```

**PostgreSQL (Production):**
```env
DATABASE_URL=postgresql://user:password@localhost/satsverdant
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test
poetry run pytest tests/test_api.py

# Watch mode
poetry run pytest-watch
```

---

## 📦 Project Structure

```
backend/
├── .venv/                 # Virtual environment
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core config, security
│   ├── db/               # Database setup
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── ml/               # ML models
│   └── main.py           # FastAPI app
├── tests/                # Test suite
├── alembic/              # Database migrations
├── .env                  # Environment variables
├── pyproject.toml        # Poetry config
├── Makefile              # Convenient commands
└── README.md
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError"

```bash
# Reinstall dependencies
poetry install
```

### "Redis connection refused"

```bash
# Install and start Redis
brew install redis
brew services start redis
```

### "Database not found"

```bash
# Initialize database
poetry run alembic upgrade head
```

### "Port 8000 already in use"

```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

---

## 📚 Next Steps

1. ✅ **Backend is running** - You're done!
2. **Test API** - Visit http://localhost:8000/docs
3. **Deploy contracts** - See `contracts/DEPLOYMENT_GUIDE.md`
4. **Train ML models** - See `ml-training/README.md`
5. **Connect frontend** - Frontend already running on port 3000

---

## 🔗 Related Documentation

- **ML Training:** `/ml-training/README.md`
- **Smart Contracts:** `/contracts/DEPLOYMENT_GUIDE.md`
- **Environment Setup:** `ENV_SETUP_GUIDE.md`
- **API Documentation:** http://localhost:8000/docs (when running)

---

## 💡 Tips

- Use `poetry shell` to activate the virtual environment
- Use `make` commands for common tasks
- Check `.env` file for configuration
- TensorFlow is optional - install only for ML training: `poetry install --with ml`
- Groq API is free and fast - perfect for MVP!

---

**Your backend is ready to go! 🚀**

Start with: `make run` or `poetry run uvicorn app.main:app --reload`
