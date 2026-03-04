# SatsVerdant — Post-MVP Roadmap & Future Improvements

**Document Version:** 2.0
**Baseline:** MVP v2.1 (Supabase + Groq + MLflow + DVC + DagsHub)
**Timeline Start:** Week 13 (post-grant delivery)

> Every improvement listed here builds on the v2.1 architecture — Supabase Edge Functions, MLflow Model Registry, DVC pipelines, Groq inference, Radar.io geofencing, and Clarity smart contracts. Nothing here requires replacing what was built in the MVP grant period.

---

## Phase 2 — Core Expansion (Weeks 13–20)

### 2.1 AI/ML: Extended Waste Classification

**Current state (MVP v2.1):** EfficientNetB0 classifies 5 waste types (plastic, paper, metal, organic, glass) at >=80% accuracy. Trained on 26,000 images. Versioned with DVC, tracked in MLflow on DagsHub, deployed via Groq API.

#### Electronic Waste Classification

The MVP excluded e-waste due to insufficient training data. Phase 2 targets a minimum 3,000-image e-waste dataset from iNaturalist, partner recycling centers, and community submissions. A new DVC stage (`data/raw/ewaste/`) is added to the existing `dvc.yaml` pipeline. EfficientNetB0 is retrained as a 6-class classifier and the new version is registered in the MLflow Model Registry on DagsHub under `satsverdant-waste-classifier v3+`. Promotion to Staging requires >=75% e-waste recall on the holdout set.

#### Multi-Label Classification

Some real-world submissions contain mixed waste (a cardboard box with plastic packaging, for example). Phase 2 adds a secondary sigmoid output head alongside the existing softmax classifier, enabling multiple waste-type labels per submission. MLflow experiments track single-label and multi-label variants as separate named runs within the `waste-classifier-efficientnetb0` experiment so both can be compared side by side on DagsHub.

#### Confidence Calibration

The current 0.7 auto-approval threshold is a fixed heuristic. Phase 2 applies temperature scaling (post-hoc calibration) to align raw model confidence with empirical accuracy on the held-out test set. Calibration curves are logged as MLflow artifacts after every retraining run, providing the grant committee and team with a visual audit trail of model reliability across versions.

#### Active Learning Pipeline

Validator-approved submissions are already stored in Supabase. Phase 2 builds a monthly retraining trigger: a `pg_cron` job queries `submissions WHERE status = 'approved' AND created_at > last_retrain_date`, exports images to a DVC-tracked `data/raw/active_learning/` directory, commits a new dataset version, and queues a Colab A100 training run. Because every MLflow run logs the `dataset_dvc_commit` parameter, each registered model is permanently linked to the exact data that produced it.

#### A/B Model Testing in Groq Inference

The `/classify` Edge Function currently calls a single `Production`-stage model from the MLflow Registry. Phase 2 routes 10% of live traffic to the `Staging` model while 90% uses `Production`. Results are logged to a new `ab_test_results` Supabase table. A model is promoted from Staging to Production only after 7 days of A/B data showing >=1% accuracy improvement with no regression in the fraud false-positive rate.

---

### 2.2 Mobile Application

**Current state (MVP v2.1):** React Native app with TFLite on-device classification and Supabase Realtime status updates.

#### Offline Submission Queue

When the user has no network connection, submissions are saved locally using React Native MMKV (encrypted key-value storage). On reconnect, a background sync task uploads queued images to Supabase Storage in order and then calls `/classify` for each. MMKV is used instead of AsyncStorage because images may contain embedded GPS metadata that requires encryption at rest. The queue displays a per-item pending/syncing/done indicator.

#### Push Notifications via Expo

Supabase Realtime already fires events on submission status changes. Phase 2 pipes these through the Expo Push Notification Service. The `task-completion-notification` Edge Function (already built in MVP for email and Slack) is extended with an EPNS call. Users receive a notification at each status transition: classified, pending_validation, minting, minted. Preferences are stored in the existing `users.metadata` JSONB column — no schema changes required.

#### AR Waste Identification

