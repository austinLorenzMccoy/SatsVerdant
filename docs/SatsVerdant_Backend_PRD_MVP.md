# SatsVerdant Backend PRD — MVP v2.0

## 1. Executive Summary

**Project:** SatsVerdant Backend
**Version:** 2.0 (MVP — Revised)
**Timeline:** 12 weeks
**Goal:** Production-ready backend to support waste tokenization, AI classification, validator workflows, and sBTC reward distribution — built entirely on Supabase with zero self-managed infrastructure.

### What Changed from v1.0

| Area | v1.0 | v2.0 |
|---|---|---|
| Core Framework | FastAPI (Python) | Supabase (PostgreSQL + Edge Functions) |
| Auth | JWT + wallet signature | Supabase Auth + Stacks Connect OAuth |
| Database | Self-hosted PostgreSQL + Alembic | Supabase PostgreSQL (managed) |
| Caching / Queue | Redis + Celery | Supabase Realtime + Edge Functions |
| Background Jobs | Celery workers | Supabase Edge Functions + pg_cron |
| File Storage | AWS S3 + Pinata IPFS | Supabase Storage + IPFS pinning |
| Geolocation | Manual PostGIS setup | Supabase built-in PostGIS extension |
| Real-time | WebSocket (custom) | Supabase Realtime subscriptions |
| Security | Manual RBAC middleware | Supabase Row Level Security (RLS) |
| Deployment | Docker Compose + Render | Supabase cloud (fully managed) |
| AI Inference | Self-hosted TF Serving | Groq API via Edge Function |

---

## 2. Product Vision

Build a robust, scalable backend that:
- Accepts waste submissions via photo upload
- Classifies waste using AI/ML via Groq API
- Orchestrates validator approval workflows with real-time updates
- Mints tokens on Stacks blockchain
- Distributes sBTC rewards
- Provides real-time data to frontend and mobile clients

**Core Principle:** Security, auditability, and fraud prevention at every layer — enforced at the database level via RLS, not just the application layer.

---

## 3. System Architecture

```
Client Applications (Web App, React Native, Dashboard)
              |
              | HTTPS
              v
+----------------------------------------------+
|           Supabase Platform                  |
|                                              |
|  +------------+  +------------------------+ |
|  |  Auth      |  |  Auto REST / GraphQL   | |
|  |  (OAuth +  |  |  (auto-generated from  | |
|  |  Stacks)   |  |   PostgreSQL schema)   | |
|  +------------+  +------------------------+ |
|                                              |
|  +------------+  +------------------------+ |
|  | PostgreSQL |  |  Realtime Engine       | |
|  | + PostGIS  |  |  (WebSocket pub/sub)   | |
|  | + RLS      |  +------------------------+ |
|  +------------+                             |
|                                              |
|  +------------------------------------------+ |
|  |         Edge Functions (Deno)            | |
|  |  /classify  /mint  /rewards  /notify     | |
|  +------------------------------------------+ |
|                                              |
|  +------------+                             |
|  |  Storage   |                             |
|  |  (Images)  |                             |
|  +------------+                             |
+----------------------------------------------+
              |
    +---------+---------+
    v                   v
Stacks Blockchain    Groq API
(Clarity contracts)  (AI inference)
```

---

## 4. Supabase Features Implemented

This backend demonstrates all six core Supabase capabilities:

| # | Feature | Where Used |
|---|---|---|
| 1 | Authentication with OAuth | Stacks Connect + Google OAuth via `supabase.auth` |
| 2 | Row Level Security (RLS) | All tables — users see only their own data |
| 3 | Real-time Subscriptions | Live submission status, validator queue updates |
| 4 | Auto-generated REST APIs | Full CRUD on all tables via PostgREST |
| 5 | Database Functions & Triggers | Auto timestamps, validator accuracy, reward calculation |
| 6 | Edge Functions (Serverless) | AI classify, mint tokens, reward notifications |

---

## 5. Database Schema

### 5.1 Enable Extensions

```sql
-- Enable PostGIS (built-in Supabase support -- just enable it)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable pg_cron for scheduled fraud analysis
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Enable uuid generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 5.2 Tables

#### users
```sql
CREATE TABLE users (
  id             UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  wallet_address TEXT UNIQUE,
  display_name   TEXT,
  email          TEXT,
  role           TEXT NOT NULL DEFAULT 'recycler'
                   CHECK (role IN ('recycler', 'validator', 'admin')),
  created_at     TIMESTAMPTZ DEFAULT now(),
  last_seen      TIMESTAMPTZ,
  metadata       JSONB DEFAULT '{}'
);

