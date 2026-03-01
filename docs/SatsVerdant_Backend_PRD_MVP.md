# SatsVerdant Backend PRD - MVP

## 1. Executive Summary

**Project:** SatsVerdant Backend API  
**Version:** 1.0 (MVP)  
**Timeline:** 12 weeks  
**Goal:** Production-ready backend to support waste tokenization, AI classification, validator verification, and sBTC reward distribution on Stacks blockchain.

---

## 2. Product Vision

Build a robust, scalable backend that:
- Accepts waste submissions via photo upload
- Classifies waste using AI/ML models
- Orchestrates validator approval workflows
- Mints tokens on Stacks blockchain
- Distributes sBTC rewards
- Provides real-time data to frontend/mobile clients

**Core Principle:** Security, auditability, and fraud prevention at every layer.

---

## 3. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Client Applications                        │
│           (Web App, Mobile App, Corporate Dashboard)          │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS/REST
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI Backend API                         │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────┐    │
│  │   Auth   │ Submiss. │ Rewards  │ Validat. │  Stats  │    │
│  └──────────┴──────────┴──────────┴──────────┴─────────┘    │
└────────────┬──────────┬──────────┬──────────┬────────────────┘
             │          │          │          │
             ▼          ▼          ▼          ▼
    ┌───────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
    │PostgreSQL │ │  Redis  │ │  IPFS   │ │  Stacks  │
    │    DB     │ │ Cache/Q │ │ Storage │ │   RPC    │
    └───────────┘ └─────────┘ └─────────┘ └──────────┘
                      │
                      ▼
            ┌──────────────────┐
            │  Celery Workers  │
            │  ┌────────────┐  │
            │  │ AI Classify│  │
            │  │    Mint    │  │
            │  │    IPFS    │  │
            │  │  Rewards   │  │
            │  └────────────┘  │
            └──────────────────┘
```

---

## 4. Technical Stack

### **Core Framework**
- **FastAPI** (Python 3.11+)
  - Type hints with Pydantic
  - Async/await support
  - Auto-generated OpenAPI docs
  - Fast performance (comparable to Node.js/Go)

### **Database**
- **PostgreSQL 15+**
  - JSONB for flexible metadata
  - Full-text search capabilities
  - PostGIS extension (geolocation)
  - Point-in-time recovery

### **Caching & Message Queue**
- **Redis 7+**
  - Caching (session data, computed rewards)
  - Celery broker
  - Rate limiting

### **Background Jobs**
- **Celery 5+**
  - Distributed task queue
  - Retry logic with exponential backoff
  - Task result backend (Redis)

### **Storage**
- **S3-compatible** (AWS S3, MinIO for local dev)
  - Temporary image storage
- **IPFS** (Pinata pinning service)
  - Permanent, immutable storage
  - Content addressing

### **Blockchain Integration**
- **Stacks RPC** (via Hiro API)
- **stacks-blockchain-api** (REST endpoints)
- **Python stacks SDK** (if available) or direct HTTP calls

### **AI/ML**
- **TensorFlow 2.x** or **PyTorch 2.x**
  - Pre-trained classification models
  - Transfer learning on waste dataset
- **OpenCV** (image preprocessing)
- **scikit-learn** (fraud detection algorithms)

### **Monitoring & Logging**
- **Prometheus** (metrics)
- **Grafana** (dashboards)
- **Sentry** (error tracking)
- **Structured logging** (JSON format)

### **Deployment**
- **Docker** + **Docker Compose** (local dev)
- **Render.com** or **Railway** (MVP hosting)
- **GitHub Actions** (CI/CD)

---

## 5. Database Schema

### **5.1 Tables**

#### **users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address TEXT UNIQUE NOT NULL,
    display_name TEXT,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'recycler' 
        CHECK (role IN ('recycler', 'validator', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_wallet ON users(wallet_address);
CREATE INDEX idx_users_role ON users(role);
```

#### **submissions**
```sql
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Image data
    image_s3_key TEXT,
    image_ipfs_cid TEXT,
    image_url TEXT,
    thumbnail_url TEXT,
    
    -- Location
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    location_accuracy DECIMAL(6, 2), -- meters
    
    -- AI Classification
    ai_waste_type TEXT CHECK (ai_waste_type IN ('plastic', 'paper', 'metal', 'organic', 'electronic')),
    ai_confidence DECIMAL(5, 4), -- 0.0000 to 1.0000
    ai_estimated_weight_kg DECIMAL(8, 3),
    ai_quality_grade TEXT CHECK (ai_quality_grade IN ('A', 'B', 'C', 'D')),
    ai_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Status workflow
    status TEXT NOT NULL DEFAULT 'pending_classification'
        CHECK (status IN (
            'pending_classification',
            'classified',
            'pending_validation',
            'approved',
            'rejected',
            'minting',
            'minted',
            'failed',
            'disputed'
        )),
    
    -- Validation
    validator_id UUID REFERENCES users(id),
    validated_at TIMESTAMP WITH TIME ZONE,
    validation_notes TEXT,
    
    -- Minting
    mint_tx_id TEXT,
    tokens_minted INTEGER,
    carbon_offset_g INTEGER, -- grams of CO2
    minted_at TIMESTAMP WITH TIME ZONE,
    
    -- Fraud detection
    fraud_score DECIMAL(3, 2), -- 0.00 to 1.00
    fraud_flags JSONB DEFAULT '[]'::jsonb,
    duplicate_of UUID REFERENCES submissions(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    device_info JSONB DEFAULT '{}'::jsonb,
    client_ip INET
);

CREATE INDEX idx_submissions_user ON submissions(user_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_validator ON submissions(validator_id);
CREATE INDEX idx_submissions_created ON submissions(created_at DESC);
CREATE INDEX idx_submissions_type ON submissions(ai_waste_type);
```