The existing TFLite model is surfaced as a live camera overlay using Expo Camera and the TensorFlow Lite React Native binding. Before the user taps submit, the overlay shows the predicted waste type and confidence as a floating badge on the feed. This reduces misclassification at the point of capture and improves overall system accuracy without any model retraining.

#### Nearby Recycling Centers Map

The `nearby_recycling_points()` PostGIS function is already live on Supabase from the MVP. Phase 2 surfaces this on a map screen using React Native Maps, showing registered recycling partner locations within 500m of the user. Tapping a pin shows accepted waste types (from `recycling_locations.waste_types`) and operating hours (from `recycling_locations.metadata` JSONB). Deep links from pins pre-fill the submission form coordinates, removing the need for the user to enable precise location permissions manually.

---

### 2.3 Enterprise Dashboard

**Current state (MVP v2.1):** No enterprise-facing interface. Individual recycler and validator UIs only.

#### ESG Reporting Dashboard

A new route (`/dashboard/enterprise`) shows aggregated metrics per organization: total waste recycled in kg, carbon offset in kg CO2, sBTC distributed, waste type breakdown, and submission trends over time. Data is served by a new `get_enterprise_stats(org_id)` Supabase RPC function. Reports export as PDF and CSV. Carbon offset figures pull directly from `submissions.carbon_offset_g`, making ESG reports blockchain-auditable.

#### Organization Accounts

A new `organizations` table links multiple user accounts to a single corporate entity. Supabase RLS policies are updated so org admins can query all submissions from their team. The existing `role` CHECK constraint on `users` is extended to include `'org_admin'`. Individual users join via an invite token. RLS ensures one organization cannot see another's data even with a service account key.

#### Bulk Submission API

Enterprise partners need to submit hundreds of items via API rather than one photo at a time. A new Edge Function `/bulk-classify` accepts a JSON array of up to 50 base64 images, fans them to parallel Groq API calls within Groq's rate limits, and returns an array of classification results. Per-item fraud detection still runs using the existing `getFraudScore()` logic. Bulk submissions are rate-limited separately in the `rate_limits` table using `action = 'bulk_submission'`.

#### Webhook System

The `task-completion-notification` Edge Function already contains a `webhooks` table stub from the MVP. Phase 2 fully implements it: org admins register webhook URLs in the dashboard. On any submission status change, the Edge Function delivers a signed payload (HMAC-SHA256 using a per-org secret) to all registered endpoints. Delivery is retried 3 times with exponential backoff. All attempts — success or failure — are recorded in a `webhook_delivery_log` table.

---

### 2.4 Advanced Fraud Detection

**Current state (MVP v2.1):** Three-signal rule-based system: perceptual hash deduplication, rate limiting at 5 per hour, and Radar.io geofencing. Fraud score is a weighted sum capped at 1.0.

#### ML-Based Anomaly Detection

The `fraud_events` table accumulates labeled fraud cases over time. Phase 2 trains an Isolation Forest (scikit-learn) on submission features: AI confidence, submission frequency, location variance over 7 days, average hash distance from prior submissions, and device fingerprint consistency. This model is versioned with DVC under a new `dvc.yaml` stage and tracked in a separate MLflow experiment named `fraud-detection-anomaly`. The ML-based score replaces the rule-based sum for users with 10 or more historical submissions. New users continue using the rule-based system until sufficient data accumulates.

#### Validator Collusion Detection

A nightly `pg_cron` job checks whether any validator is approving submissions from a specific user at a rate more than 2 standard deviations above that validator's own historical approval baseline. Flagged pairs are written to `fraud_events` with `fraud_type = 'validator_collusion'` and `severity = 'critical'`. Admin notification fires immediately through the Slack integration in the existing `task-completion-notification` Edge Function.

#### Device Fingerprinting

The existing `device_info` JSONB column captures basic metadata. Phase 2 enriches it with a fingerprint hash combining screen resolution, timezone, user agent, and GPU renderer string via WebGL. The hash is stored per submission. Multiple distinct accounts sharing a device fingerprint are flagged for manual review rather than auto-rejected, protecting shared-device households from false positives.

---

## Phase 3 — Ecosystem Growth (Weeks 21–32)