CREATE INDEX idx_users_wallet ON users(wallet_address);
CREATE INDEX idx_users_role   ON users(role);
```

#### submissions
```sql
CREATE TABLE submissions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Image
  image_storage_path    TEXT,
  image_ipfs_cid        TEXT,
  image_url             TEXT,
  thumbnail_url         TEXT,

  -- Location (PostGIS)
  latitude              FLOAT,
  longitude             FLOAT,
  location_accuracy     FLOAT,
  coordinates           GEOGRAPHY(POINT, 4326)
    GENERATED ALWAYS AS (
      CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL
        THEN ST_MakePoint(longitude, latitude)::GEOGRAPHY
      END
    ) STORED,

  -- AI Classification
  ai_waste_type         TEXT CHECK (ai_waste_type IN ('plastic','paper','metal','organic','glass')),
  ai_confidence         FLOAT,
  ai_estimated_weight_kg FLOAT,
  ai_quality_grade      CHAR(1) CHECK (ai_quality_grade IN ('A','B','C','D')),
  ai_reasoning          TEXT,
  ai_model_version      TEXT,

  -- Status workflow
  status                TEXT NOT NULL DEFAULT 'pending_classification'
                          CHECK (status IN (
                            'pending_classification','classified',
                            'pending_validation','approved','rejected',
                            'minting','minted','failed','disputed'
                          )),

  -- Validation
  validator_id          UUID REFERENCES users(id),
  validated_at          TIMESTAMPTZ,
  validation_notes      TEXT,

  -- Minting
  mint_tx_id            TEXT,
  tokens_minted         INTEGER,
  carbon_offset_g       INTEGER,
  minted_at             TIMESTAMPTZ,

  -- Fraud
  fraud_score           FLOAT DEFAULT 0,
  fraud_flags           JSONB DEFAULT '[]',
  image_hash            TEXT,
  duplicate_of          UUID REFERENCES submissions(id),

  -- Meta
  device_info           JSONB DEFAULT '{}',
  created_at            TIMESTAMPTZ DEFAULT now(),
  updated_at            TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_submissions_user       ON submissions(user_id);
CREATE INDEX idx_submissions_status     ON submissions(status);
CREATE INDEX idx_submissions_validator  ON submissions(validator_id);
CREATE INDEX idx_submissions_created    ON submissions(created_at DESC);
CREATE INDEX idx_submissions_waste_type ON submissions(ai_waste_type);
CREATE INDEX idx_submissions_hash       ON submissions(image_hash);
CREATE INDEX idx_submissions_geo        ON submissions USING GIST(coordinates);
```

#### validators
```sql
CREATE TABLE validators (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  stx_staked        FLOAT NOT NULL DEFAULT 0,
  stake_tx_id       TEXT,
  staked_at         TIMESTAMPTZ,
  reputation_score  INTEGER NOT NULL DEFAULT 100,
  validations_count INTEGER NOT NULL DEFAULT 0,
  approvals_count   INTEGER NOT NULL DEFAULT 0,
  rejections_count  INTEGER NOT NULL DEFAULT 0,
  accuracy_rate     FLOAT,
  is_active         BOOLEAN DEFAULT true,
  suspended_until   TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_validators_user       ON validators(user_id);
CREATE INDEX idx_validators_active     ON validators(is_active);
CREATE INDEX idx_validators_reputation ON validators(reputation_score DESC);
```

#### rewards
```sql
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
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now(),
  metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_rewards_user       ON rewards(user_id);
CREATE INDEX idx_rewards_submission ON rewards(submission_id);
CREATE INDEX idx_rewards_status     ON rewards(status);
CREATE INDEX idx_rewards_claimable  ON rewards(status, user_id) WHERE status = 'claimable';
```

#### recycling_locations
```sql
-- Supabase built-in PostGIS -- enable with CREATE EXTENSION postgis (see 5.1)
CREATE TABLE recycling_locations (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT NOT NULL,
  address        TEXT,
  coordinates    GEOGRAPHY(POINT, 4326) NOT NULL,
  waste_types    TEXT[] DEFAULT '{}',
  radar_fence_id TEXT,
  partner_name   TEXT,
  is_active      BOOLEAN DEFAULT true,
  created_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_recycling_locations_geo ON recycling_locations USING GIST(coordinates);

-- Find recycling points within radius of user
CREATE OR REPLACE FUNCTION nearby_recycling_points(
  user_lat FLOAT, user_lng FLOAT, radius_m INT DEFAULT 100
)
RETURNS TABLE(id UUID, name TEXT, address TEXT, distance_meters FLOAT, waste_types TEXT[]) AS $$
  SELECT id, name, address,
    ST_Distance(coordinates, ST_MakePoint(user_lng, user_lat)::GEOGRAPHY) AS distance_meters,
    waste_types
  FROM recycling_locations
  WHERE ST_DWithin(coordinates, ST_MakePoint(user_lng, user_lat)::GEOGRAPHY, radius_m)
    AND is_active = true
  ORDER BY distance_meters;
$$ LANGUAGE SQL;
```

#### fraud_events
```sql
CREATE TABLE fraud_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
  user_id       UUID REFERENCES users(id),
  fraud_type    TEXT NOT NULL
                  CHECK (fraud_type IN (
                    'duplicate_image','location_clustering',
                    'rapid_submission','low_confidence',
                    'suspicious_device','validator_collusion'
                  )),
  severity      TEXT NOT NULL DEFAULT 'medium'
                  CHECK (severity IN ('low','medium','high','critical')),
  confidence    FLOAT,
  description   TEXT,
  evidence      JSONB DEFAULT '{}',
  action_taken  TEXT,
  resolved      BOOLEAN DEFAULT false,
  resolved_at   TIMESTAMPTZ,
  resolved_by   UUID REFERENCES users(id),
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_fraud_submission  ON fraud_events(submission_id);
CREATE INDEX idx_fraud_user        ON fraud_events(user_id);
CREATE INDEX idx_fraud_type        ON fraud_events(fraud_type);
CREATE INDEX idx_fraud_unresolved  ON fraud_events(resolved) WHERE NOT resolved;
```

#### transactions
```sql
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
  retry_count   INTEGER DEFAULT 0,
  raw_payload   JSONB,
  raw_response  JSONB,
  created_at    TIMESTAMPTZ DEFAULT now(),
  broadcasted_at TIMESTAMPTZ,
  confirmed_at  TIMESTAMPTZ,
  updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tx_id      ON transactions(tx_id);
CREATE INDEX idx_tx_entity  ON transactions(entity_type, entity_id);
CREATE INDEX idx_tx_status  ON transactions(status);
CREATE INDEX idx_tx_user    ON transactions(user_id);
```

---

## 6. Supabase Feature 5: Database Functions & Triggers

All data integrity logic lives in the database — not the application layer.

```sql
-- ── Auto-update updated_at ────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_submissions_updated_at
  BEFORE UPDATE ON submissions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_validators_updated_at
  BEFORE UPDATE ON validators
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rewards_updated_at
  BEFORE UPDATE ON rewards
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at
  BEFORE UPDATE ON transactions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── Auto-calculate validator accuracy ────────────────────────
CREATE OR REPLACE FUNCTION calculate_validator_accuracy()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.validations_count > 0 THEN
    NEW.accuracy_rate = NEW.approvals_count::FLOAT / NEW.validations_count::FLOAT;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_validator_accuracy
  BEFORE UPDATE ON validators
  FOR EACH ROW EXECUTE FUNCTION calculate_validator_accuracy();

-- ── Auto-create user profile on signup ───────────────────────
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, display_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ── Auto-create reward when submission is minted ─────────────
CREATE OR REPLACE FUNCTION create_reward_on_mint()
RETURNS TRIGGER AS $$
DECLARE
  -- Matches rewards-pool.clar (define-data-var conversion-rate uint u10000000)
  -- Formula: sbtc = tokens / 10_000_000  =>  1,000 tokens = 0.0001 sBTC
  -- In sats:  tokens * 10 sats per token  =>  1,000 tokens = 10,000 sats = 0.0001 sBTC
  conversion_rate  FLOAT := 10000000.0;
  sbtc_amt         FLOAT;
BEGIN
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

CREATE TRIGGER trigger_create_reward
  AFTER UPDATE ON submissions
  FOR EACH ROW EXECUTE FUNCTION create_reward_on_mint();

-- ── Scheduled fraud analysis (pg_cron, every 6 hours) ────────
SELECT cron.schedule(
  'fraud-analysis',
  '0 */6 * * *',
  $$ SELECT run_periodic_fraud_analysis() $$
);
```

---

## 7. Supabase Feature 2: Row Level Security (RLS)

Security is enforced at the database level. Users cannot read or write other users' data even if they call the API directly.

```sql
-- Enable RLS on all tables
ALTER TABLE users        ENABLE ROW LEVEL SECURITY;
ALTER TABLE submissions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE rewards      ENABLE ROW LEVEL SECURITY;
ALTER TABLE validators   ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- ── users ─────────────────────────────────────────────────────
CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Admins can view all users"
  ON users FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
  ));