#### **validators**
```sql
CREATE TABLE validators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Staking
    stx_staked DECIMAL(18, 6) NOT NULL DEFAULT 0,
    stake_tx_id TEXT,
    staked_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance
    reputation_score INTEGER NOT NULL DEFAULT 100, -- 0-100
    validations_count INTEGER NOT NULL DEFAULT 0,
    approvals_count INTEGER NOT NULL DEFAULT 0,
    rejections_count INTEGER NOT NULL DEFAULT 0,
    accuracy_rate DECIMAL(5, 4), -- calculated field
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    suspended_until TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_validators_user ON validators(user_id);
CREATE INDEX idx_validators_active ON validators(is_active);
CREATE INDEX idx_validators_reputation ON validators(reputation_score DESC);
```

#### **rewards**
```sql
CREATE TABLE rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submission_id UUID REFERENCES submissions(id) ON DELETE SET NULL,
    
    -- Reward details
    waste_tokens INTEGER NOT NULL,
    sbtc_amount DECIMAL(18, 8) NOT NULL,
    conversion_rate DECIMAL(10, 6), -- tokens per sBTC at time of calculation
    
    -- Status
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'claimable', 'claimed', 'distributed', 'failed')),
    
    -- Transaction
    claim_tx_id TEXT,
    claimed_at TIMESTAMP WITH TIME ZONE,
    distributed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_rewards_user ON rewards(user_id);
CREATE INDEX idx_rewards_submission ON rewards(submission_id);
CREATE INDEX idx_rewards_status ON rewards(status);
CREATE INDEX idx_rewards_claimable ON rewards(status, user_id) WHERE status = 'claimable';
```

#### **transactions**
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Transaction details
    tx_id TEXT UNIQUE NOT NULL,
    tx_type TEXT NOT NULL 
        CHECK (tx_type IN ('mint', 'claim_reward', 'stake_validator', 'unstake_validator')),
    
    -- Related entities
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    user_id UUID REFERENCES users(id),
    
    -- Status
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'broadcasted', 'confirmed', 'failed', 'dropped')),
    
    -- Blockchain data
    block_height INTEGER,
    block_hash TEXT,
    confirmations INTEGER DEFAULT 0,
    
    -- Error handling
    error_code TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    broadcasted_at TIMESTAMP WITH TIME ZONE,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Raw data
    raw_payload JSONB,
    raw_response JSONB
);