### 3.1 Token Marketplace

**Current state (MVP v2.1):** Fixed token-to-sBTC rate hardcoded in the `create_reward_on_mint()` PostgreSQL trigger. Linear, no secondary market.

#### Carbon Credit Marketplace

A new `marketplace_listings` table allows users and organizations to list verified carbon credits — backed by on-chain `carbon_offset_g` records — for peer-to-peer trading. The Clarity `rewards-pool.clar` contract is extended with `list-carbon-credit` and `purchase-carbon-credit` functions. The marketplace UI shows listings, seller history, and carbon offset provenance as an IPFS link to the original submission. Every listing is end-to-end on-chain verifiable.

Note: before Phase 3 marketplace work begins, the hardcoded `0.0001` sBTC rate in `create_reward_on_mint()` must be moved to a `platform_config` table with an admin update endpoint. This is listed under Technical Debt below.

#### NFT Recycling Certificates

Phase 3 mints an NFT (SIP-009 standard on Stacks) for high-volume recyclers and enterprise partners that exceed a monthly recycling threshold set in `platform_config`. NFT metadata includes waste type, weight, carbon offset, validator identity, timestamp, and the IPFS image link. A new `nft_certificates` Supabase table tracks minted certificates. Enterprises use these as auditable proof-of-recycling in sustainability reports.

#### Community Governance

A new `governance_proposals` table stores parameter change proposals: confidence thresholds, reward rates, validator stake minimums, waste category additions. STX-staked validators vote with weight proportional to `validators.stx_staked`. A new `governance.clar` Clarity contract executes approved proposals on-chain after a 7-day voting window. Results broadcast via the existing Supabase Realtime channel so all connected clients update instantly.

#### Secondary Token Market Integration

A new read-only Edge Function `/market-price` fetches the live SatsVerdant token price from Stacks DEX protocols (ALEX or Velar). The frontend reward display shows token amounts alongside the current market-rate USD equivalent. No new smart contracts are required — this links out to the DEX for trading.

---

### 3.2 Third-Party Integrations

#### Developer SDK

A typed TypeScript SDK (`@satsverdant/sdk`) wraps the Supabase auto-generated REST API and all four MVP Edge Functions. Published to npm. Exposes: `submit()`, `getStatus()`, `claimReward()`, `getNearbyLocations()`, and `getStats()`. Authentication uses a Supabase anon key passed at initialization — no additional auth infrastructure. Docs hosted on the public DagsHub repo alongside the MLflow experiment history.

#### Recycling Partner API

A new `partner_integrations` table stores credentials for registered recycling companies. Partners push pickup confirmations without photos: `POST /partners/confirm-pickup` accepts `{ partner_id, waste_type, weight_kg, bin_id }`. The Edge Function calculates and mints the reward using the same Clarity contract flow as standard submissions. Location verification uses the partner's pre-registered `recycling_locations.radar_fence_id` entry rather than Radar.io at submission time.

#### IoT Sensor Integration

Smart waste bins with weight sensors push readings to a new Edge Function `/iot/bin-event`. Payload: `{ bin_id, waste_type, weight_kg, timestamp }`. Bins are pre-registered in `recycling_locations` using the `metadata.bin_id` JSONB field. Rewards distribute to the organization account linked to the bin. IoT submissions bypass visual fraud detection but are rate-limited by bin capacity constraints — a bin cannot report more waste than its physical rated capacity within a time window.

#### Corporate ESG Platform Connectors

Pre-built connectors for Salesforce Sustainability Cloud, SAP Sustainability, and Microsoft Cloud for Sustainability. Each connector is a Supabase Edge Function that reformats SatsVerdant data into the target platform's schema and pushes on a schedule. Org admins configure connectors in the enterprise dashboard by providing OAuth credentials — no code required.

---

### 3.3 GraphQL API

**Current state (MVP v2.1):** Auto-generated PostgREST REST API via Supabase.

Supabase natively exposes a GraphQL endpoint at `/graphql/v1` via the `pg_graphql` extension. Phase 3 enables this extension and publishes the schema in the DagsHub repo. Complex queries — a user's last 10 submissions with rewards and validator details grouped by waste type — become single GraphQL operations instead of multiple chained REST calls. All existing RLS policies apply to GraphQL queries automatically with no additional configuration.

