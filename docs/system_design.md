# SatsVerdant MVP System Architecture

## **MVP Scope (12 Weeks to Launch)**

Focus on **core value loop**: Photo → AI Classification → Validator Approval → Token Minting → sBTC Rewards

---

## **Complete Folder Structure**

```
satsverdant/
│
├── contracts/                          # Clarity smart contracts
│   ├── waste-tokens.clar              # SIP-010 waste token (plastic, paper, metal, organic)
│   ├── validator-pool.clar            # Simple validator staking (STX)
│   └── rewards-pool.clar              # Basic sBTC reward distribution
│
├── backend/                            # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   │
│   │   ├── api/                       # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # Wallet signature verification
│   │   │   ├── submissions.py         # Waste submission endpoints
│   │   │   ├── validators.py          # Validator queue & approval
│   │   │   └── rewards.py             # Reward claims
│   │   │
│   │   ├── ml/                        # AI/ML services
│   │   │   ├── __init__.py
│   │   │   ├── classifier.py          # Waste classification model
│   │   │   ├── fraud_detector.py      # Image deduplication
│   │   │   └── models/                # Trained models
│   │   │       └── waste_classifier_v1.h5
│   │   │
│   │   ├── blockchain/                # Stacks integration
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # Stacks RPC client
│   │   │   └── contracts.py           # Contract call wrappers
│   │   │
│   │   ├── workers/                   # Background jobs (Celery)
│   │   │   ├── __init__.py
│   │   │   ├── classify.py            # AI classification job
│   │   │   ├── mint.py                # Token minting job
│   │   │   └── ipfs.py                # IPFS pinning job
│   │   │
│   │   ├── models/                    # Database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── submission.py
│   │   │   ├── validator.py
│   │   │   └── transaction.py
│   │   │
│   │   ├── schemas/                   # Pydantic schemas (validation)
│   │   │   ├── __init__.py
│   │   │   ├── submission.py
│   │   │   ├── validator.py
│   │   │   └── reward.py
│   │   │
│   │   ├── services/                  # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── submission_service.py
│   │   │   ├── validator_service.py
│   │   │   └── reward_service.py
│   │   │
│   │   ├── core/                      # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Settings & env vars
│   │   │   ├── database.py            # DB connection
│   │   │   ├── security.py            # Auth helpers
│   │   │   └── ipfs.py                # IPFS client
│   │   │
│   │   └── db/
│   │       ├── migrations/            # Alembic migrations
│   │       │   └── versions/
│   │       └── init_db.py
│   │
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_ml.py
│   │   └── test_services.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── web/                                # Next.js web app (validators/corporate)
│   ├── public/
│   │   ├── logo.svg
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── app/                       # Next.js 14 app router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx               # Landing page
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx           # User dashboard
│   │   │   ├── validate/
│   │   │   │   └── page.tsx           # Validator queue
│   │   │   └── rewards/
│   │   │       └── page.tsx           # Rewards page
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   └── dialog.tsx
│   │   │   ├── WalletConnect.tsx      # Stacks Connect
│   │   │   ├── SubmissionCard.tsx
│   │   │   ├── ValidatorQueue.tsx
│   │   │   └── RewardsDisplay.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── stacks.ts              # Stacks.js utilities
│   │   │   ├── api.ts                 # Backend API client
│   │   │   └── contracts.ts           # Contract addresses/ABIs
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWallet.ts
│   │   │   ├── useContract.ts
│   │   │   └── useSubmissions.ts
│   │   │
│   │   └── contexts/
│   │       └── StacksContext.tsx
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── next.config.js
│
├── mobile/                             # React Native mobile app (recyclers)
│   ├── src/
│   │   ├── screens/
│   │   │   ├── HomeScreen.tsx         # Main screen
│   │   │   ├── CameraScreen.tsx       # Photo capture
│   │   │   ├── DashboardScreen.tsx    # User stats
│   │   │   └── RewardsScreen.tsx      # Rewards view
│   │   │
│   │   ├── components/
│   │   │   ├── WalletButton.tsx       # Stacks mobile wallet
│   │   │   ├── CameraCapture.tsx      # Camera UI
│   │   │   ├── SubmissionList.tsx
│   │   │   └── RewardCard.tsx
│   │   │
│   │   ├── navigation/
│   │   │   └── AppNavigator.tsx       # React Navigation
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts                 # Backend API
│   │   │   ├── camera.ts              # Camera service
│   │   │   ├── location.ts            # GPS service
│   │   │   └── wallet.ts              # Stacks wallet integration
│   │   │
│   │   ├── hooks/
│   │   │   ├── useCamera.ts
│   │   │   ├── useLocation.ts
│   │   │   └── useWallet.ts
│   │   │
│   │   └── utils/
│   │       ├── imageCompression.ts
│   │       └── constants.ts
│   │
│   ├── android/
│   ├── ios/
│   ├── app.json
│   └── package.json
│
├── tests/
│   ├── contracts/                     # Clarity contract tests
│   │   ├── waste-tokens.test.ts       # Unit tests
│   │   ├── validator-pool.test.ts
│   │   ├── rewards-pool.test.ts
│   │   └── integration.test.ts        # Integration tests
│   │
│   └── e2e/                           # End-to-end tests
│       └── user-flow.spec.ts          # Playwright
│
├── infra/                             # Infrastructure (optional for MVP)
│   ├── docker-compose.yml             # Local dev stack
│   └── render.yaml                    # Render.com config
│
├── scripts/
│   ├── deploy-contracts.sh            # Deploy to testnet/mainnet
│   ├── seed-db.py                     # Seed test data
│   └── train-model.py                 # Train ML model
│
├── docs/
│   ├── API.md                         # API documentation
│   ├── CONTRACTS.md                   # Smart contract docs
│   └── SETUP.md                       # Local setup guide
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       ├── web-ci.yml
│       └── mobile-ci.yml
│
├── Clarinet.toml                      # Clarinet config
├── settings/
│   ├── Devnet.toml
│   └── Testnet.toml
│
├── README.md
└── .gitignore
```