CREATE INDEX idx_transactions_tx_id ON transactions(tx_id);
CREATE INDEX idx_transactions_entity ON transactions(entity_type, entity_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_created ON transactions(created_at DESC);
```

#### **fraud_events**
```sql
CREATE TABLE fraud_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    
    -- Fraud detection
    fraud_type TEXT NOT NULL
        CHECK (fraud_type IN (
            'duplicate_image',
            'location_clustering',
            'rapid_submission',
            'low_confidence',
            'suspicious_device',
            'validator_collusion'
        )),
    severity TEXT NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence DECIMAL(5, 4),
    
    -- Details
    description TEXT,
    evidence JSONB DEFAULT '{}'::jsonb,
    
    -- Actions
    action_taken TEXT,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fraud_events_submission ON fraud_events(submission_id);
CREATE INDEX idx_fraud_events_user ON fraud_events(user_id);
CREATE INDEX idx_fraud_events_type ON fraud_events(fraud_type);
CREATE INDEX idx_fraud_events_unresolved ON fraud_events(resolved) WHERE NOT resolved;
```

### **5.2 Database Functions & Triggers**

#### **Update timestamp trigger**
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_submissions_updated_at BEFORE UPDATE ON submissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_validators_updated_at BEFORE UPDATE ON validators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rewards_updated_at BEFORE UPDATE ON rewards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### **Calculate validator accuracy**
```sql
CREATE OR REPLACE FUNCTION calculate_validator_accuracy()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.validations_count > 0 THEN
        NEW.accuracy_rate = NEW.approvals_count::DECIMAL / NEW.validations_count::DECIMAL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_validator_accuracy BEFORE UPDATE ON validators
    FOR EACH ROW EXECUTE FUNCTION calculate_validator_accuracy();
```

---

## 6. API Specification

### **6.1 Base Configuration**

**Base URL:** `https://api.satsverdant.com/v1`  
**Protocol:** HTTPS only  
**Format:** JSON  
**Auth:** JWT Bearer token (from Stacks wallet signature)

**Rate Limits:**
- Authenticated: 100 req/min per wallet
- Anonymous: 10 req/min per IP
- Upload: 5 submissions per day per wallet (MVP)

### **6.2 Authentication**

#### **POST /auth/challenge**
Generate a signature challenge for wallet authentication.

**Request:**
```json
{
  "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM"
}
```

**Response:**
```json
{
  "challenge": "Sign this message to authenticate: 8a7d9c3b1e...",
  "expires_at": "2026-01-27T10:30:00Z"
}
```

#### **POST /auth/verify**
Verify signed challenge and issue JWT.

**Request:**
```json
{
  "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
  "signature": "0x5d8a...",
  "challenge": "Sign this message to authenticate: 8a7d9c3b1e..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
    "role": "recycler",
    "created_at": "2026-01-15T08:30:00Z"
  }
}
```

#### **GET /auth/me**
Get current user profile.

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
  "role": "recycler",
  "display_name": "Austin",
  "stats": {
    "submissions_count": 8,
    "tokens_earned": 450,
    "sbtc_earned": "0.0045",
    "carbon_offset_kg": 3.2
  },
  "created_at": "2026-01-15T08:30:00Z"
}
```

---

### **6.3 Submissions**

#### **POST /submissions**
Create a new waste submission (upload photo).

**Headers:** 
- `Authorization: Bearer {token}`
- `Content-Type: multipart/form-data`

**Request:**
```
image: [File] (max 10MB, JPEG/PNG/HEIC)
latitude: 52.3676 (optional)
longitude: 4.9041 (optional)
location_accuracy: 10.5 (optional, meters)
device_info: {"model": "iPhone 14", "os": "iOS 17"} (optional)
notes: "Plastic bottles from office" (optional)
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending_classification",
  "image_url": "https://storage.satsverdant.com/temp/abc123.jpg",
  "created_at": "2026-01-26T14:30:00Z",
  "estimated_processing_time_seconds": 30
}
```

**Status Codes:**
- `201 Created` - Submission created
- `400 Bad Request` - Invalid image format or size
- `401 Unauthorized` - Invalid or missing token
- `429 Too Many Requests` - Rate limit exceeded
- `413 Payload Too Large` - Image exceeds 10MB

#### **GET /submissions**
List user's submissions with pagination and filters.

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 20, max: 100)
- `status` (filter by status)
- `waste_type` (filter by type)
- `sort` (created_at, updated_at)
- `order` (asc, desc, default: desc)

**Response:**
```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "image_url": "https://ipfs.io/ipfs/QmX...",
      "thumbnail_url": "https://storage.satsverdant.com/thumb/abc.jpg",
      "ai_waste_type": "plastic",
      "ai_confidence": 0.9532,
      "ai_estimated_weight_kg": 0.5,
      "ai_quality_grade": "A",
      "status": "minted",
      "tokens_minted": 50,
      "carbon_offset_g": 250,
      "created_at": "2026-01-25T10:00:00Z",
      "minted_at": "2026-01-25T12:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 8,
    "total_pages": 1
  }
}
```

#### **GET /submissions/{id}**
Get detailed submission information.

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "image_url": "https://ipfs.io/ipfs/QmX...",
  "image_ipfs_cid": "QmX...",
  "thumbnail_url": "https://storage.satsverdant.com/thumb/abc.jpg",
  "location": {
    "latitude": 52.3676,
    "longitude": 4.9041,
    "accuracy": 10.5
  },
  "ai_classification": {
    "waste_type": "plastic",
    "confidence": 0.9532,
    "estimated_weight_kg": 0.5,
    "quality_grade": "A",
    "metadata": {
      "model_version": "v1.2.0",
      "processing_time_ms": 234
    }
  },
  "status": "minted",
  "tokens_minted": 50,
  "carbon_offset_g": 250,
  "mint_tx_id": "0x7a8b...",
  "validator": {
    "id": "789e4567-e89b-12d3-a456-426614174999",
    "wallet_address": "ST2...",
    "reputation_score": 95
  },
  "validated_at": "2026-01-25T11:00:00Z",
  "minted_at": "2026-01-25T12:30:00Z",
  "fraud_score": 0.02,
  "fraud_flags": [],
  "created_at": "2026-01-25T10:00:00Z",
  "updated_at": "2026-01-25T12:30:00Z"
}
```