---

### 3.4 International Expansion

#### Multi-Language Support

The frontend uses `next-intl` for i18n. Translation files live in `src/locales/` as JSON, versioned in the DagsHub repo. Priority languages: Spanish, Portuguese, French, and Yoruba (targeting the West Africa launch market). The waste classification model is image-based and language-agnostic — no ML changes are needed for localization.

#### Regional Waste Categories

Phase 3 adds region-specific category sets — coconut husks, palm fronds, and rubber tyres for West Africa, for example — as a new `regional.categories` key in `params.yaml`, tracked by DVC. A region-tagged dataset is assembled, versioned, and pushed to the DagsHub DVC remote. A separate MLflow experiment (`waste-classifier-regional`) tracks regional model variants independently from the global model.

#### Fiat Off-Ramp

Stacks sBTC is already globally transferable. Phase 3 adds a fiat off-ramp integration via MoonPay or Transak for markets without direct sBTC liquidity. A new Edge Function `/offramp/quote` fetches live conversion rates and redirects to the provider's hosted checkout. No SatsVerdant-side fiat custody is required.

---

## Phase 4 — Enterprise Scale (Weeks 33–44)

### 4.1 MLOps at Scale

#### Automated Retraining CI/CD

A GitHub Actions workflow triggers on a new DVC dataset push to the DagsHub remote. It provisions a cloud GPU (Lambda Labs or Vast.ai), executes `dvc repro` to run the full pipeline, evaluates against the holdout set, logs to MLflow on DagsHub, and auto-promotes to Staging if accuracy meets the target. Human approval in the DagsHub UI is required to move Staging to Production. This closes the active learning loop end-to-end with zero manual steps after the dataset push.

#### Model Monitoring and Drift Detection

A new Edge Function `/monitor/drift` runs weekly via `pg_cron`. It computes the distribution of `ai_confidence` scores and `ai_waste_type` predictions over the past 7 days and compares against the training distribution stored as a DVC-tracked artifact. Significant drift — KL divergence above a threshold in `platform_config` — triggers a Slack alert via the existing notification Edge Function and creates a retraining task. Drift metrics are logged to a `model_monitoring` table and displayed in the enterprise dashboard.

#### Ensemble Inference

Phase 4 adds EfficientNetB3 as a secondary model in the Groq inference layer for borderline submissions (confidence between 0.6 and 0.75). The `/classify` Edge Function calls both models and uses the higher-confidence result. Both models have separate MLflow Registry entries and independent DVC dataset tracking. A/B data from Phase 2 informs the exact confidence band for ensemble routing.

---

### 4.2 Microservices Migration

**Current state (MVP v2.1):** All logic in Supabase Edge Functions. Appropriate for MVP scale.

At 10,000+ submissions per day, specific Edge Functions are extracted to dedicated services. The `/classify` function becomes a standalone FastAPI service (Python, on Railway or Fly.io) with independent auto-scaling. The Supabase Edge Function becomes a thin proxy. The Stacks blockchain interaction moves to a dedicated Node.js service using the `@stacks/transactions` SDK, which has better error handling and retry logic than the direct HTTP approach used in the MVP.

The Supabase database, RLS policies, and Realtime layer remain central and unchanged throughout. This is an additive migration — the Edge Function URLs remain as stable proxies during transition.

---

### 4.3 Multi-Region Infrastructure

**CDN for image delivery.** Supabase Storage public URLs are fronted with Cloudflare CDN. Images are served from edge nodes nearest to the requesting client. The IPFS CID in `submissions.image_ipfs_cid` is unchanged — CDN is a transparent cache only.

**Database read replicas.** Supabase read replicas (Pro plan) receive all validator queue, stats, and leaderboard queries, reducing load on the primary write instance.

**Multi-region Edge Functions.** The `/classify` function deploys to US East, EU West, and Africa regions using Supabase's multi-region Edge Function support. This directly addresses the West Africa expansion where US-only latency would exceed 200ms per classification.

---