---

## **Tech Stack Decisions**

### **Smart Contracts**
- **Clarity** (Stacks native)
- **Clarinet** for local development & testing
- **Deployment:** Testnet first, then mainnet

### **Backend**
- **FastAPI** (Python 3.11+)
- **PostgreSQL** (primary database)
- **Redis** (caching + Celery broker)
- **Celery** (async workers)
- **SQLAlchemy** (ORM)
- **Alembic** (migrations)
- **IPFS** (Pinata for pinning service)
- **Deployment:** Render.com or Railway (simple, affordable)

### **Web App** (Validators/Corporate)
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** + **shadcn/ui**
- **Stacks.js** (wallet integration)
- **React Query** (data fetching)
- **Deployment:** Vercel

### **Mobile App** (Recyclers)
- **React Native** + **Expo**
- **TypeScript**
- **React Navigation**
- **Expo Camera** (photo capture)
- **Expo Location** (GPS)
- **AsyncStorage** (local data)
- **Stacks Connect Mobile** (wallet)
- **Deployment:** Expo EAS (TestFlight/Play Store)

### **ML/AI**
- **TensorFlow/Keras** or **PyTorch**
- **OpenCV** (image processing)
- **scikit-learn** (fraud detection)
- **Hugging Face Transformers** (optional for advanced classification)

---

## **MVP Data Models**

### **PostgreSQL Schema**

