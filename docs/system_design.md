# SatsVerdant — MVP System Architecture v2.0

**Version:** 2.0 (Supabase-native)
**Baseline:** MVP v2.1 — Supabase + Groq + MLflow + DVC + DagsHub

### What Changed from v1.0

| Area | v1.0 | v2.0 |
|---|---|---|
| Backend | Python FastAPI + SQLAlchemy + Alembic | **Supabase PostgreSQL + Edge Functions (Deno)** |
| Async workers | Redis + Celery | **Supabase Edge Functions (serverless)** |
| Storage | AWS S3 + Pinata IPFS | **Supabase Storage** (IPFS CID still recorded) |
| Auth | Custom wallet signature | **Supabase Auth + Stacks Connect OAuth** |
| DB migrations | Alembic | **Supabase CLI (`supabase db push`)** |
| Deployment | Docker + Render.com | **Supabase cloud (fully managed)** |
| AI inference | TF Serving / self-hosted | **Groq API via Edge Function** |
| ML tracking | None | **MLflow + DVC + DagsHub** |
| Real-time | Polling (GET /api/submissions/:id) | **Supabase Realtime subscriptions** |
| Location | PostGIS queries only | **Supabase PostGIS + Radar.io geofencing** |
| Mobile local storage | AsyncStorage | **MMKV (encrypted)** |

---

## Core Value Loop

```
Photo → AI Classification (Groq) → Validator Approval (Realtime) → Token Minting (Clarity) → sBTC Reward
```

---

## Complete Folder Structure