### 4.4 Security Hardening

**Multi-signature transactions.** The current service account key is replaced for high-value transactions with a 2-of-3 multisig scheme using Stacks' native multisig: primary service, HSM, and a time-locked backup key.

**GDPR and right to erasure.** A new `/privacy/delete` Edge Function anonymizes `users.wallet_address`, `users.email`, and `users.display_name`; replaces `submissions.image_url` with a placeholder; and logs the deletion to a `privacy_audit_log` table. On-chain Stacks records are immutable and excluded — documented in the privacy policy.

**Complete audit trail.** A `platform_audit_log` table is populated by PostgreSQL triggers on all critical tables, recording: the authenticated user ID, operation type, table and row affected, previous values in JSONB, and timestamp. The log is append-only via RLS, retained for 90 days, then archived to cold storage.

---

## Architecture Invariants

These principles hold across all phases regardless of what is added:

**DVC as the single source of truth for data.** Every model in the MLflow Model Registry must have a `dataset_dvc_commit` parameter logged in its MLflow run. Enforced in `src/train.py` and checked in the Phase 4 CI pipeline.

**RLS as the security boundary.** Every new Supabase table ships with a tested RLS policy before any application code touches it. No table goes live without RLS enabled.

**Stable Edge Function contracts.** `/classify`, `/mint-tokens`, `/claim-reward`, and `/task-completion-notification` are versioned contracts. Breaking changes increment the path version (`/v2/classify`). Old versions stay available for 60 days after deprecation notice.

**MLflow Model Registry as the deployment gate.** No model is served in production without a `Production` stage tag in the Registry. The `/classify` Edge Function reads the active Production model version from the Registry at cold-start — never from a hardcoded path or environment variable.

---

## Technical Debt to Resolve Before Phase 2

**Fix the Q1 2025 timeline error.** The original grant application referenced past dates. All post-MVP dates must reference Q3/Q4 2026 consistently across all PRD documents.

**Migrate image quality grading out of Python OpenCV.** The `quality_grader.py` described in the AI/ML PRD cannot run inside a Supabase Deno Edge Function. Phase 2 replaces it with the `sharp` npm library (Deno compatible) or moves quality grading to the standalone FastAPI service introduced in Phase 4.

**Parameterize the sBTC conversion rate.** Currently hardcoded as `0.0001` in the `create_reward_on_mint()` PostgreSQL trigger. Must move to a `platform_config` table with an admin update endpoint before Phase 3 marketplace work begins.

**Add a dedicated DVC pipeline stage for the fraud detection model.** The Phase 2 Isolation Forest fraud detector needs its own `dvc.yaml` stage and MLflow experiment from day one — not retrofitted after deployment.

**Add automated inter-annotator agreement measurement to the evaluate stage.** The MVP success criteria require >=85% inter-annotator agreement but there is no automated measurement in the current pipeline. This must be added as a metric in `metrics/eval_metrics.json` and tracked in MLflow before the active learning pipeline activates — otherwise retraining data quality cannot be verified programmatically.

---

## Phase Success Metrics

### Phase 2 (Weeks 13–20)
- Mobile app installs: 500+
- E-waste classification live at >=75% recall
- Active learning retraining: first automated run completed
- Enterprise partnerships signed: 3+
- Offline submission sync success rate: >=98%

### Phase 3 (Weeks 21–32)
- Carbon credit marketplace volume: $5,000+/month
- Developer SDK npm downloads: 100+
- IoT bin integrations: 5+ live partners
- International users: 20% of total active users
- On-chain governance proposals completed: 2+

### Phase 4 (Weeks 33–44)
- Enterprise organization accounts: 20+
- Monthly submissions: 5,000+
- Carbon offset tracked: 50+ tonnes/month
- Retraining pipeline: fully automated with zero manual steps to Staging promotion
- Global Edge Function p95 latency: <150ms across US, EU, and Africa

---

*This is a living document. Priorities should be revisited after each phase based on user feedback, validator input, on-chain adoption data, and grant committee guidance. The existing prototype contains working implementations of several features listed here — reference them during development but build all new versions following the v2.1 architecture patterns.*