#### **POST /submissions/{id}/submit**
Submit for validation (after reviewing AI classification).

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "confirm_classification": true,
  "override_weight_kg": 0.6 (optional)
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending_validation",
  "estimated_validation_time_minutes": 60,
  "estimated_reward": {
    "tokens": 50,
    "sbtc": "0.0005"
  }
}
```

---

### **6.4 Validation (Validator-only)**

#### **GET /validate/queue**
Get pending submissions for validation.

**Headers:** `Authorization: Bearer {token}`  
**Required Role:** `validator`

**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 20, max: 50)
- `waste_type` (filter)
- `min_confidence` (filter, default: 0.7)

**Response:**
```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "image_url": "https://ipfs.io/ipfs/QmX...",
      "ai_classification": {
        "waste_type": "plastic",
        "confidence": 0.9532,
        "estimated_weight_kg": 0.5,
        "quality_grade": "A"
      },
      "location": {
        "latitude": 52.3676,
        "longitude": 4.9041
      },
      "user_history": {
        "submissions_count": 5,
        "approval_rate": 0.8,
        "avg_confidence": 0.92
      },
      "fraud_indicators": {
        "score": 0.02,
        "flags": []
      },
      "created_at": "2026-01-26T10:00:00Z",
      "time_in_queue_minutes": 15
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 3,
    "total_pages": 1
  }
}
```

#### **POST /validate/{submission_id}/approve**
Approve a submission.

**Headers:** `Authorization: Bearer {token}`  
**Required Role:** `validator`

**Request:**
```json
{
  "notes": "Verified - clear images, appropriate classification",
  "override_weight_kg": 0.55 (optional),
  "override_quality": "A" (optional)
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "approved",
  "mint_job_id": "job_789...",
  "estimated_mint_time_seconds": 30
}
```

#### **POST /validate/{submission_id}/reject**
Reject a submission.

**Headers:** `Authorization: Bearer {token}`  
**Required Role:** `validator`

**Request:**
```json
{
  "reason": "poor_quality" | "wrong_classification" | "duplicate" | "fraud",
  "notes": "Image quality too low to verify waste type"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "rejected",
  "reason": "poor_quality",
  "user_notified": true
}
```

---

### **6.5 Rewards**

#### **GET /rewards**
List user's rewards.

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 20)
- `status` (claimable, claimed, all)

**Response:**
```json
{
  "summary": {
    "total_earned_sbtc": "0.0045",
    "total_earned_tokens": 450,
    "claimable_sbtc": "0.001",
    "claimable_tokens": 100,
    "claimed_sbtc": "0.0035",
    "pending_rewards": 2
  },
  "data": [
    {
      "id": "reward_123...",
      "submission_id": "sub_456...",
      "waste_tokens": 50,
      "sbtc_amount": "0.0005",
      "status": "claimable",
      "created_at": "2026-01-25T12:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 8,
    "total_pages": 1
  }
}
```

#### **POST /rewards/{reward_id}/claim**
Claim a specific reward.

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "id": "reward_123...",
  "status": "claimed",
  "transaction": {
    "tx_id": "0x9c7d...",
    "status": "broadcasted",
    "explorer_url": "https://explorer.stacks.co/txid/0x9c7d..."
  },
  "estimated_confirmation_time_seconds": 600
}
```

#### **POST /rewards/claim-all**
Batch claim all claimable rewards.

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "claimed_count": 3,
  "total_sbtc": "0.0015",
  "transaction": {
    "tx_id": "0x9c7d...",
    "status": "broadcasted",
    "explorer_url": "https://explorer.stacks.co/txid/0x9c7d..."
  }
}
```

---

### **6.6 Validators**

#### **GET /validators**
List all validators (public leaderboard).

**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 20)
- `sort` (reputation_score, validations_count, stx_staked)
- `order` (asc, desc)

**Response:**
```json
{
  "data": [
    {
      "id": "validator_123...",
      "wallet_address": "ST2...",
      "stx_staked": "1000.0",
      "reputation_score": 95,
      "validations_count": 150,
      "accuracy_rate": 0.96,
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 12,
    "total_pages": 1
  }
}
```

#### **POST /validators/stake**
Register as a validator by staking STX.

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "stx_amount": "1000.0",
  "tx_id": "0x5f8a..." // Proof of stake transaction
}
```

**Response:**
```json
{
  "id": "validator_123...",
  "user_id": "user_456...",
  "stx_staked": "1000.0",
  "status": "pending_confirmation",
  "can_validate_after": "2026-01-26T15:00:00Z" // After tx confirms
}
```

---

### **6.7 Stats & Analytics**

#### **GET /stats/global**
Get platform-wide statistics (public).

**Response:**
```json
{
  "total_waste_recycled_kg": 1240.5,
  "total_sbtc_distributed": "0.52",
  "total_tokens_minted": 124050,
  "total_carbon_offset_kg": 320.8,
  "active_recyclers": 89,
  "active_validators": 12,
  "submissions_last_24h": 23,
  "avg_classification_time_seconds": 28,
  "avg_validation_time_minutes": 45,
  "blockchain": {
    "network": "mainnet",
    "last_block": 152340,
    "contract_address": "SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7.waste-tokens"
  }
}
```

#### **GET /stats/user/{wallet_address}**
Get user-specific statistics (public).

**Response:**
```json
{
  "wallet_address": "ST1...",
  "submissions_count": 8,
  "tokens_earned": 450,
  "sbtc_earned": "0.0045",
  "carbon_offset_kg": 3.2,
  "waste_breakdown": {
    "plastic": 5,
    "paper": 2,
    "metal": 1,
    "organic": 0
  },
  "approval_rate": 0.875,
  "avg_confidence_score": 0.94,
  "rank": 23,
  "joined_at": "2026-01-15T08:30:00Z"
}
```

---

## 7. Background Jobs (Celery Tasks)

### **7.1 Task: classify_submission**

**Trigger:** After image upload  
**Priority:** High  
**Timeout:** 60 seconds  
**Retry:** 3 attempts with exponential backoff

**Input:**
```python
submission_id: UUID
```

**Process:**
1. Load image from S3
2. Preprocess (resize, normalize)
3. Run AI classification model
4. Run fraud detection (duplicate check, location clustering)
5. Calculate confidence score
6. Update submission record in DB
7. If confidence > 0.7: Set status to `classified`
8. If confidence < 0.7: Flag for manual review

**Output:**
```python
{
  "submission_id": UUID,
  "waste_type": str,
  "confidence": float,
  "estimated_weight_kg": float,
  "quality_grade": str,
  "fraud_score": float,
  "fraud_flags": List[str],
  "processing_time_ms": int
}
```

---

### **7.2 Task: pin_to_ipfs**

**Trigger:** After successful classification  
**Priority:** Medium  
**Timeout:** 120 seconds  
**Retry:** 5 attempts with exponential backoff

**Input:**
```python
submission_id: UUID
s3_key: str
```

**Process:**
1. Download image from S3
2. Upload to IPFS via Pinata API
3. Generate thumbnail (200x200)
4. Upload thumbnail to IPFS
5. Update submission record with IPFS CIDs
6. Delete from S3 (optional, keep for backup period)

**Output:**
```python
{
  "submission_id": UUID,
  "ipfs_cid": str,
  "thumbnail_ipfs_cid": str,
  "ipfs_url": str
}
```

---

### **7.3 Task: mint_tokens**

**Trigger:** After validator approval  
**Priority:** High  
**Timeout:** 180 seconds  
**Retry:** 3 attempts

**Input:**
```python
submission_id: UUID
validator_id: UUID
```

**Process:**
1. Load submission details
2. Calculate token amount:
   ```python
   tokens = weight_kg * 100 * quality_multiplier
   quality_multiplier = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.4}
   ```
3. Calculate carbon offset (kg CO₂):
   ```python
   carbon_offset_g = weight_kg * carbon_factor[waste_type]
   carbon_factors = {"plastic": 500, "paper": 200, "metal": 1200, "organic": 100}
   ```
4. Prepare Clarity contract call:
   ```clarity
   (contract-call? .waste-tokens mint-waste-token
     waste-type
     tokens
     recipient)
   ```
5. Sign transaction (via KMS/service account)
6. Broadcast to Stacks network
7. Update submission: `status = "minting"`, store `tx_id`
8. Enqueue `confirm_transaction` task

**Output:**
```python
{
  "submission_id": UUID,
  "tx_id": str,
  "tokens_minted": int,
  "carbon_offset_g": int,
  "status": "broadcasted"
}
```

---

### **7.4 Task: confirm_transaction**

**Trigger:** After broadcasting any transaction  
**Priority:** Medium  
**Timeout:** 600 seconds (10 min)  
**Retry:** Polling every 30s until confirmed or timeout

**Input:**
```python
tx_id: str
entity_type: str  # "submission", "reward", "validator"
entity_id: UUID
```

**Process:**
1. Poll Stacks API: `GET /extended/v1/tx/{tx_id}`
2. Check status:
   - `pending` → Keep polling
   - `success` → Update entity status, create reward record
   - `abort_by_response` or `abort_by_post_condition` → Mark as failed, notify user
3. If confirmed:
   - Update submission: `status = "minted"`
   - Create reward record: `status = "claimable"`
   - Update validator stats
4. If failed:
   - Update submission: `status = "failed"`
   - Log error
   - Notify admins

**Output:**
```python
{
  "tx_id": str,
  "status": str,
  "block_height": int,
  "confirmations": int,
  "confirmed_at": datetime
}
```

---

### **7.5 Task: calculate_and_create_reward**

**Trigger:** After successful token minting  
**Priority:** High  
**Timeout:** 30 seconds  
**Retry:** 3 attempts

**Input:**
```python
submission_id: UUID
tokens_minted: int
```

**Process:**
1. Get current sBTC conversion rate
   ```python
   sbtc_per_100_tokens = 0.0001  # Example rate
   sbtc_amount = (tokens_minted / 100) * sbtc_per_100_tokens
   ```
2. Create reward record:
   ```python
   reward = Reward(
     user_id=submission.user_id,
     submission_id=submission_id,
     waste_tokens=tokens_minted,
     sbtc_amount=sbtc_amount,
     conversion_rate=sbtc_per_100_tokens,
     status="claimable"
   )
   ```
3. Notify user (push notification, email if enabled)

**Output:**
```python
{
  "reward_id": UUID,
  "sbtc_amount": Decimal,
  "status": "claimable"
}
```

---

### **7.6 Task: distribute_reward**

**Trigger:** User claims reward  
**Priority:** High  
**Timeout:** 180 seconds  
**Retry:** 3 attempts

**Input:**
```python
reward_id: UUID
```

**Process:**
1. Load reward details
2. Prepare Clarity contract call:
   ```clarity
   (contract-call? .rewards-pool claim-reward
     waste-tokens
     recipient)
   ```
3. Burn waste tokens
4. Transfer sBTC from pool to user
5. Sign and broadcast transaction
6. Update reward: `status = "claimed"`, store `claim_tx_id`
7. Enqueue `confirm_transaction` task

**Output:**
```python
{
  "reward_id": UUID,
  "claim_tx_id": str,
  "sbtc_amount": Decimal,
  "status": "claimed"
}
```

---

### **7.7 Task: periodic_fraud_analysis**

**Trigger:** Cron job (every 6 hours)  
**Priority:** Low  
**Timeout:** 300 seconds

**Process:**
1. Analyze submission patterns:
   - Location clustering (same GPS for multiple submissions)
   - Rapid submissions (>5 per hour from one user)
   - Duplicate images (perceptual hashing)
   - Low confidence patterns
   - Validator collusion patterns
2. Flag suspicious submissions
3. Create fraud_events records
4. Notify admins if critical fraud detected
5. Auto-suspend users with fraud_score > 0.8

**Output:**
```python
{
  "analyzed_submissions": int,
  "fraud_events_created": int,
  "users_flagged": int,
  "users_suspended": int
}
```

---

## 8. AI/ML Pipeline

### **8.1 Waste Classification Model**

**Architecture:** Transfer learning on MobileNetV3 or EfficientNet-B0

**Training Data:**
- ImageNet pre-trained weights
- Fine-tune on custom waste dataset:
  - Plastic: 5,000 images
  - Paper: 4,000 images
  - Metal: 3,000 images
  - Organic: 2,000 images
  - Electronic: 1,000 images (optional for MVP)

**Input:** RGB image (224x224 or 256x256)  
**Output:** 
```python
{
  "waste_type": str,  # plastic, paper, metal, organic
  "confidence": float,  # 0.0 to 1.0
  "probabilities": {
    "plastic": 0.92,
    "paper": 0.05,
    "metal": 0.02,
    "organic": 0.01
  }
}
```

**Preprocessing:**
```python
def preprocess_image(image_bytes):
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (224, 224))
    image = image.astype('float32') / 255.0
    image = np.expand_dims(image, axis=0)
    return image
```

**Inference:**
```python
def classify_waste(image_bytes):
    preprocessed = preprocess_image(image_bytes)
    predictions = model.predict(preprocessed)
    class_idx = np.argmax(predictions[0])
    confidence = float(predictions[0][class_idx])
    
    class_names = ["plastic", "paper", "metal", "organic"]
    waste_type = class_names[class_idx]
    
    return {
        "waste_type": waste_type,
        "confidence": confidence,
        "probabilities": {
            class_names[i]: float(predictions[0][i])
            for i in range(len(class_names))
        }
    }
```

**Model Versioning:**
- Store model checkpoints in S3
- Tag with version (v1.0.0, v1.1.0)
- Track which model version classified each submission
- A/B test new models before full rollout

---

### **8.2 Weight Estimation**

**Approach:** Regression model or heuristic-based

**MVP Heuristic:**
```python
def estimate_weight(waste_type, image_metadata):
    # Extract image dimensions if available
    # Use object detection to count items
    
    # Simple heuristic for MVP
    base_weights = {
        "plastic": 0.5,  # kg
        "paper": 1.0,
        "metal": 0.8,
        "organic": 1.5
    }
    
    # Add variance ±20%
    base = base_weights.get(waste_type, 1.0)
    variance = random.uniform(0.8, 1.2)
    return round(base * variance, 2)
```

**Future:** Train regression model on labeled data (image → actual weight)

---

### **8.3 Fraud Detection**

#### **Duplicate Image Detection**
```python
import imagehash
from PIL import Image

def calculate_perceptual_hash(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    phash = imagehash.phash(image)
    return str(phash)

def check_duplicate(submission_id, phash, threshold=5):
    # Query DB for similar hashes
    similar = db.query("""
        SELECT id, image_hash 
        FROM submissions 
        WHERE user_id = :user_id 
          AND image_hash IS NOT NULL
    """)
    
    for sub in similar:
        distance = imagehash.hex_to_hash(phash) - imagehash.hex_to_hash(sub.image_hash)
        if distance < threshold:
            return {
                "is_duplicate": True,
                "duplicate_of": sub.id,
                "similarity": 1 - (distance / 64)
            }
    
    return {"is_duplicate": False}
```

#### **Location Clustering**
```python
def check_location_clustering(user_id, latitude, longitude):
    # Get user's recent submissions
    recent = db.query("""
        SELECT latitude, longitude
        FROM submissions
        WHERE user_id = :user_id
          AND latitude IS NOT NULL
          AND created_at > NOW() - INTERVAL '7 days'
    """)
    
    same_location_count = 0
    for sub in recent:
        distance_km = haversine_distance(
            (latitude, longitude),
            (sub.latitude, sub.longitude)
        )
        if distance_km < 0.05:  # Within 50 meters
            same_location_count += 1
    
    if same_location_count > 5:
        return {
            "flag": "location_clustering",
            "severity": "medium",
            "same_location_submissions": same_location_count
        }
    
    return None
```

#### **Rapid Submission Detection**
```python
def check_rapid_submissions(user_id):
    count = db.query("""
        SELECT COUNT(*) 
        FROM submissions
        WHERE user_id = :user_id
          AND created_at > NOW() - INTERVAL '1 hour'
    """).scalar()
    
    if count > 5:
        return {
            "flag": "rapid_submission",
            "severity": "high",
            "submissions_last_hour": count
        }
    
    return None
```

#### **Composite Fraud Score**
```python
def calculate_fraud_score(submission):
    score = 0.0
    flags = []
    
    # Low confidence (0-0.3 weight)
    if submission.ai_confidence < 0.7:
        score += (0.7 - submission.ai_confidence) * 0.3
        flags.append("low_confidence")
    
    # Duplicate image (0.5 weight)
    duplicate = check_duplicate(submission.id, submission.image_hash)
    if duplicate["is_duplicate"]:
        score += 0.5 * duplicate["similarity"]
        flags.append("duplicate_image")
    
    # Location clustering (0.2 weight)
    location_flag = check_location_clustering(
        submission.user_id,
        submission.latitude,
        submission.longitude
    )
    if location_flag:
        score += 0.2
        flags.append("location_clustering")
    
    # Rapid submission (0.3 weight)
    rapid_flag = check_rapid_submissions(submission.user_id)
    if rapid_flag:
        score += 0.3
        flags.append("rapid_submission")
    
    return {
        "fraud_score": min(score, 1.0),
        "flags": flags
    }
```

---

## 9. Blockchain Integration

### **9.1 Stacks RPC Client**

```python
import requests
from typing import Dict, Any

class StacksClient:
    def __init__(self, network: str = "testnet"):
        self.base_url = {
            "mainnet": "https://stacks-node-api.mainnet.stacks.co",
            "testnet": "https://stacks-node-api.testnet.stacks.co"
        }[network]
    
    def get_account_info(self, address: str) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/v2/accounts/{address}")
        return response.json()
    
    def get_transaction(self, tx_id: str) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/extended/v1/tx/{tx_id}")
        return response.json()
    
    def broadcast_transaction(self, signed_tx: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/v2/transactions",
            json=signed_tx
        )
        return response.json()
    
    def call_read_only_function(
        self,
        contract_address: str,
        contract_name: str,
        function_name: str,
        sender: str,
        arguments: list
    ) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/v2/contracts/call-read/{contract_address}/{contract_name}/{function_name}",
            json={
                "sender": sender,
                "arguments": arguments
            }
        )
        return response.json()
```

### **9.2 Contract Call Construction**

```python
from stacks_sdk import make_contract_call, AnchorMode

def mint_waste_tokens(
    waste_type: str,
    amount: int,
    recipient: str,
    service_account_key: str
):
    tx_options = {
        "contract_address": "SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7",
        "contract_name": "waste-tokens",
        "function_name": "mint-waste-token",
        "function_args": [
            string_ascii_cv(waste_type),
            uint_cv(amount),
            principal_cv(recipient)
        ],
        "sender_key": service_account_key,
        "network": StacksTestnet(),
        "anchor_mode": AnchorMode.ANY,
        "post_condition_mode": PostConditionMode.DENY,
        "fee": 2000  # micro-STX
    }
    
    transaction = make_contract_call(tx_options)
    result = broadcast_transaction(transaction)
    
    return {
        "tx_id": result["txid"],
        "status": "broadcasted"
    }
```

### **9.3 Transaction Monitoring**

```python
async def monitor_transaction(tx_id: str, timeout: int = 600):
    start_time = time.time()
    stacks_client = StacksClient()
    
    while time.time() - start_time < timeout:
        tx = stacks_client.get_transaction(tx_id)
        
        status = tx.get("tx_status")
        
        if status == "success":
            return {
                "status": "confirmed",
                "block_height": tx["block_height"],
                "tx_result": tx.get("tx_result")
            }
        elif status in ["abort_by_response", "abort_by_post_condition"]:
            return {
                "status": "failed",
                "error": tx.get("tx_result")
            }
        
        # Still pending
        await asyncio.sleep(30)
    
    return {
        "status": "timeout",
        "message": "Transaction confirmation timeout"
    }
```

---

## 10. Security

### **10.1 Authentication & Authorization**

**JWT Structure:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "wallet_address": "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM",
  "role": "recycler",
  "iat": 1706270400,
  "exp": 1706356800
}
```

**Signature Verification:**
```python
from stacks_sdk import verify_message_signature