```
satsverdant/
│
├── contracts/
│   ├── waste-tokens.clar          # SIP-010 tokens (plastic, paper, metal, organic, glass)
│   ├── validator-pool.clar        # STX staking + on-chain validation records
│   ├── rewards-pool.clar          # sBTC reward distribution
│   └── carbon-credits.clar        # Carbon offset SIP-010 tokens
│
├── supabase/                       # Replaces entire backend/ from v1.0
│   ├── functions/
│   │   ├── classify/index.ts       # Quality → fraud → Radar.io → Groq → DB write
│   │   ├── mint-tokens/index.ts    # record-validation → mint-waste-token → notify
│   │   ├── claim-reward/index.ts   # verify claimable → claim-rewards → update DB
│   │   └── task-completion-notification/index.ts  # email + Slack + ESG webhooks
│   │
│   ├── migrations/
│   │   ├── 20260301000000_initial_schema.sql
│   │   ├── 20260301000001_rls_policies.sql
│   │   ├── 20260301000002_functions_triggers.sql
│   │   └── 20260301000003_postgis_setup.sql
│   │
│   └── config.toml
│
├── web/
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx                    # Landing page
│       │   └── dashboard/
│       │       ├── layout.tsx              # Sidebar layout
│       │       ├── page.tsx                # Overview
│       │       ├── submit/page.tsx
│       │       ├── rewards/page.tsx
│       │       ├── validate/page.tsx
│       │       ├── impact/page.tsx
│       │       └── settings/page.tsx
│       │
│       ├── components/
│       │   ├── ui/                         # Radix UI primitives
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx             # State via React useState — NOT localStorage
│       │   │   ├── Header.tsx
│       │   │   └── Footer.tsx
│       │   ├── auth/
│       │   │   ├── LoginForm.tsx           # Stacks Connect + Google OAuth buttons
│       │   │   └── WalletConnect.tsx
│       │   ├── submissions/
│       │   │   ├── SubmissionCard.tsx
│       │   │   └── SubmissionTracker.tsx   # Realtime: pending→classified→minted
│       │   ├── validators/
│       │   │   └── ValidatorQueue.tsx      # Realtime queue (auto-updates on new submissions)
│       │   └── rewards/
│       │       └── RewardCard.tsx
│       │
│       ├── contexts/
│       │   └── AuthContext.tsx             # Supabase Auth + Stacks Connect session
│       │
│       ├── lib/
│       │   ├── supabase.ts                 # Supabase client + typed API wrappers (PostgREST)
│       │   └── contracts.ts               # Stacks contract addresses + call helpers
│       │
│       └── hooks/
│           ├── useWallet.ts
│           ├── useSubmissions.ts           # Supabase queries (replaces React Query)
│           └── useSidebar.ts              # React state only — no localStorage
│
├── mobile/
│   └── src/
│       ├── screens/
│       │   ├── HomeScreen.tsx
│       │   ├── CameraScreen.tsx
│       │   ├── DashboardScreen.tsx
│       │   └── RewardsScreen.tsx
│       ├── components/
│       │   ├── WalletButton.tsx
│       │   ├── CameraCapture.tsx
│       │   ├── SubmissionList.tsx
│       │   └── RewardCard.tsx
│       ├── services/
│       │   ├── supabase.ts                # Supabase JS SDK (same project, mobile client)
│       │   ├── camera.ts                  # Expo Camera
│       │   ├── location.ts                # Expo Location + Radar.io pre-check
│       │   └── wallet.ts                  # Stacks Connect Mobile
│       ├── storage/
│       │   └── mmkv.ts                    # MMKV encrypted — offline submission queue
│       │                                   # NOT AsyncStorage (images contain GPS metadata)
│       └── hooks/
│           ├── useCamera.ts
│           ├── useLocation.ts
│           └── useWallet.ts
│
├── ml-training/
│   ├── data/
│   │   ├── raw/               # DVC-tracked: TrashNet, TACO, Kaggle, custom
│   │   ├── processed/         # DVC-tracked: train/val/test splits
│   │   └── active_learning/   # DVC-tracked: monthly validator-approved submissions
│   ├── models/
│   │   ├── waste_classifier.h5       # Groq inference backend
│   │   └── waste_classifier.tflite   # On-device (React Native)
│   ├── metrics/
│   │   ├── train_metrics.json
│   │   ├── eval_metrics.json
│   │   └── confusion_matrix.csv
│   ├── src/
│   │   ├── prepare_data.py    # DVC 'prepare' stage
│   │   ├── train.py           # DVC 'train' stage + MLflow logging to DagsHub
│   │   ├── evaluate.py        # DVC 'evaluate' stage
│   │   ├── active_learning.py
│   │   └── monitor_quality.py # Cohen's kappa + class balance checks
│   ├── params.yaml            # All hyperparameters (DVC-tracked)
│   ├── dvc.yaml               # Pipeline: prepare → train → evaluate
│   └── dvc.lock
│
├── tests/
│   ├── contracts/
│   │   ├── waste-tokens.test.ts
│   │   ├── validator-pool.test.ts
│   │   ├── rewards-pool.test.ts
│   │   └── integration.test.ts
│   └── e2e/
│       └── user-flow.spec.ts   # Playwright: connect → submit → claim
│
├── .github/workflows/
│   ├── supabase-deploy.yml     # Edge Functions + migrations on push to main
│   ├── web-ci.yml              # Next.js build + Vercel
│   ├── mobile-ci.yml           # Expo EAS
│   └── ml-retrain.yml          # Triggered by DVC dataset push to DagsHub
│
├── Clarinet.toml
├── settings/Devnet.toml
├── settings/Testnet.toml
└── README.md
```

---

## Tech Stack

### Smart Contracts
- **Clarity** — `waste-tokens`, `validator-pool`, `rewards-pool`, `carbon-credits`
- **Clarinet** — local dev and testing
- **Deployment:** Testnet → mainnet

### Supabase (replaces all of backend/ from v1.0)
- **PostgreSQL + PostGIS** — primary DB with spatial queries and RLS at DB layer
- **Row Level Security** — access control enforced at database level, not application layer
- **Edge Functions (Deno/TypeScript)** — `/classify`, `/mint-tokens`, `/claim-reward`, `/task-completion-notification`
- **Realtime** — live submission status + validator queue (replaces all polling)
- **Storage** — waste images; IPFS CID recorded in submissions table
- **Auth** — Stacks Connect OAuth + Google OAuth
- **`supabase db push`** — migration management (replaces Alembic)

### Web App
- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** + **Radix UI**
- **Supabase JS SDK** — data fetching, Realtime, Auth (no React Query needed)
- **Stacks.js / Stacks Connect** — wallet
- **Deployment:** Vercel

### Mobile App
- **React Native + Expo** + **TypeScript**
- **React Navigation**
- **Expo Camera** + **Expo Location**
- **MMKV** — encrypted local storage for offline queue (NOT AsyncStorage)
- **Supabase JS SDK** — same Supabase project, mobile client
- **TFLite** — on-device pre-classification
- **Deployment:** Expo EAS