```sql
-- users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('recycler', 'validator', 'admin')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- submissions
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    image_ipfs_cid TEXT,
    image_url TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- AI classification
    ai_waste_type TEXT CHECK (ai_waste_type IN ('plastic', 'paper', 'metal', 'organic')),
    ai_confidence DECIMAL(5, 4),
    ai_weight_kg DECIMAL(8, 3),
    
    -- Status
    status TEXT DEFAULT 'pending_classification' 
        CHECK (status IN ('pending_classification', 'pending_validation', 'approved', 'rejected', 'minted')),
    
    -- Validation
    validator_id UUID REFERENCES users(id),
    validated_at TIMESTAMP,
    
    -- Minting
    mint_tx_id TEXT,
    tokens_minted INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- validators
CREATE TABLE validators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id),
    stx_staked DECIMAL(18, 6),
    reputation_score INTEGER DEFAULT 100,
    validations_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- rewards
CREATE TABLE rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    submission_id UUID REFERENCES submissions(id),
    sbtc_amount DECIMAL(18, 8),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'claimed', 'distributed')),
    claim_tx_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- transactions (audit log)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tx_id TEXT UNIQUE NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    action TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## **MVP API Endpoints**

### **Authentication**
```
POST   /api/auth/connect          # Verify wallet signature
GET    /api/auth/me               # Get current user
```

### **Submissions**
```
POST   /api/submissions           # Upload waste photo
GET    /api/submissions           # List user's submissions
GET    /api/submissions/:id       # Get submission details
POST   /api/submissions/:id/submit # Submit for validation
```

### **Validation** (Validator-only)
```
GET    /api/validate/queue        # Get pending submissions
POST   /api/validate/:id/approve  # Approve submission
POST   /api/validate/:id/reject   # Reject submission
```

### **Rewards**
```
GET    /api/rewards               # List user rewards
POST   /api/rewards/:id/claim     # Claim sBTC reward
GET    /api/rewards/stats         # Get reward stats
```

### **Stats** (Public)
```
GET    /api/stats/global          # Global platform stats
GET    /api/stats/user/:address   # User stats
```

---

## **MVP Smart Contracts**

### **1. waste-tokens.clar**
```clarity
;; SIP-010 Fungible Token for waste types
(define-fungible-token plastic-token)
(define-fungible-token paper-token)
(define-fungible-token metal-token)
(define-fungible-token organic-token)

;; Mint tokens after validation
(define-public (mint-waste-token 
    (waste-type (string-ascii 10))
    (amount uint)
    (recipient principal))
  (begin
    ;; Only authorized minter (backend service account)
    (asserts! (is-eq tx-sender contract-owner) (err u403))
    
    (match waste-type
      "plastic" (ft-mint? plastic-token amount recipient)
      "paper" (ft-mint? paper-token amount recipient)
      "metal" (ft-mint? metal-token amount recipient)
      "organic" (ft-mint? organic-token amount recipient)
      (err u404))))

;; Get token balance
(define-read-only (get-balance (waste-type (string-ascii 10)) (account principal))
  (match waste-type
    "plastic" (ok (ft-get-balance plastic-token account))
    "paper" (ok (ft-get-balance paper-token account))
    "metal" (ok (ft-get-balance metal-token account))
    "organic" (ok (ft-get-balance organic-token account))
    (err u404)))
```

### **2. validator-pool.clar**
```clarity
;; Simple validator staking
(define-map validators principal {
  staked: uint,
  reputation: uint,
  validations: uint
})

(define-public (stake-as-validator (amount uint))
  (begin
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    (map-set validators tx-sender {
      staked: amount,
      reputation: u100,
      validations: u0
    })
    (ok true)))

(define-read-only (get-validator (validator principal))
  (map-get? validators validator))
```

### **3. rewards-pool.clar**
```clarity
;; Basic sBTC reward distribution
(define-constant reward-rate u10) ;; 10% of token value

(define-public (claim-reward (waste-tokens uint))
  (let ((sbtc-reward (/ (* waste-tokens reward-rate) u100)))
    (begin
      ;; Burn waste tokens
      (try! (contract-call? .waste-tokens burn-token waste-tokens tx-sender))
      
      ;; Transfer sBTC from pool
      (try! (as-contract (stx-transfer? sbtc-reward tx-sender (as-contract tx-sender))))
      
      (ok sbtc-reward))))
```

---

## **MVP Data Flow**

### **1. Photo Submission Flow**
```
[Mobile App]
    ↓ User takes photo
    ↓ Compress image (max 2MB)
    ↓ Get GPS location
    ↓
POST /api/submissions
    ↓
[Backend API]
    ↓ Save to temp storage (S3)
    ↓ Create DB record (status: pending_classification)
    ↓ Enqueue classification job
    ↓ Return submission_id
    ↓
[Celery Worker - classify.py]
    ↓ Load AI model
    ↓ Classify image → {type, confidence, weight}
    ↓ Run fraud detection (duplicate check)
    ↓ Update DB (status: pending_validation)
    ↓ Pin to IPFS
    ↓