def verify_wallet_signature(
    wallet_address: str,
    message: str,
    signature: str
) -> bool:
    try:
        is_valid = verify_message_signature(
            message=message,
            public_key=wallet_address,
            signature=signature
        )
        return is_valid
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False
```

**Role-Based Access Control:**
```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_role(required_role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role != required_role and current_user.role != "admin":
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires {required_role} role"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

@router.post("/validate/{submission_id}/approve")
@require_role("validator")
async def approve_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user)
):
    # Validator-only endpoint
    pass
```

### **10.2 Rate Limiting**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/submissions")
@limiter.limit("5/day")  # 5 submissions per day
async def create_submission(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # Check user-specific rate limit
    today_count = db.query(Submission).filter(
        Submission.user_id == current_user.id,
        Submission.created_at >= datetime.utcnow().date()
    ).count()
    
    if today_count >= 5:
        raise HTTPException(
            status_code=429,
            detail="Daily submission limit reached (5 per day)"
        )
    
    # Process submission
    pass
```

### **10.3 Input Validation**

```python
from pydantic import BaseModel, validator, constr
from typing import Optional

class SubmissionCreate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    notes: Optional[constr(max_length=500)] = None
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    @validator('location_accuracy')
    def validate_accuracy(cls, v):
        if v is not None and v < 0:
            raise ValueError('Location accuracy cannot be negative')
        return v
```