-- ── submissions ───────────────────────────────────────────────
CREATE POLICY "Users can view own submissions"
  ON submissions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create submissions"
  ON submissions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Validators can view pending submissions"
  ON submissions FOR SELECT
  USING (
    status = 'pending_validation'
    AND EXISTS (
      SELECT 1 FROM validators v
      JOIN users u ON u.id = v.user_id
      WHERE u.id = auth.uid() AND v.is_active = true
    )
  );

CREATE POLICY "Validators can update submissions they review"
  ON submissions FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM validators v
      JOIN users u ON u.id = v.user_id
      WHERE u.id = auth.uid() AND v.is_active = true
    )
    AND status IN ('pending_validation', 'classified')
  );

CREATE POLICY "Service role has full access"
  ON submissions FOR ALL
  USING (auth.role() = 'service_role');

-- ── rewards ───────────────────────────────────────────────────
CREATE POLICY "Users can view own rewards"
  ON rewards FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service role manages rewards"
  ON rewards FOR ALL
  USING (auth.role() = 'service_role');

-- ── validators ────────────────────────────────────────────────
CREATE POLICY "Validators are publicly viewable"
  ON validators FOR SELECT
  USING (true);

CREATE POLICY "Validators manage own record"
  ON validators FOR UPDATE
  USING (auth.uid() = user_id);

-- ── recycling_locations ───────────────────────────────────────
CREATE POLICY "Recycling locations are public"
  ON recycling_locations FOR SELECT
  USING (is_active = true);

CREATE POLICY "Admins manage recycling locations"
  ON recycling_locations FOR ALL
  USING (EXISTS (
    SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
  ));
```

---

## 8. Supabase Feature 1: Authentication with OAuth

### 8.1 Stacks Connect + Supabase Auth

```typescript
// src/contexts/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { AppConfig, UserSession, showConnect } from '@stacks/connect';
import { StacksMainnet } from '@stacks/network';

const appConfig = new AppConfig(['store_write', 'publish_data']);

