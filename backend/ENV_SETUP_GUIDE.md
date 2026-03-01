# Environment Variables Setup Guide

## Quick Start

A `.env` file has been created from `.env.example`. You need to update it with your actual API keys and credentials.

```bash
# Edit the .env file
nano .env  # or use your preferred editor
```

## Required API Keys & Credentials

### 1. **Groq AI API Key** (for LLM features)

Get your API key from: https://console.groq.com/

```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

**How to get it:**
1. Go to https://console.groq.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create new API key
5. Copy and paste into `.env`

---

### 2. **Pinata API Keys** (for IPFS storage)

Get your API keys from: https://app.pinata.cloud/

```env
IPFS_PINATA_API_KEY=your_pinata_api_key
IPFS_PINATA_SECRET_KEY=your_pinata_secret_key
```

**How to get it:**
1. Go to https://app.pinata.cloud/
2. Sign up for free account
3. Go to API Keys section
4. Create new API key with admin permissions
5. Copy both API Key and Secret Key

---

### 3. **Google Cloud Storage** (for temporary image uploads)

Get credentials from: https://console.cloud.google.com/

```env
GCP_PROJECT_ID=your-gcp-project-id
GCP_STORAGE_BUCKET=satsverdant-temp-uploads
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

**How to set up:**
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Cloud Storage API
4. Create a storage bucket named `satsverdant-temp-uploads`
5. Create service account:
   - IAM & Admin → Service Accounts → Create
   - Grant "Storage Admin" role
   - Create JSON key
   - Download and save to secure location
6. Update path in `.env`

---

### 4. **Security Keys** (generate random strings)

```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

**Generate secure keys:**
```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste into `.env`

---

### 5. **Stacks Blockchain** (for testnet)

```env
STACKS_NETWORK=testnet
STACKS_API_URL=https://api.testnet.hiro.so
STACKS_CONTRACT_DEPLOYER=ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM
```

**Update after deploying contracts:**
- Replace `STACKS_CONTRACT_DEPLOYER` with your actual deployer address after running `clarinet deployments apply --testnet`

---

## Optional API Keys

### **OpenAI API Key** (optional, for GPT models)

```env
OPENAI_API_KEY=sk-your_openai_api_key_here
```

Get from: https://platform.openai.com/api-keys

### **Anthropic API Key** (optional, for Claude models)

```env
ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here
```

Get from: https://console.anthropic.com/

### **HuggingFace API Key** (optional, for HF models)

```env
HUGGINGFACE_API_KEY=hf_your_huggingface_api_key_here
```

Get from: https://huggingface.co/settings/tokens

---

## Database Configuration

### **SQLite (Default for MVP)**

```env
DATABASE_URL=sqlite:///./satsverdant.db
```

No additional setup needed - SQLite file will be created automatically.

### **Redis (for Celery/caching)**

```env
REDIS_URL=redis://localhost:6379/0
```

**Install Redis:**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis
```

---

## Verification

After updating `.env`, verify your configuration:

```bash
# Check if all required keys are set
python3 -c "
from dotenv import load_dotenv
import os

load_dotenv()

required = [
    'SECRET_KEY',
    'JWT_SECRET_KEY',
    'GROQ_API_KEY',
    'IPFS_PINATA_API_KEY',
    'IPFS_PINATA_SECRET_KEY',
    'GCP_PROJECT_ID',
]

missing = [k for k in required if not os.getenv(k) or os.getenv(k).startswith('your-')]

if missing:
    print('❌ Missing or placeholder values:')
    for k in missing:
        print(f'  - {k}')
else:
    print('✅ All required environment variables are set!')
"
```

---

## Security Best Practices

1. **Never commit `.env` to git** (already in `.gitignore`)
2. **Use different keys for dev/staging/production**
3. **Rotate keys regularly**
4. **Use environment-specific `.env` files:**
   - `.env.development`
   - `.env.staging`
   - `.env.production`
5. **Store production keys in secure vault** (e.g., AWS Secrets Manager, HashiCorp Vault)

---

## Example Complete `.env`

```env
# Database
DATABASE_URL=sqlite:///./satsverdant.db
REDIS_URL=redis://localhost:6379/0

# Security (REPLACE WITH ACTUAL GENERATED KEYS)
SECRET_KEY=xK9mP2nQ5rT8vW1yZ4bC6dF7gH0jL3mN5pR8sU1wX4zA7cE9fG2hJ5kM8nP0qS3t
JWT_SECRET_KEY=aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3aB4cD5eF6gH7iJ8kL9mN0oP1q
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stacks Blockchain
STACKS_NETWORK=testnet
STACKS_API_URL=https://api.testnet.hiro.so
STACKS_CONTRACT_DEPLOYER=ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM

# IPFS (REPLACE WITH YOUR ACTUAL KEYS)
IPFS_PINATA_API_KEY=abc123def456ghi789jkl012mno345pqr
IPFS_PINATA_SECRET_KEY=xyz987wvu654tsr321qpo098nml765kji
IPFS_GATEWAY_URL=https://gateway.pinata.cloud/ipfs/

# Google Cloud Storage (REPLACE WITH YOUR ACTUAL VALUES)
GCP_PROJECT_ID=satsverdant-mvp-12345
GCP_STORAGE_BUCKET=satsverdant-temp-uploads
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourname/keys/satsverdant-gcp-key.json

# AI/ML API Keys (REPLACE WITH YOUR ACTUAL KEYS)
GROQ_API_KEY=gsk_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
OPENAI_API_KEY=sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
ANTHROPIC_API_KEY=sk-ant-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
HUGGINGFACE_API_KEY=hf_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz

# ML Model Paths
MODEL_PATH=./models
WEIGHT_ESTIMATOR_MODEL=./models/weight_estimator.h5

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=SatsVerdant
PROJECT_VERSION=1.0.0
PROJECT_DESCRIPTION=Waste Tokenization Platform on Stacks

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
UPLOAD_RATE_LIMIT_PER_DAY=5
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"

```bash
poetry add python-dotenv
```

### "Google Cloud credentials not found"

Make sure the path in `GOOGLE_APPLICATION_CREDENTIALS` is absolute and the file exists:

```bash
ls -la /path/to/service-account-key.json
```

### "Redis connection refused"

Start Redis:
```bash
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

---

## Next Steps

1. ✅ Update `.env` with actual API keys
2. ✅ Generate security keys
3. ✅ Set up GCP and Pinata accounts
4. ✅ Install and start Redis
5. ✅ Run the backend: `poetry run uvicorn app.main:app --reload`