### **10.4 File Upload Security**

```python
from fastapi import UploadFile
import magic

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/heic"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_image_upload(file: UploadFile):
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )
    
    # Check MIME type (magic bytes, not extension)
    file_bytes = await file.read()
    mime = magic.from_buffer(file_bytes, mime=True)
    
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {ALLOWED_MIME_TYPES}"
        )
    
    # Reset file pointer
    file.file.seek(0)
    
    return file_bytes
```

### **10.5 Environment Variables & Secrets**

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    
    # Redis
    REDIS_URL: str
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_S3_BUCKET: str
    AWS_REGION: str = "us-east-1"
    
    # IPFS (Pinata)
    PINATA_API_KEY: str
    PINATA_SECRET_KEY: str
    
    # Stacks
    STACKS_NETWORK: str = "testnet"
    STACKS_SERVICE_ACCOUNT_KEY: str  # Stored in KMS/Vault
    CONTRACT_ADDRESS: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # API
    API_RATE_LIMIT: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Never commit secrets to git:**
- Use `.env` files (gitignored)
- Use environment variables in production
- Use secrets managers (AWS Secrets Manager, HashiCorp Vault)
- Use KMS for service account keys

---

## 11. Monitoring & Observability

### **11.1 Metrics (Prometheus)**

```python
from prometheus_client import Counter, Histogram, Gauge

# Counters
submissions_total = Counter(
    'submissions_total',
    'Total number of submissions',
    ['status', 'waste_type']
)

rewards_claimed_total = Counter(
    'rewards_claimed_total',
    'Total rewards claimed',
    ['user_role']
)

# Histograms
classification_duration = Histogram(
    'classification_duration_seconds',
    'Time to classify waste image',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

mint_duration = Histogram(
    'mint_duration_seconds',
    'Time to mint tokens',
    buckets=[10, 30, 60, 120, 300, 600]
)

# Gauges
pending_validations = Gauge(
    'pending_validations',
    'Number of submissions pending validation'
)

active_validators = Gauge(
    'active_validators',
    'Number of active validators'
)
```