interface AuthContextType {
  user:        any | null;
  stacksUser:  UserSession | null;
  signInWithStacks: () => void;
  signInWithGoogle: () => void;
  signOut:     () => Promise<void>;
  loading:     boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user,       setUser]       = useState<any | null>(null);
  const [stacksUser, setStacksUser] = useState<UserSession | null>(null);
  const [loading,    setLoading]    = useState(true);

  useEffect(() => {
    // Listen for Supabase auth changes (Feature 1: Real-time auth state)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );
    return () => subscription.unsubscribe();
  }, []);

  // Stacks wallet authentication
  const signInWithStacks = () => {
    showConnect({
      appDetails: { name: 'SatsVerdant', icon: '/logo.svg' },
      redirectTo: '/',
      onFinish: async ({ userSession }) => {
        setStacksUser(userSession);
        const walletAddress = userSession.loadUserData().profile.stxAddress.mainnet;

        // Exchange Stacks identity for Supabase session
        const { data, error } = await supabase.functions.invoke('auth-stacks', {
          body: { walletAddress, userData: userSession.loadUserData() }
        });

        if (data?.token) {
          await supabase.auth.setSession({ access_token: data.token, refresh_token: data.refresh });
        }
      },
      userSession: new UserSession({ appConfig }),
      network: new StacksMainnet()
    });
  };

  // Google OAuth (Supabase native)
  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` }
    });
  };

  const signOut = async () => {
    setStacksUser(null);
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ user, stacksUser, signInWithStacks, signInWithGoogle, signOut, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
```

### 8.2 Login Component

```typescript
// src/components/LoginForm.tsx
import { useAuth } from '../contexts/AuthContext';

export function LoginForm() {
  const { signInWithStacks, signInWithGoogle, loading } = useAuth();

  return (
    <div className="flex flex-col gap-4 p-8 max-w-sm mx-auto">
      <h1 className="text-2xl font-bold text-center">Sign in to SatsVerdant</h1>

      <button
        onClick={signInWithStacks}
        disabled={loading}
        className="flex items-center gap-3 px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
      >
        <img src="/stacks-logo.svg" alt="Stacks" className="w-5 h-5" />
        Connect Stacks Wallet
      </button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">or</span>
        </div>
      </div>

      <button
        onClick={signInWithGoogle}
        disabled={loading}
        className="flex items-center gap-3 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
      >
        <img src="/google-logo.svg" alt="Google" className="w-5 h-5" />
        Continue with Google
      </button>
    </div>
  );
}
```

---

## 9. Supabase Feature 4: Auto-generated REST APIs

No backend routing code needed. Supabase generates a full REST API automatically from the PostgreSQL schema via PostgREST.

```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// ── Submissions ───────────────────────────────────────────────
export const submissionsApi = {
  // GET /rest/v1/submissions (auto-generated, filtered by RLS)
  list: (filters?: { status?: string; waste_type?: string }) =>
    supabase.from('submissions')
      .select(`
        id, status, ai_waste_type, ai_confidence, ai_quality_grade,
        ai_estimated_weight_kg, tokens_minted, image_url, thumbnail_url,
        created_at, minted_at, fraud_score
      `)
      .match(filters ?? {})
      .order('created_at', { ascending: false }),

  // GET /rest/v1/submissions?id=eq.{id}
  get: (id: string) =>
    supabase.from('submissions')
      .select(`
        *, validator:validator_id(id, wallet_address, reputation_score)
      `)
      .eq('id', id)
      .single(),

  // POST /rest/v1/submissions
  create: (data: Partial<Submission>) =>
    supabase.from('submissions').insert(data).select().single(),

  // PATCH /rest/v1/submissions?id=eq.{id}
  update: (id: string, data: Partial<Submission>) =>
    supabase.from('submissions').update(data).eq('id', id).select().single(),
};

// ── Rewards ───────────────────────────────────────────────────
export const rewardsApi = {
  list: (status?: string) =>
    supabase.from('rewards')
      .select('*, submission:submission_id(ai_waste_type, image_url)')
      .match(status ? { status } : {})
      .order('created_at', { ascending: false }),

  summary: () =>
    supabase.rpc('get_rewards_summary'),
};

// ── Validators ────────────────────────────────────────────────
export const validatorsApi = {
  leaderboard: () =>
    supabase.from('validators')
      .select('*, user:user_id(wallet_address, display_name)')
      .eq('is_active', true)
      .order('reputation_score', { ascending: false })
      .limit(50),

  getQueue: () =>
    supabase.from('submissions')
      .select(`
        id, image_url, ai_waste_type, ai_confidence, ai_quality_grade,
        fraud_score, fraud_flags, created_at,
        user:user_id(wallet_address, metadata)
      `)
      .eq('status', 'pending_validation')
      .order('created_at', { ascending: true }),
};

// ── Stats ─────────────────────────────────────────────────────
export const statsApi = {
  global: () => supabase.rpc('get_global_stats'),
  user:   (walletAddress: string) => supabase.rpc('get_user_stats', { wallet: walletAddress }),
};
```

---

## 10. Supabase Feature 3: Real-time Subscriptions

No polling. All clients receive live updates via WebSocket.