[Mobile App polls GET /api/submissions/:id]
    ↓ Show classification result
    ↓ User confirms submission
    ↓
POST /api/submissions/:id/submit
    ↓ Update status: pending_validation
```

### **2. Validation Flow**
```
[Web App - Validator]
    ↓
GET /api/validate/queue
    ↓ Returns pending submissions
    ↓ Validator reviews image + AI classification
    ↓
POST /api/validate/:id/approve
    ↓
[Backend API]
    ↓ Update DB (status: approved, validator_id)
    ↓ Enqueue minting job
    ↓
[Celery Worker - mint.py]
    ↓ Calculate tokens (weight * quality_factor)
    ↓ Call Clarity contract: mint-waste-token
    ↓ Broadcast transaction
    ↓ Wait for confirmation
    ↓ Update DB (status: minted, mint_tx_id, tokens_minted)
    ↓ Create reward record
    ↓
[Mobile App - Push Notification]
    ↓ "Your submission was approved! 50 tokens minted"
```

### **3. Reward Claim Flow**
```
[Mobile/Web App]
    ↓
GET /api/rewards
    ↓ Shows claimable rewards
    ↓
POST /api/rewards/:id/claim
    ↓
[Backend API]
    ↓ Calculate sBTC amount
    ↓ Call Clarity contract: claim-reward
    ↓ Broadcast transaction
    ↓ Update DB (status: claimed, claim_tx_id)
    ↓
[User Wallet]
    ↓ Receives sBTC
```

---

## **MVP Deployment Architecture**

```
┌─────────────┐
│   Mobile    │───┐
│     App     │   │
└─────────────┘   │
                  │
┌─────────────┐   │    ┌──────────────┐
│   Web App   │───┼───▶│   Backend    │
│  (Vercel)   │   │    │ (Render.com) │
└─────────────┘   │    └──────────────┘
                  │           │
                  │           ├─▶ PostgreSQL (Render)
                  │           ├─▶ Redis (Render)
                  │           ├─▶ Celery Workers
                  │           ├─▶ IPFS (Pinata)
                  │           └─▶ Stacks RPC
                  │
                  └─────────────────────┐
                                        │
                               ┌────────▼────────┐
                               │ Stacks Testnet  │
                               │   Contracts     │
                               └─────────────────┘
```

---

## **MVP Development Timeline (12 Weeks)**

### **Week 1-2: Foundation**
- [ ] Set up repos (monorepo or separate?)
- [ ] Backend skeleton (FastAPI + DB + Redis)
- [ ] Basic Clarity contracts
- [ ] Deploy contracts to testnet

### **Week 3-4: Core Backend**
- [ ] Submission API
- [ ] AI classification (mock → real model)
- [ ] IPFS integration
- [ ] Celery workers

### **Week 5-6: Web App**
- [ ] Next.js setup
- [ ] Wallet connection
- [ ] Validator queue UI
- [ ] Dashboard

### **Week 7-8: Mobile App**
- [ ] React Native setup
- [ ] Camera capture
- [ ] Submission flow
- [ ] Rewards display

### **Week 9-10: Integration**
- [ ] Contract integration
- [ ] End-to-end testing
- [ ] Bug fixes

### **Week 11: Testing & Polish**
- [ ] 10 true fans testing
- [ ] Feedback implementation
- [ ] Security audit (basic)

### **Week 12: Launch**
- [ ] Deploy to mainnet
- [ ] Submit to app stores
- [ ] Launch marketing

---

## **MVP Success Metrics**

**Technical:**
- [ ] Contracts deployed to mainnet
- [ ] API uptime > 99%
- [ ] AI classification accuracy > 85%
- [ ] Image → minting < 5 min average

**User:**
- [ ] 10 recyclers with real transactions
- [ ] 3 validators actively validating
- [ ] 100+ submissions processed
- [ ] 50+ tokens minted

**Business:**
- [ ] Landing page conversion > 3%
- [ ] User retention > 40% (week 1)
- [ ] Average 3+ submissions per user

---