**Expose metrics endpoint:**
```python
from prometheus_client import generate_latest

@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

### **11.2 Logging**

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        
        if hasattr(record, 'submission_id'):
            log_obj['submission_id'] = record.submission_id
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

# Configure logger
logger = logging.getLogger("satsverdant")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

**Usage:**
```python
logger.info(
    "Submission created",
    extra={
        "user_id": str(user.id),
        "submission_id": str(submission.id),
        "waste_type": submission.ai_waste_type
    }
)
```

### **11.3 Error Tracking (Sentry)**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
)

# Automatic error capture
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

---

## 12. Testing Strategy

### **12.1 Unit Tests**

```python
# tests/test_fraud_detection.py
import pytest
from app.ml.fraud_detector import check_duplicate, calculate_fraud_score

def test_duplicate_detection():
    # Mock submission with known hash
    result = check_duplicate(
        submission_id="test-123",
        phash="8f373714d3f1e000",
        threshold=5
    )
    assert result["is_duplicate"] == False

def test_fraud_score_calculation():
    submission = MockSubmission(
        ai_confidence=0.5,
        latitude=52.3676,
        longitude=4.9041
    )
    
    score = calculate_fraud_score(submission)
    assert 0.0 <= score["fraud_score"] <= 1.0
    assert "low_confidence" in score["flags"]