```typescript
// src/components/SubmissionTracker.tsx
import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { RealtimePostgresChangesPayload } from '@supabase/supabase-js';

const STATUS_LABELS: Record<string, string> = {
  pending_classification: 'Uploading...',
  classified:             'AI classified ✓',
  pending_validation:     'Awaiting validator...',
  approved:               'Approved ✓',
  minting:                'Minting token...',
  minted:                 'Token minted! Reward ready ✓',
  rejected:               'Rejected',
  failed:                 'Failed — please resubmit',
};

export function SubmissionTracker({ submissionId }: { submissionId: string }) {
  const [submission, setSubmission] = useState<any>(null);

  useEffect(() => {
    // Initial fetch
    supabase.from('submissions').select('*').eq('id', submissionId).single()
      .then(({ data }) => setSubmission(data));

    // Feature 3: Real-time subscription — live status updates
    const channel = supabase
      .channel(`submission:${submissionId}`)
      .on(
        'postgres_changes',
        {
          event:  'UPDATE',
          schema: 'public',
          table:  'submissions',
          filter: `id=eq.${submissionId}`
        },
        (payload: RealtimePostgresChangesPayload<any>) => {
          setSubmission(payload.new);
        }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [submissionId]);

  if (!submission) return <div>Loading...</div>;

  return (
    <div className="p-6 rounded-xl border">
      <h3 className="font-semibold text-lg mb-2">Submission Status</h3>
      <div className="flex items-center gap-2">
        <span className={`px-3 py-1 rounded-full text-sm font-medium
          ${submission.status === 'minted' ? 'bg-green-100 text-green-800' :
            submission.status === 'rejected' ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'}`}>
          {STATUS_LABELS[submission.status] ?? submission.status}
        </span>
      </div>
      {submission.tokens_minted && (
        <p className="mt-3 text-green-600 font-medium">
          +{submission.tokens_minted} waste tokens earned!
        </p>
      )}
    </div>
  );
}

// ── Validator Queue (real-time for validators) ─────────────────
export function ValidatorQueue() {
  const [queue, setQueue] = useState<any[]>([]);

  useEffect(() => {
    // Initial load
    supabase.from('submissions')
      .select('id, image_url, ai_waste_type, ai_confidence, fraud_score, created_at')
      .eq('status', 'pending_validation')
      .then(({ data }) => setQueue(data ?? []));

    // Feature 3: Live validator queue updates
    const channel = supabase
      .channel('validator-queue')
      .on('postgres_changes', {
        event:  '*',
        schema: 'public',
        table:  'submissions',
        filter: "status=eq.pending_validation"
      }, (payload) => {
        if (payload.eventType === 'INSERT') {
          setQueue(prev => [payload.new, ...prev]);
        } else if (payload.eventType === 'UPDATE') {
          setQueue(prev => prev.filter(s => s.id !== payload.old.id));
        }
      })
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">
        Validation Queue ({queue.length} pending)
      </h2>
      {queue.map(sub => (
        <SubmissionCard key={sub.id} submission={sub} />
      ))}
    </div>
  );
}
```

---

## 11. Supabase Feature 6: Edge Functions

All serverless logic runs in Deno-based Edge Functions — no server management.

### 11.1 `/classify` — AI Classification Pipeline

```typescript
// supabase/functions/classify/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GROQ_API_KEY  = Deno.env.get("GROQ_API_KEY")!;
const RADAR_API_KEY = Deno.env.get("RADAR_API_KEY")!;
const SUPABASE_URL  = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_KEY  = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

serve(async (req) => {
  const { imageBase64, userId, latitude, longitude, deviceInfo } = await req.json();

  try {
    // 1. Quality gate
    const quality = await checkImageQuality(imageBase64);
    if (quality.grade === "D") {
      return json({ success: false, reason: "Image quality too low." }, 400);
    }

    // 2. Duplicate detection
    const imageHash   = await computeHash(imageBase64);
    const isDuplicate = await checkDuplicate(userId, imageHash);
    if (isDuplicate) {
      return json({ success: false, reason: "Duplicate submission." }, 409);
    }

    // 3. Radar.io geofence check
    if (latitude && longitude) {
      const geo = await verifyLocation(latitude, longitude);
      if (!geo.isAtRecyclingPoint) {
        return json({
          success: false, reason: "Must be at a registered recycling location.",
          nearestLocation: geo.nearestLocation
        }, 403);
      }
    }

    // 4. Groq AI classification
    const classification = await classifyWithGroq(imageBase64);

    // 5. Fraud score
    const fraudScore = await getFraudScore(userId, classification.confidence);

    // 6. Persist to Supabase (RLS: service role bypasses for server-side ops)
    const { data: submission } = await supabase
      .from("submissions")
      .insert({
        user_id:               userId,
        ai_waste_type:         classification.wasteType,
        ai_confidence:         classification.confidence,
        ai_quality_grade:      quality.grade,
        ai_reasoning:          classification.reasoning,
        ai_model_version:      "groq-llama-3.2-11b-vision-v1",
        image_hash:            imageHash,
        latitude, longitude,
        fraud_score:           fraudScore,
        status:                fraudScore > 0.5 ? "pending_validation" : "classified",
        device_info:           deviceInfo
      })
      .select()
      .single();

    // 7. Trigger notification Edge Function if reward-ready
    if (submission.status === "classified" && classification.confidence >= 0.7) {
      await supabase.functions.invoke("task-completion-notification", {
        body: { type: "classified", submissionId: submission.id, userId }
      });
    }

    return json({ success: true, submissionId: submission.id, ...classification, status: submission.status });

  } catch (err) {
    return json({ success: false, error: err.message }, 500);
  }
});

async function classifyWithGroq(imageBase64: string) {
  const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { "Authorization": `Bearer ${GROQ_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "llama-3.2-11b-vision-preview",
      messages: [{
        role: "user",
        content: [
          { type: "image_url", image_url: { url: `data:image/jpeg;base64,${imageBase64}` } },
          { type: "text", text: `Classify this waste. Respond ONLY in JSON:
{ "wasteType": "<plastic|paper|metal|organic|glass>", "confidence": <0-1>, "reasoning": "<one sentence>" }` }
        ]
      }],
      max_tokens: 150, temperature: 0.1
    })
  });
  const data = await res.json();
  return JSON.parse(data.choices[0].message.content.replace(/```json|```/g, "").trim());
}

async function verifyLocation(lat: number, lng: number) {
  const res   = await fetch(
    `https://api.radar.io/v1/geofences/nearby?coordinates=${lat},${lng}&radius=100`,
    { headers: { "Authorization": RADAR_API_KEY } }
  );
  const data  = await res.json();
  const fences = (data.geofences ?? []).filter((f: any) => f.tag === "recycling_point");
  return { isAtRecyclingPoint: fences.length > 0, nearestLocation: fences[0]?.description ?? null };
}

async function computeHash(imageBase64: string): Promise<string> {
  const bytes = Uint8Array.from(atob(imageBase64), c => c.charCodeAt(0));
  const hash  = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2,"0")).join("").slice(0,16);
}