### AI / ML
- **EfficientNetB0** (TensorFlow/Keras) — waste classifier
- **Groq API** — production inference via Edge Function (~50ms)
- **DVC** — dataset versioning + pipeline reproducibility
- **MLflow** — experiment tracking + model registry
- **DagsHub** — hosted MLflow server + DVC remote (free tier) + public experiment URL for grant evidence
- **Google Colab Pro** (A100) — training
- **Radar.io** — geofencing (must be within 100m of registered recycling location)
- **sharp** — image quality grading in Deno Edge Function (Python OpenCV is training-only)

---

## Supabase Database Schema

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- users (references Supabase auth.users)
CREATE TABLE users (
    id             UUID PRIMARY KEY REFERENCES auth.users(id),
    wallet_address TEXT UNIQUE,
    role           TEXT NOT NULL DEFAULT 'recycler'
                   CHECK (role IN ('recycler','validator','admin','org_admin')),
    display_name   TEXT,
    metadata       JSONB DEFAULT '{}',
    created_at     TIMESTAMPTZ DEFAULT now(),
    updated_at     TIMESTAMPTZ DEFAULT now()
);

-- submissions
CREATE TABLE submissions (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Image
  image_storage_path     TEXT,
  image_ipfs_cid         TEXT,
  image_url              TEXT,                          -- public CDN URL
  thumbnail_url          TEXT,                          -- 200px thumbnail

  -- Location (PostGIS)
  latitude               FLOAT,
  longitude              FLOAT,
  location_accuracy      FLOAT,                         -- GPS accuracy in metres
  coordinates            GEOGRAPHY(POINT, 4326)
    GENERATED ALWAYS AS (
      CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL
        THEN ST_MakePoint(longitude, latitude)::GEOGRAPHY
      END
    ) STORED,

  -- AI Classification
  ai_waste_type          TEXT CHECK (ai_waste_type IN ('plastic','paper','metal','organic','glass')),
  ai_confidence          FLOAT,
  ai_estimated_weight_kg FLOAT,                         -- matches Edge Function field name
  ai_quality_grade       CHAR(1) CHECK (ai_quality_grade IN ('A','B','C','D')),
  ai_reasoning           TEXT,                          -- Groq explanation string
  ai_model_version       TEXT,                          -- e.g. groq-llama-3.2-11b-vision-v1

  -- Status workflow
  -- classified    = Groq returned result, fraud_score < 0.5, confidence < 0.7 (awaiting validator)
  -- pending_validation = fraud_score >= 0.5 OR routed to queue
  -- disputed      = validator flagged, needs admin review
  -- failed        = mint transaction failed on-chain
  status                 TEXT NOT NULL DEFAULT 'pending_classification'
                         CHECK (status IN (
                           'pending_classification','classified',
                           'pending_validation','approved','rejected',
                           'minting','minted','failed','disputed'
                         )),

  -- Validation
  validator_id           UUID REFERENCES users(id),
  validation_notes       TEXT,
  validated_at           TIMESTAMPTZ,

  -- Minting
  mint_tx_id             TEXT,
  tokens_minted          INTEGER,
  carbon_offset_g        INTEGER,
  minted_at              TIMESTAMPTZ,

  -- Fraud
  fraud_score            FLOAT DEFAULT 0,
  fraud_flags            JSONB DEFAULT '[]',
  image_hash             TEXT,                          -- perceptual hash for dedup
  duplicate_of           UUID REFERENCES submissions(id),

  -- Meta
  device_info            JSONB DEFAULT '{}',
  created_at             TIMESTAMPTZ DEFAULT now(),
  updated_at             TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_submissions_user       ON submissions(user_id);
CREATE INDEX idx_submissions_status     ON submissions(status);
CREATE INDEX idx_submissions_coordinates ON submissions USING GIST(coordinates);

-- validators
CREATE TABLE validators (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID UNIQUE REFERENCES users(id),
    stx_staked        DECIMAL(18,6) DEFAULT 0,
    reputation_score  INTEGER DEFAULT 100,
    validations_count INTEGER DEFAULT 0,
    accuracy_rate     DECIMAL(5,4) DEFAULT 1.0,
    is_active         BOOLEAN DEFAULT true,
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- rewards
CREATE TABLE rewards (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  submission_id   UUID REFERENCES submissions(id) ON DELETE SET NULL,
  waste_tokens    INTEGER NOT NULL,
  sbtc_amount     FLOAT NOT NULL,
  conversion_rate FLOAT,
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','claimable','claimed','distributed','failed')),
  claim_tx_id     TEXT,
  claimed_at      TIMESTAMPTZ,
  distributed_at  TIMESTAMPTZ,
  metadata        JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- recycling_locations (PostGIS + Radar.io registry)
CREATE TABLE recycling_locations (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT NOT NULL,
    latitude       DECIMAL(10,8),
    longitude      DECIMAL(11,8),
    coordinates    GEOGRAPHY(POINT) GENERATED ALWAYS AS (
                     ST_SetSRID(ST_MakePoint(longitude,latitude),4326)::GEOGRAPHY
                   ) STORED,
    waste_types    TEXT[] NOT NULL,
    radar_fence_id TEXT,
    metadata       JSONB DEFAULT '{}',
    created_at     TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX recycling_locations_coordinates_idx
  ON recycling_locations USING GIST(coordinates);

-- transactions (blockchain audit log)
CREATE TABLE transactions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tx_id         TEXT UNIQUE NOT NULL,
  tx_type       TEXT NOT NULL
                CHECK (tx_type IN ('mint','claim_reward','stake_validator','unstake_validator')),
  entity_type   TEXT NOT NULL,
  entity_id     UUID NOT NULL,
  user_id       UUID REFERENCES users(id),
  status        TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','broadcasted','confirmed','failed','dropped')),
  block_height  INTEGER,
  block_hash    TEXT,
  confirmations INTEGER DEFAULT 0,
  error_code    TEXT,
  error_message TEXT,
  raw_payload   JSONB,
  raw_response  JSONB,
  created_at    TIMESTAMPTZ DEFAULT now()
);
```

### Key Functions and Triggers

```sql
-- PostGIS spatial query: used by /classify to verify submission location
CREATE OR REPLACE FUNCTION nearby_recycling_points(
    user_lat FLOAT, user_lng FLOAT, radius_m FLOAT DEFAULT 100
)
RETURNS TABLE (id UUID, name TEXT, distance_m FLOAT, waste_types TEXT[]) AS $$
    SELECT id, name,
        ST_Distance(coordinates, ST_SetSRID(ST_MakePoint(user_lng,user_lat),4326)::GEOGRAPHY),
        waste_types
    FROM recycling_locations
    WHERE ST_DWithin(coordinates,
        ST_SetSRID(ST_MakePoint(user_lng,user_lat),4326)::GEOGRAPHY, radius_m)
    ORDER BY 3;
$$ LANGUAGE SQL;

-- Auto-create reward row when submission transitions minting → minted.
-- Formula: sbtc_amount = tokens / 10_000_000.0
--   1,000 tokens → 0.0001 sBTC (matches rewards-pool.clar conversion-rate u10000000)
--   Equivalent in sats: tokens * 10 sats per token
--
-- Token formula (in /mint-tokens Edge Function):
--   tokens = floor(ai_estimated_weight_kg * 100 * qualityMultiplier)
--   qualityMultiplier: A=1.0, B=0.8, C=0.6, D=0.4
--
-- Carbon factors (grams CO2 per kg, in /mint-tokens Edge Function):
--   plastic=500, paper=200, metal=1200, organic=100, glass=300
CREATE OR REPLACE FUNCTION create_reward_on_mint()
RETURNS TRIGGER AS $$
DECLARE
  conversion_rate FLOAT := 10000000.0;  -- matches rewards-pool.clar data-var
  sbtc_amt        FLOAT;
BEGIN
  -- Only fire on the minting → minted transition
  IF NEW.status = 'minted' AND OLD.status = 'minting' THEN
    sbtc_amt := NEW.tokens_minted::FLOAT / conversion_rate;

    INSERT INTO rewards (user_id, submission_id, waste_tokens, sbtc_amount,
                         conversion_rate, status)
    VALUES (NEW.user_id, NEW.id, NEW.tokens_minted, sbtc_amt,
            1.0 / conversion_rate, 'claimable');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_reward_on_mint
    AFTER UPDATE ON submissions
    FOR EACH ROW EXECUTE FUNCTION create_reward_on_mint();
```

---

## Row Level Security

```sql
-- Users: own profile only; service role unrestricted
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_user"        ON users FOR ALL    USING (auth.uid() = id);
CREATE POLICY "service_role_u"  ON users FOR ALL    USING (auth.role() = 'service_role');

-- Submissions: recyclers see own; validators see classified + pending_validation queue
-- 'classified' = Groq result returned, fraud_score < 0.5, confidence < 0.7 (needs human)
-- 'pending_validation' = fraud_score >= 0.5, routed to validators
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_submissions" ON submissions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "validators_queue" ON submissions FOR SELECT USING (
    status IN ('pending_validation','classified') AND
    (SELECT role FROM users WHERE id = auth.uid()) = 'validator'
);
CREATE POLICY "validators_update" ON submissions FOR UPDATE USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'validator'
);
CREATE POLICY "service_role_s"  ON submissions FOR ALL USING (auth.role() = 'service_role');

-- Rewards: users see own
ALTER TABLE rewards ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_rewards"     ON rewards FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "service_role_r"  ON rewards FOR ALL    USING (auth.role() = 'service_role');

-- Recycling locations: public read
ALTER TABLE recycling_locations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read"     ON recycling_locations FOR SELECT USING (true);
```

---

## Data Flows (v2.0)

### 1. Photo Submission (no polling — Realtime only)

```
[Mobile App]
    ↓ Capture photo (Expo Camera), get GPS
    ↓ On-device TFLite pre-classify (UI hint only, not authoritative)
    ↓
Upload → Supabase Storage: waste-images/{user_id}/{timestamp}.jpg
    ↓
POST /functions/v1/classify
    ↓
[/classify Edge Function]
    ↓ sharp quality gate → grade A/B/C (continue) or D (reject)
    ↓ Perceptual hash dedup → check submissions.image_hash (30-day window)
    ↓ Radar.io geofence API → verify within 100m of recycling_location
    ↓ Groq API (llama-3.2-11b-vision-preview) → waste_type, confidence, weight_kg, reasoning
    ↓ Fraud score:
        rapid submissions (<10 min since last) → +0.4
        confidence < 0.6                       → +0.3
    ↓ Status routing:
        fraud_score >= 0.5  → status: 'pending_validation' (routed to validators immediately)
        fraud_score < 0.5 AND confidence >= 0.7 → status: 'classified' (may auto-approve)
        fraud_score < 0.5 AND confidence < 0.7  → status: 'classified' (awaiting validator)
    ↓ INSERT into submissions
    ↓
[SubmissionTracker.tsx — Supabase Realtime channel: submission:{id}]
    ↓ Status update pushed instantly to client — zero polling
```

### 2. Validation Flow (Realtime queue)

```
[ValidatorQueue.tsx — Supabase Realtime channels: 'classified' AND 'pending_validation']
    ↓ New row in either status triggers INSERT event → card appears in queue
    ↓ Validator reviews: image + AI result + fraud score + GPS map pin
    ↓ Clicks Approve
    ↓
PATCH submissions/{id} → status: approved, validator_id
    ↓
POST /functions/v1/mint-tokens { submission_id }
    ↓
[/mint-tokens Edge Function]
    ↓ Fetch submission from Supabase
    ↓ Calculate tokens:
        tokens = floor(ai_estimated_weight_kg * 100 * qualityMultiplier)
        qualityMultiplier: A=1.0, B=0.8, C=0.6, D=0.4
    ↓ Calculate carbon_offset_g:
        carbon_offset_g = floor(ai_estimated_weight_kg * carbonFactor[waste_type])
        carbonFactor: plastic=500, paper=200, metal=1200, organic=100, glass=300
    ↓ UPDATE submissions SET status='minting'
    ↓ Call validator-pool.record-validation (on-chain proof + pay 0.1 STX fee)
    ↓ Call waste-tokens.mint-waste-token (Clarity — 5 types: plastic/paper/metal/organic/glass)
    ↓ UPDATE submissions SET status='minted', mint_tx_id, tokens_minted, carbon_offset_g
    ↓ DB trigger fires: create_reward_on_mint → INSERT into rewards (status: claimable)
    ↓ Call /task-completion-notification
    ↓
[SubmissionTracker.tsx Realtime]
    ↓ User sees: "75 PLASTIC tokens minted!" — no refresh needed
```

### 3. Reward Claim Flow

```
[RewardCard.tsx]
    ↓ User clicks "Claim 0.0001 sBTC"
    ↓
POST /functions/v1/claim-reward { reward_id }
    ↓
[/claim-reward Edge Function]
    ↓ Assert rewards.status = 'claimable' (double-spend guard)
    ↓ rewards-pool.claim-rewards (burns waste tokens, transfers sBTC)
    ↓ UPDATE rewards SET status='claimed', claim_tx_id=...
    ↓
[Supabase Realtime subscription on rewards table]
    ↓ RewardCard.tsx updates to "Claimed" instantly
```

---

## Deployment Architecture (v2.0)

```
┌──────────────────┐    ┌──────────────────┐
│  Mobile App      │    │  Web App         │
│  Expo + MMKV     │    │  Next.js (Vercel)│
└────────┬─────────┘    └────────┬─────────┘
         │   Supabase JS SDK     │
         └───────────┬───────────┘
                     │
        ┌────────────▼──────────────────────┐
        │         SUPABASE CLOUD            │
        │  Auth (Stacks Connect + Google)   │
        │  PostgreSQL + PostGIS + RLS        │
        │  Edge Functions (Deno)            │
        │  Realtime (WebSocket)             │
        │  Storage (waste-images bucket)    │
        └──────────────┬────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    Groq API       Radar.io    Stacks Network
    (inference)   (geofence)  (Clarity contracts)
```

---

## CI/CD

```yaml
# .github/workflows/supabase-deploy.yml
name: Supabase Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: supabase/setup-cli@v1
      - run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
      - run: supabase db push
      - run: supabase functions deploy classify
      - run: supabase functions deploy mint-tokens
      - run: supabase functions deploy claim-reward
      - run: supabase functions deploy task-completion-notification
      - run: |
          supabase secrets set GROQ_API_KEY=${{ secrets.GROQ_API_KEY }}
          supabase secrets set RADAR_API_KEY=${{ secrets.RADAR_API_KEY }}
          supabase secrets set STACKS_SERVICE_KEY=${{ secrets.STACKS_SERVICE_KEY }}
```

---

## 12-Week Timeline (v2.0)

### Weeks 1–2: Foundation
- [ ] Supabase project + PostGIS + pg_cron enabled
- [ ] Initial schema migration
- [ ] Clarity contracts deployed to testnet
- [ ] DagsHub repo + DVC initialized + dataset pushed

### Weeks 3–4: Edge Functions
- [ ] /classify with Groq + Radar.io
- [ ] /mint-tokens with Stacks contract calls
- [ ] /claim-reward
- [ ] /task-completion-notification
- [ ] RLS policies tested (no cross-user leaks)

### Weeks 5–6: Web App
- [ ] AuthContext.tsx (Stacks Connect + Google OAuth)
- [ ] SubmissionTracker.tsx (Realtime)
- [ ] ValidatorQueue.tsx (Realtime)
- [ ] All dashboard pages

### Weeks 7–8: ML Training + Mobile
- [ ] EfficientNetB0 on Colab A100 (dvc repro + MLflow)
- [ ] Model registered in MLflow Registry on DagsHub
- [ ] React Native with MMKV offline queue
- [ ] TFLite on-device classification

### Weeks 9–10: Integration + Testing
- [ ] Full E2E: photo → classify → validate → mint → claim
- [ ] Clarinet contract tests all passing
- [ ] Playwright E2E suite

### Weeks 11–12: Polish + Launch
- [ ] 10 true fans beta test
- [ ] 100 concurrent submission load test
- [ ] RLS security audit
- [ ] Stacks mainnet deployment
- [ ] App Store + Play Store submissions

---

## Success Metrics

| Metric | Target |
|---|---|
| Edge Function cold start | < 500ms |
| Classification end-to-end | < 3s |
| Realtime status delivery | < 200ms |
| API response p95 | < 300ms |
| AI classification accuracy | >= 80% |
| Active validators | 3+ |
| On-chain submissions | 100+ |
| Tokens minted | 50+ |

---

*SatsVerdant System Architecture v2.0 — March 2026. Supersedes v1.0 entirely. FastAPI, Redis, Celery, Alembic, Docker, S3, Pinata all replaced by Supabase. AsyncStorage replaced by MMKV. Polling replaced by Supabase Realtime. MLflow + DVC + DagsHub added.*