```

### **12.2 Integration Tests**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_submission():
    # Get auth token
    auth_response = client.post("/auth/verify", json={
        "wallet_address": "ST1TEST...",
        "signature": "0x...",
        "challenge": "test-challenge"
    })
    token = auth_response.json()["access_token"]
    
    # Upload image
    with open("tests/fixtures/plastic_bottle.jpg", "rb") as f:
        response = client.post(
            "/submissions",
            files={"image": f},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending_classification"

def test_validator_approval_flow():
    # Setup: Create submission
    submission = create_test_submission()
    
    # Validator approves
    response = client.post(
        f"/validate/{submission.id}/approve",
        json={"notes": "Looks good"},
        headers={"Authorization": f"Bearer {validator_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
```

### **12.3 Load Tests**

```python
# tests/locustfile.py
from locust import HttpUser, task, between

class SatsVerdantUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Authenticate
        response = self.client.post("/auth/verify", json={
            "wallet_address": "ST1TEST...",
            "signature": "0x...",
            "challenge": "test"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def view_submissions(self):
        self.client.get(
            "/submissions",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def upload_submission(self):
        with open("test_image.jpg", "rb") as f:
            self.client.post(
                "/submissions",
                files={"image": f},
                headers={"Authorization": f"Bearer {self.token}"}
            )
```

**Run:** `locust -f tests/locustfile.py --host=https://api.satsverdant.com`

---

## 13. Deployment

### **13.1 Docker Setup**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Run migrations and start server
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/satsverdant
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app
  
  worker:
    build: .
    command: celery -A app.workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/satsverdant
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: satsverdant
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### **13.2 CI/CD (GitHub Actions)**

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST https://api.render.com/v1/services/$SERVICE_ID/deploys \
            -H "Authorization: Bearer $RENDER_API_KEY"
```

---

## 14. MVP Acceptance Criteria

### **✅ Core Functionality**
- [ ] User can connect wallet and authenticate
- [ ] User can upload waste photo
- [ ] AI classifies waste with >85% accuracy
- [ ] Image stored on IPFS permanently
- [ ] Validator can approve/reject submissions
- [ ] Tokens minted on Stacks testnet
- [ ] User can claim sBTC rewards
- [ ] All transactions confirmed on-chain

### **✅ Performance**
- [ ] Image classification < 30 seconds
- [ ] API response time < 500ms (p95)
- [ ] Token minting < 5 minutes
- [ ] 99% uptime

### **✅ Security**
- [ ] No secrets in codebase
- [ ] Rate limiting active
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] CORS properly configured

### **✅ Data Quality**
- [ ] Fraud detection catches obvious duplicates
- [ ] Database backups automated
- [ ] Audit logs for all critical actions
- [ ] Monitoring alerts configured

### **✅ User Experience**
- [ ] Clear error messages
- [ ] Transaction status tracking
- [ ] Email/push notifications (optional for MVP)
- [ ] OpenAPI documentation published

---

## 15. Post-MVP Roadmap

### **Phase 2 (Weeks 13-20)**
- WebSocket support for real-time updates
- Advanced fraud detection (ML-based)
- Mobile app API optimizations
- Governance voting endpoints
- Carbon credit marketplace API

### **Phase 3 (Weeks 21-32)**
- Multi-language support
- Advanced analytics dashboard
- Webhook support for integrations
- GraphQL API
- Batch operations for enterprises

---

This Backend PRD provides a complete blueprint for building the SatsVerdant MVP backend. All components are production-ready and aligned with the frontend and system architecture.