async function checkDuplicate(userId: string, hash: string): Promise<boolean> {
  const { data } = await supabase
    .from("submissions").select("id").eq("user_id", userId).eq("image_hash", hash)
    .gte("created_at", new Date(Date.now() - 30*24*60*60*1000).toISOString()).limit(1);
  return (data?.length ?? 0) > 0;
}

async function getFraudScore(userId: string, confidence: number): Promise<number> {
  const { count } = await supabase
    .from("submissions").select("*", { count: "exact", head: true }).eq("user_id", userId)
    .gte("created_at", new Date(Date.now() - 60*60*1000).toISOString());
  let score = 0;
  if ((count ?? 0) >= 5) score += 0.4;
  if (confidence < 0.6)  score += 0.3;
  return Math.min(score, 1.0);
}

async function checkImageQuality(imageBase64: string) {
  // Basic quality check via image metadata (full OpenCV check runs server-side)
  const bytes = Uint8Array.from(atob(imageBase64), c => c.charCodeAt(0));
  if (bytes.length < 5000) return { grade: "D" };
  return { grade: "B" }; // Default — full quality grading in AI PRD
}

function json(data: object, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
}
```

### 11.2 `/mint-tokens` — Stacks Blockchain Minting

```typescript
// supabase/functions/mint-tokens/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
);

const STACKS_API     = "https://stacks-node-api.mainnet.stacks.co";
const CONTRACT_ADDR  = Deno.env.get("STACKS_CONTRACT_ADDRESS")!;
const SERVICE_KEY    = Deno.env.get("STACKS_SERVICE_ACCOUNT_KEY")!;

serve(async (req) => {
  const { submissionId, validatorId } = await req.json();

  const { data: submission } = await supabase
    .from("submissions").select("*").eq("id", submissionId).single();

  if (!submission || submission.status !== "approved") {
    return json({ success: false, reason: "Submission not approved" }, 400);
  }

  // Calculate tokens
  const qualityMultipliers: Record<string, number> = { A: 1.0, B: 0.8, C: 0.6, D: 0.4 };
  const tokens = Math.floor(
    (submission.ai_estimated_weight_kg ?? 1.0) * 100
    * (qualityMultipliers[submission.ai_quality_grade] ?? 0.8)
  );

  // Carbon offset
  const carbonFactors: Record<string, number> = { plastic: 500, paper: 200, metal: 1200, organic: 100, glass: 300 };
  const carbonOffsetG = Math.floor(
    (submission.ai_estimated_weight_kg ?? 1.0) * (carbonFactors[submission.ai_waste_type] ?? 200)
  );

  // Update status to minting
  await supabase.from("submissions").update({ status: "minting", tokens_minted: tokens, carbon_offset_g: carbonOffsetG })
    .eq("id", submissionId);

  // Broadcast to Stacks (simplified — uses Hiro API)
  const txResponse = await fetch(`${STACKS_API}/v2/transactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      // Contract call to waste-tokens.mint-waste-token
      contract_address: CONTRACT_ADDR,
      function_name: "mint-waste-token",
      function_args: [submission.ai_waste_type, tokens, submission.user_id],
      sender_key: SERVICE_KEY
    })
  });

  const txData = await txResponse.json();

  // Log transaction
  await supabase.from("transactions").insert({
    tx_id:       txData.txid,
    tx_type:     "mint",
    entity_type: "submission",
    entity_id:   submissionId,
    user_id:     submission.user_id,
    status:      "broadcasted",
    raw_response: txData
  });

  // Update submission with tx_id
  await supabase.from("submissions").update({
    status: "minting", mint_tx_id: txData.txid
  }).eq("id", submissionId);

  // Notify user
  await supabase.functions.invoke("task-completion-notification", {
    body: { type: "minting", submissionId, userId: submission.user_id, txId: txData.txid }
  });

  return json({ success: true, txId: txData.txid, tokens, carbonOffsetG });
});

function json(data: object, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
}
```

### 11.3 `/task-completion-notification` — Notifications (Feature 6)

```typescript
// supabase/functions/task-completion-notification/index.ts
// Feature 6: Edge Functions for external integrations
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabase    = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const SLACK_URL   = Deno.env.get("SLACK_WEBHOOK_URL");
const EMAIL_KEY   = Deno.env.get("RESEND_API_KEY");

serve(async (req) => {
  const { type, submissionId, userId, txId } = await req.json();

  const { data: user } = await supabase
    .from("users").select("email, display_name, wallet_address").eq("id", userId).single();

  const messages: Record<string, { title: string; body: string }> = {
    classified:  { title: "Waste classified!", body: "Your submission has been classified. Awaiting validator approval." },
    approved:    { title: "Submission approved!", body: "Your waste has been verified. Token minting in progress." },
    minting:     { title: "Token minted!", body: `Your sBTC reward is now claimable. Tx: ${txId}` },
    reward_ready:{ title: "Reward ready to claim!", body: "You have a new sBTC reward available to claim." },
  };

  const msg = messages[type];
  if (!msg) return new Response("Unknown type", { status: 400 });

  // Email notification via Resend
  if (user?.email && EMAIL_KEY) {
    await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { "Authorization": `Bearer ${EMAIL_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        from: "SatsVerdant <no-reply@satsverdant.com>",
        to:   user.email,
        subject: msg.title,
        html: `<p>Hi ${user.display_name ?? "recycler"},</p><p>${msg.body}</p>`
      })
    });
  }

  // Slack admin notification (for minting events)
  if (SLACK_URL && type === "minting") {
    await fetch(SLACK_URL, {
      method: "POST",
      body: JSON.stringify({
        text: `Token minted for ${user?.wallet_address ?? userId} | Submission: ${submissionId} | Tx: ${txId}`
      })
    });
  }

  // Webhook (for enterprise ESG dashboard integrations)
  const { data: webhooks } = await supabase
    .from("webhooks").select("url").eq("event_type", type);

  for (const webhook of webhooks ?? []) {
    await fetch(webhook.url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event: type, submissionId, userId, timestamp: new Date().toISOString() })
    });
  }

  return new Response(JSON.stringify({ sent: true }), { status: 200 });
});
```

### 11.4 `/claim-reward` — sBTC Reward Distribution

```typescript
// supabase/functions/claim-reward/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabase   = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const STACKS_API = "https://stacks-node-api.mainnet.stacks.co";

serve(async (req) => {
  const { rewardId, userId } = await req.json();

  const { data: reward } = await supabase
    .from("rewards").select("*").eq("id", rewardId).eq("user_id", userId)
    .eq("status", "claimable").single();

  if (!reward) return json({ success: false, reason: "Reward not claimable" }, 400);

  // Mark as processing
  await supabase.from("rewards").update({ status: "claimed" }).eq("id", rewardId);

  // Call rewards.clar contract to distribute sBTC
  const txResponse = await fetch(`${STACKS_API}/v2/transactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contract_address: Deno.env.get("STACKS_CONTRACT_ADDRESS"),
      function_name: "claim-reward",
      function_args: [reward.waste_tokens, userId],
      sender_key: Deno.env.get("STACKS_SERVICE_ACCOUNT_KEY")
    })
  });

  const txData = await txResponse.json();

  // Log transaction and update reward
  await supabase.from("transactions").insert({
    tx_id: txData.txid, tx_type: "claim_reward",
    entity_type: "reward", entity_id: rewardId,
    user_id: userId, status: "broadcasted"
  });

  await supabase.from("rewards").update({
    claim_tx_id: txData.txid, claimed_at: new Date().toISOString()
  }).eq("id", rewardId);

  return json({ success: true, txId: txData.txid, sbtcAmount: reward.sbtc_amount });
});

function json(data: object, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
}
```

---

## 12. File Storage

```typescript
// src/lib/storage.ts
import { supabase } from './supabase';

export async function uploadWasteImage(
  file: File, userId: string
): Promise<{ path: string; url: string; base64: string }> {

  const ext  = file.name.split('.').pop();
  const path = `submissions/${userId}/${Date.now()}.${ext}`;

  // Upload to Supabase Storage
  const { error } = await supabase.storage
    .from('waste-images')
    .upload(path, file, { contentType: file.type, upsert: false });

  if (error) throw error;

  const { data: { publicUrl } } = supabase.storage
    .from('waste-images').getPublicUrl(path);

  // Convert to base64 for Edge Function classification
  const base64 = await fileToBase64(file);

  return { path, url: publicUrl, base64 };
}

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload  = () => resolve((reader.result as string).split(',')[1]);
    reader.onerror = reject;
  });
}

// Storage bucket policy (set in Supabase dashboard)
// CREATE POLICY "Users can upload own images"
//   ON storage.objects FOR INSERT
//   WITH CHECK (auth.uid()::text = (storage.foldername(name))[2]);
```

---

## 13. Environment Variables

```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...

# Supabase Edge Function secrets (set via Supabase CLI)
# supabase secrets set GROQ_API_KEY=gsk_...
GROQ_API_KEY=gsk_...
RADAR_API_KEY=prj_live_...
STACKS_CONTRACT_ADDRESS=SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7
STACKS_SERVICE_ACCOUNT_KEY=<stored in Supabase Vault, not .env>
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
RESEND_API_KEY=re_...
```

---

## 14. Deployment

### Supabase CLI Deployment

```bash
# Install Supabase CLI
npm install -g supabase

# Link to your project
supabase link --project-ref your-project-ref

# Push database schema
supabase db push

# Deploy all Edge Functions
supabase functions deploy classify
supabase functions deploy mint-tokens
supabase functions deploy task-completion-notification
supabase functions deploy claim-reward

# Set secrets
supabase secrets set GROQ_API_KEY=gsk_...
supabase secrets set RADAR_API_KEY=prj_live_...
supabase secrets set STACKS_SERVICE_ACCOUNT_KEY=...
supabase secrets set SLACK_WEBHOOK_URL=...
supabase secrets set RESEND_API_KEY=...
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Supabase

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Supabase CLI
        uses: supabase/setup-cli@v1
        with:
          version: latest

      - name: Link project
        run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      - name: Push database migrations
        run: supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      - name: Deploy Edge Functions
        run: |
          supabase functions deploy classify
          supabase functions deploy mint-tokens
          supabase functions deploy task-completion-notification
          supabase functions deploy claim-reward
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

---

## 15. Security

### Input Validation (Edge Function layer)

```typescript
// Shared validation in Edge Functions
function validateSubmissionInput(body: any): { valid: boolean; error?: string } {
  if (!body.imageBase64 || typeof body.imageBase64 !== 'string') {
    return { valid: false, error: "imageBase64 required" };
  }
  if (body.imageBase64.length > 15 * 1024 * 1024) { // ~10MB base64
    return { valid: false, error: "Image too large (max 10MB)" };
  }
  if (body.latitude !== undefined && (body.latitude < -90 || body.latitude > 90)) {
    return { valid: false, error: "Invalid latitude" };
  }
  if (body.longitude !== undefined && (body.longitude < -180 || body.longitude > 180)) {
    return { valid: false, error: "Invalid longitude" };
  }
  return { valid: true };
}
```

### Rate Limiting (Supabase + PostgreSQL)

```sql
-- Rate limit tracking table
CREATE TABLE rate_limits (
  user_id    UUID REFERENCES users(id),
  action     TEXT,
  count      INTEGER DEFAULT 1,
  window_end TIMESTAMPTZ DEFAULT now() + INTERVAL '1 day',
  PRIMARY KEY (user_id, action)
);

-- Rate limit check function
CREATE OR REPLACE FUNCTION check_rate_limit(
  p_user_id UUID, p_action TEXT, p_max INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE v_count INTEGER;
BEGIN
  INSERT INTO rate_limits (user_id, action, count, window_end)
  VALUES (p_user_id, p_action, 1, now() + INTERVAL '1 day')
  ON CONFLICT (user_id, action) DO UPDATE
    SET count = CASE
      WHEN rate_limits.window_end < now()
        THEN 1
      ELSE rate_limits.count + 1
    END,
    window_end = CASE
      WHEN rate_limits.window_end < now()
        THEN now() + INTERVAL '1 day'
      ELSE rate_limits.window_end
    END
  RETURNING count INTO v_count;

  RETURN v_count <= p_max;
END;
$$ LANGUAGE plpgsql;

-- Usage in Edge Function: SELECT check_rate_limit(userId, 'submission', 5);
```

---

## 16. MVP Acceptance Criteria

### Core Functionality
- [ ] User can sign in via Stacks Connect or Google OAuth (Feature 1)
- [ ] Users only see their own data — RLS enforced (Feature 2)
- [ ] Submission status updates in real-time without refresh (Feature 3)
- [ ] Full CRUD via auto-generated REST API (Feature 4)
- [ ] Auto-timestamps and validator accuracy auto-calculated (Feature 5)
- [ ] classify, mint-tokens, and notification Edge Functions live (Feature 6)
- [ ] AI classifies waste with >80% accuracy via Groq
- [ ] Image stored in Supabase Storage + IPFS CID recorded
- [ ] Validator can approve/reject from real-time queue
- [ ] Tokens minted on Stacks testnet
- [ ] User can claim sBTC rewards
- [ ] PostGIS nearby_recycling_points function works with Radar.io

### Performance
- [ ] Edge Function cold start < 500ms
- [ ] Classification end-to-end < 3 seconds
- [ ] Real-time update delivery < 200ms
- [ ] API response time < 300ms (p95, PostgREST auto-API)

### Security
- [ ] RLS tested — no cross-user data access possible
- [ ] No secrets in codebase or frontend bundle
- [ ] Rate limiting active (5 submissions/day)
- [ ] Input validation on all Edge Functions

---

## 17. Post-MVP Roadmap

### Phase 2 (Weeks 13-20)
- Supabase Realtime broadcast channels for global stats dashboard
- Governance voting endpoints
- Carbon credit marketplace API
- Mobile push notifications via Supabase + Expo

### Phase 3 (Weeks 21-32)
- Supabase Vector (pgvector) for semantic waste search
- Advanced analytics via Supabase SQL editor
- Multi-language support
- Enterprise ESG webhook integrations

---

*SatsVerdant Backend PRD v2.0 — March 2026. Supersedes v1.0 in all sections.*