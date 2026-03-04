# SatsVerdant Smart Contracts PRD — MVP v2.0

**Project:** SatsVerdant Clarity Smart Contracts
**Blockchain:** Stacks (Bitcoin Layer 2)
**Version:** 2.0 (MVP — Revised)
**Timeline:** 4 weeks (parallel with Supabase backend)
**Goal:** Production-ready Clarity contracts for waste tokenization, validator staking, and sBTC reward distribution — all interfaces aligned to the Supabase Edge Functions that call them.

### What Changed from v1.0

| Area | v1.0 | v2.0 |
|---|---|---|
| Waste categories | plastic, paper, metal, organic, **electronic** | plastic, paper, metal, organic, **glass** |
| `electronic-token` | Defined, minted | **Removed** — e-waste is Phase 2 target |
| `glass-token` | Missing | **Added** — matches v2.1 classifier output and Supabase schema |
| Authorized minter | Backend service account (vague) | **Supabase `/mint-tokens` Edge Function service role key** |
| `mint-waste-token` args | waste-type, amount, recipient, submission-id, carbon-offset-g, validator | Unchanged — but submission-id now explicitly maps to `submissions.id` (UUID as buff 32) |
| `governance.clar` | Listed as MVP contract | **Moved to Phase 3** — not in MVP scope |
| Contract callers | FastAPI background workers | **Supabase Edge Functions** (Deno/TypeScript) |
| Post-deploy init | Generic | **Specific service role key registration sequence** |

---

## 2. Contract Architecture

```
            Supabase Edge Functions (Deno/TypeScript)
            ┌──────────────────────────────────────┐
            │  /mint-tokens    /claim-reward        │
            │  /classify       (validator-pool)     │
            └──────────────────────────────────────┘
                      │              │
          ┌───────────┘              └──────────────┐
          ▼                                         ▼
┌──────────────────┐                    ┌──────────────────┐
│  waste-tokens    │◄───cross-contract──│  rewards-pool    │
│  .clar           │                    │  .clar           │
│  (SIP-010 x 5)   │                    │  (sBTC distrib.) │
└────────┬─────────┘                    └──────────────────┘
         │
         │ cross-contract (mint-credits)
         ▼
┌──────────────────┐     ┌──────────────────┐
│  carbon-credits  │     │  validator-pool  │
│  .clar (SIP-010) │     │  .clar (staking) │
└──────────────────┘     └──────────────────┘
```

### MVP Contracts (this document)
1. **waste-tokens.clar** — SIP-010 fungible tokens for 5 waste types (plastic, paper, metal, organic, glass)
2. **validator-pool.clar** — Validator staking and on-chain validation records
3. **rewards-pool.clar** — sBTC reward distribution and claiming
4. **carbon-credits.clar** — Carbon offset credit tracking (SIP-010)

### Post-MVP Contracts (Phase 3+)
- **governance.clar** — DAO voting on platform parameters
- **marketplace.clar** — Carbon credit peer-to-peer trading
- **nft-certificates.clar** — SIP-009 proof-of-recycling certificates

---

## 3. Technical Specifications

### Clarity Features Used
- `define-fungible-token` — waste tokens and carbon credits
- `define-map` — validator registry, submission records, authorization maps
- `define-data-var` — conversion rate, total staked, fee amounts
- `define-constant` — error codes, minimum stake, owner
- `asserts!`, `try!`, `match` — safety and error propagation
- Post-conditions on all token transfers
- `tx-sender` for caller identity, `contract-caller` for cross-contract

### SIP-010 Compliance
All token contracts implement the full SIP-010 fungible token trait: `transfer`, `get-balance`, `get-total-supply`, `get-name`, `get-symbol`, `get-decimals`, `get-token-uri`.

---

## 4. Contract 1: waste-tokens.clar

### Purpose
Manage the five MVP waste-type tokens as SIP-010 fungible tokens. Minting is gated to the Supabase `/mint-tokens` Edge Function service role key registered as an authorized minter. Burning is gated to the `rewards-pool` contract registered as an authorized burner.

### Data Structures

```clarity
;; ── Title: SatsVerdant Waste Tokens
;; ── Version: 2.0.0
;; ── Description: SIP-010 fungible tokens for waste classification rewards.
;;    Five MVP waste types: plastic, paper, metal, organic, glass.
;;    NOTE: electronic-token is intentionally excluded from MVP.
;;    It will be introduced in waste-tokens-v2.clar when the e-waste
;;    training dataset reaches >= 3,000 images (Phase 2 target).
;;
;; Minting:  Only authorized minters (Supabase /mint-tokens Edge Function)
;; Burning:  Only authorized burners (rewards-pool contract)
;; Transfers: SIP-010 compliant, sender must be tx-sender

(define-constant contract-owner         tx-sender)
(define-constant min-stake-amount       u1000000000)
(define-constant err-owner-only         (err u100))
(define-constant err-not-authorized     (err u101))
(define-constant err-invalid-waste-type (err u102))
(define-constant err-insufficient-balance (err u103))
(define-constant err-zero-amount        (err u104))
(define-constant err-no-block-time      (err u105))
(define-constant err-no-metadata        (err u106))

;; ── Fungible tokens — 5 MVP categories ───────────────────────────────
;; electronic-token is NOT defined here. Any call with waste-type="electronic"
;; will fall through to err-invalid-waste-type (u102) in every match block.
(define-fungible-token plastic-token)
(define-fungible-token paper-token)
(define-fungible-token metal-token)
(define-fungible-token organic-token)
(define-fungible-token glass-token)

;; ── Authorization ─────────────────────────────────────────────────────
;; Minters: Supabase /mint-tokens Edge Function service role key
(define-map authorized-minters principal bool)
;; Burners: rewards-pool contract principal only
(define-map authorized-burners principal bool)

;; ── Token metadata ────────────────────────────────────────────────────
(define-map token-metadata
  { token-type: (string-ascii 20) }
  {
    name:     (string-ascii 32),
    symbol:   (string-ascii 10),
    decimals: uint,
    uri:      (optional (string-utf8 256))
  }
)

;; ── Per-user submission stats ─────────────────────────────────────────
(define-map user-submissions
  { user: principal }
  {
    total-submissions:     uint,
    total-tokens-earned:   uint,
    last-submission-block: uint
  }
)

;; ── Immutable on-chain submission audit log ───────────────────────────
;; submission-id = Supabase submissions.id cast to buff 32
(define-map submission-records
  { submission-id: (buff 32) }
  {
    user:             principal,
    waste-type:       (string-ascii 20),
    tokens-minted:    uint,
    carbon-offset-g:  uint,
    validator:        principal,
    block-height:     uint,
    timestamp:        uint
  }
)
```

### Administrative Functions

```clarity
;; Called once immediately after deployment to set token display metadata.
(define-public (initialize-metadata)
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)

    (map-set token-metadata { token-type: "plastic" }
      { name: "Plastic Waste Token",  symbol: "PLASTIC", decimals: u0, uri: none })
    (map-set token-metadata { token-type: "paper" }
      { name: "Paper Waste Token",    symbol: "PAPER",   decimals: u0, uri: none })
    (map-set token-metadata { token-type: "metal" }
      { name: "Metal Waste Token",    symbol: "METAL",   decimals: u0, uri: none })
    (map-set token-metadata { token-type: "organic" }
      { name: "Organic Waste Token",  symbol: "ORGANIC", decimals: u0, uri: none })
    (map-set token-metadata { token-type: "glass" }
      { name: "Glass Waste Token",    symbol: "GLASS",   decimals: u0, uri: none })

    (ok true)
  )
)

;; Register the Supabase /mint-tokens Edge Function service role key as minter.
;; Called once post-deployment with the service account principal.
(define-public (add-minter (minter principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-set authorized-minters minter true))
  )
)

(define-public (remove-minter (minter principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-delete authorized-minters minter))
  )
)

;; Register rewards-pool.clar as the sole authorized burner.
(define-public (add-burner (burner principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-set authorized-burners burner true))
  )
)

(define-private (is-authorized-minter (caller principal))
  (default-to false (map-get? authorized-minters caller))
)

(define-private (is-authorized-burner (caller principal))
  (default-to false (map-get? authorized-burners caller))
)
```

### Minting

```clarity
;; Called by: Supabase /mint-tokens Edge Function (service role key)
;; Triggered: after validator approves in ValidatorQueue.tsx (Supabase Realtime)
;;
;; submission-id: Supabase submissions.id (UUID) encoded as buff 32
;; carbon-offset-g: calculated in Edge Function as weight_kg * carbon_factor[waste_type]
;; validator: Stacks principal of the approving validator
(define-public (mint-waste-token
    (waste-type       (string-ascii 20))
    (amount           uint)
    (recipient        principal)
    (submission-id    (buff 32))
    (carbon-offset-g  uint)
    (validator        principal)
  )
  (begin
    (asserts! (is-authorized-minter tx-sender) err-not-authorized)
    (asserts! (> amount u0) err-zero-amount)

    (try! (match waste-type
      "plastic" (ft-mint? plastic-token amount recipient)
      "paper"   (ft-mint? paper-token   amount recipient)
      "metal"   (ft-mint? metal-token   amount recipient)
      "organic" (ft-mint? organic-token amount recipient)
      "glass"   (ft-mint? glass-token   amount recipient)
      err-invalid-waste-type  ;; "electronic" and any unknown type hits here
    ))

    ;; Immutable on-chain record linking Stacks transaction to Supabase submission row
    (map-set submission-records { submission-id: submission-id }
      {
        user:            recipient,
        waste-type:      waste-type,
        tokens-minted:   amount,
        carbon-offset-g: carbon-offset-g,
        validator:       validator,
        block-height:    block-height,
        timestamp:       (unwrap! (get-block-info? time block-height) err-no-block-time)
      }
    )

    ;; Update per-user lifetime stats
    (let (
      (stats (default-to
        { total-submissions: u0, total-tokens-earned: u0, last-submission-block: u0 }
        (map-get? user-submissions { user: recipient })
      ))
    )
      (map-set user-submissions { user: recipient }
        {
          total-submissions:     (+ (get total-submissions stats) u1),
          total-tokens-earned:   (+ (get total-tokens-earned stats) amount),
          last-submission-block: block-height
        }
      )
    )

    (print { event: "token-minted", waste-type: waste-type, amount: amount,
             recipient: recipient, submission-id: submission-id,
             carbon-offset-g: carbon-offset-g })
    (ok amount)
  )
)

;; Batch mint — up to 10 submissions per transaction.
;; Used by /bulk-classify Edge Function (Phase 2 enterprise feature).
(define-public (batch-mint-waste-tokens
    (mints (list 10 {
      waste-type:      (string-ascii 20),
      amount:          uint,
      recipient:       principal,
      submission-id:   (buff 32),
      carbon-offset-g: uint,
      validator:       principal
    }))
  )
  (begin
    (asserts! (is-authorized-minter tx-sender) err-not-authorized)
    (ok (map mint-single-waste-token mints))
  )
)

(define-private (mint-single-waste-token (d {
    waste-type: (string-ascii 20), amount: uint, recipient: principal,
    submission-id: (buff 32), carbon-offset-g: uint, validator: principal
  }))
  (mint-waste-token
    (get waste-type d) (get amount d) (get recipient d)
    (get submission-id d) (get carbon-offset-g d) (get validator d)
  )
)
```

### Transfer (SIP-010)

```clarity
(define-public (transfer
    (waste-type (string-ascii 20))
    (amount     uint)
    (sender     principal)
    (recipient  principal)
    (memo       (optional (buff 34)))
  )
  (begin
    (asserts! (is-eq tx-sender sender) err-not-authorized)

    (try! (match waste-type
      "plastic" (ft-transfer? plastic-token amount sender recipient)
      "paper"   (ft-transfer? paper-token   amount sender recipient)
      "metal"   (ft-transfer? metal-token   amount sender recipient)
      "organic" (ft-transfer? organic-token amount sender recipient)
      "glass"   (ft-transfer? glass-token   amount sender recipient)
      err-invalid-waste-type
    ))

    (match memo memo-val (print { event: "transfer", memo: memo-val }) true)
    (ok true)
  )
)
```

### Burning

```clarity
;; Called by: rewards-pool contract via cross-contract call during claim-rewards.
;; The rewards-pool principal must be registered via add-burner before claiming works.
(define-public (burn-waste-token
    (waste-type (string-ascii 20))
    (amount     uint)
    (owner      principal)
  )
  (begin
    (asserts!
      (or (is-eq tx-sender owner)
          (is-authorized-burner contract-caller))
      err-not-authorized
    )

    (try! (match waste-type
      "plastic" (ft-burn? plastic-token amount owner)
      "paper"   (ft-burn? paper-token   amount owner)
      "metal"   (ft-burn? metal-token   amount owner)
      "organic" (ft-burn? organic-token amount owner)
      "glass"   (ft-burn? glass-token   amount owner)
      err-invalid-waste-type
    ))

    (print { event: "token-burned", waste-type: waste-type, amount: amount, owner: owner })
    (ok amount)
  )
)
```

### Read-Only Functions

```clarity
(define-read-only (get-balance (waste-type (string-ascii 20)) (account principal))
  (ok (match waste-type
    "plastic" (ft-get-balance plastic-token account)
    "paper"   (ft-get-balance paper-token   account)
    "metal"   (ft-get-balance metal-token   account)
    "organic" (ft-get-balance organic-token account)
    "glass"   (ft-get-balance glass-token   account)
    u0
  ))
)

(define-read-only (get-total-supply (waste-type (string-ascii 20)))
  (ok (match waste-type
    "plastic" (ft-get-supply plastic-token)
    "paper"   (ft-get-supply paper-token)
    "metal"   (ft-get-supply metal-token)
    "organic" (ft-get-supply organic-token)
    "glass"   (ft-get-supply glass-token)
    u0
  ))
)

;; Total tokens across all 5 types for one user (used by dashboard)
(define-read-only (get-total-balance (account principal))
  (ok (+
    (ft-get-balance plastic-token account)
    (ft-get-balance paper-token   account)
    (ft-get-balance metal-token   account)
    (ft-get-balance organic-token account)
    (ft-get-balance glass-token   account)
  ))
)

(define-read-only (get-user-stats (user principal))
  (ok (map-get? user-submissions { user: user }))
)

(define-read-only (get-submission-record (submission-id (buff 32)))
  (ok (map-get? submission-records { submission-id: submission-id }))
)

(define-read-only (get-token-metadata (waste-type (string-ascii 20)))
  (ok (map-get? token-metadata { token-type: waste-type }))
)

;; SIP-010 trait functions
(define-read-only (get-name (waste-type (string-ascii 20)))
  (ok (get name (unwrap! (map-get? token-metadata { token-type: waste-type }) err-no-metadata)))
)
(define-read-only (get-symbol (waste-type (string-ascii 20)))
  (ok (get symbol (unwrap! (map-get? token-metadata { token-type: waste-type }) err-no-metadata)))
)
(define-read-only (get-decimals (waste-type (string-ascii 20)))
  (ok (get decimals (unwrap! (map-get? token-metadata { token-type: waste-type }) err-no-metadata)))
)
(define-read-only (get-token-uri (waste-type (string-ascii 20)))
  (ok (get uri (unwrap! (map-get? token-metadata { token-type: waste-type }) err-no-metadata)))
)
```

---

## 5. Contract 2: validator-pool.clar

### Purpose
Manage validator staking, reputation, and on-chain validation records. The Supabase `/mint-tokens` Edge Function calls `record-validation` after every validator decision to write immutable on-chain proof and pay the validation fee.

```clarity
(define-constant contract-owner         tx-sender)
(define-constant min-stake-amount       u1000000000)  ;; 1,000 STX in micro-STX
(define-constant err-owner-only         (err u200))
(define-constant err-insufficient-stake (err u201))
(define-constant err-not-validator      (err u202))
(define-constant err-suspended          (err u203))
(define-constant err-already-validator  (err u204))

(define-map validators principal
  {
    staked-amount:          uint,
    reputation-score:       uint,   ;; 0–100
    validations-count:      uint,
    approvals-count:        uint,
    rejections-count:       uint,
    is-active:              bool,
    joined-at-block:        uint,
    last-validation-block:  uint
  }
)

;; submission-id corresponds to Supabase submissions.id (UUID as buff 32)
(define-map validation-records
  { submission-id: (buff 32) }
  {
    validator:          principal,
    decision:           (string-ascii 10),  ;; "approved" | "rejected"
    validated-at-block: uint,
    fee-earned:         uint
  }
)

(define-data-var total-staked   uint u0)
(define-data-var validation-fee uint u100000)  ;; 0.1 STX per validation
```

### Core Functions

```clarity
(define-public (stake-as-validator (amount uint))
  (begin
    (asserts! (>= amount min-stake-amount) err-insufficient-stake)
    (asserts! (is-none (map-get? validators tx-sender)) err-already-validator)
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    (map-set validators tx-sender {
      staked-amount: amount, reputation-score: u100,
      validations-count: u0, approvals-count: u0, rejections-count: u0,
      is-active: true, joined-at-block: block-height, last-validation-block: u0
    })
    (var-set total-staked (+ (var-get total-staked) amount))
    (print { event: "validator-staked", validator: tx-sender, amount: amount })
    (ok true)
  )
)

(define-public (add-stake (amount uint))
  (let ((v (unwrap! (map-get? validators tx-sender) err-not-validator)))
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    (map-set validators tx-sender (merge v { staked-amount: (+ (get staked-amount v) amount) }))
    (var-set total-staked (+ (var-get total-staked) amount))
    (ok true)
  )
)

(define-public (unstake)
  (let (
    (v      (unwrap! (map-get? validators tx-sender) err-not-validator))
    (amount (get staked-amount v))
  )
    (asserts! (get is-active v) err-suspended)
    (try! (as-contract (stx-transfer? amount tx-sender tx-sender)))
    (map-delete validators tx-sender)
    (var-set total-staked (- (var-get total-staked) amount))
    (print { event: "validator-unstaked", validator: tx-sender, amount: amount })
    (ok amount)
  )
)

;; Called by: Supabase /mint-tokens Edge Function after validator approves/rejects
;; in the ValidatorQueue.tsx Realtime component.
(define-public (record-validation
    (submission-id (buff 32))
    (validator     principal)
    (decision      (string-ascii 10))
  )
  (let ((v (unwrap! (map-get? validators validator) err-not-validator)))
    (asserts! (get is-active v) err-suspended)

    (map-set validation-records { submission-id: submission-id }
      { validator: validator, decision: decision,
        validated-at-block: block-height, fee-earned: (var-get validation-fee) }
    )

    (map-set validators validator (merge v {
      validations-count:    (+ (get validations-count v) u1),
      approvals-count:      (if (is-eq decision "approved")
                              (+ (get approvals-count v) u1) (get approvals-count v)),
      rejections-count:     (if (is-eq decision "rejected")
                              (+ (get rejections-count v) u1) (get rejections-count v)),
      last-validation-block: block-height
    }))

    (try! (as-contract (stx-transfer? (var-get validation-fee) tx-sender validator)))

    (print { event: "validation-recorded", submission-id: submission-id,
             validator: validator, decision: decision })
    (ok true)
  )
)

;; Admin: update reputation score (driven by Supabase fraud detection results)
(define-public (update-reputation (validator principal) (new-score uint))
  (let ((v (unwrap! (map-get? validators validator) err-not-validator)))
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (map-set validators validator (merge v { reputation-score: new-score }))
    (ok true)
  )
)

(define-public (suspend-validator (validator principal))
  (let ((v (unwrap! (map-get? validators validator) err-not-validator)))
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (map-set validators validator (merge v { is-active: false }))
    (print { event: "validator-suspended", validator: validator })
    (ok true)
  )
)

(define-public (reactivate-validator (validator principal))
  (let ((v (unwrap! (map-get? validators validator) err-not-validator)))
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (map-set validators validator (merge v { is-active: true }))
    (ok true)
  )
)
```

### Read-Only Functions

```clarity
(define-read-only (get-validator (validator principal))
  (ok (map-get? validators validator))
)
(define-read-only (is-active-validator (validator principal))
  (match (map-get? validators validator) v (ok (get is-active v)) (ok false))
)
(define-read-only (get-validation-record (submission-id (buff 32)))
  (ok (map-get? validation-records { submission-id: submission-id }))
)
(define-read-only (get-total-staked)
  (ok (var-get total-staked))
)
;; Returns accuracy as basis points (0–10000) to avoid floats
(define-read-only (get-accuracy-rate (validator principal))
  (match (map-get? validators validator)
    v (let ((total (get validations-count v)) (approvals (get approvals-count v)))
        (if (> total u0) (ok (/ (* approvals u10000) total)) (ok u0))
      )
    (err u202)
  )
)
```

---

## 6. Contract 3: rewards-pool.clar

### Purpose
Distribute sBTC rewards by burning waste tokens. Called by the Supabase `/claim-reward` Edge Function. The conversion rate is a `data-var` in MVP — Phase 3 parameterizes it through the `platform_config` Supabase table so rate changes never require a contract redeployment.

```clarity
(define-constant contract-owner     tx-sender)
(define-constant err-owner-only     (err u300))
(define-constant err-pool-empty     (err u302))
(define-constant err-invalid-amount (err u303))

;; 1,000 waste tokens = 0.0001 sBTC
;; sbtc_sats = (token_amount * 100_000_000) / conversion-rate
(define-data-var conversion-rate            uint u10000000)
(define-data-var total-rewards-distributed  uint u0)

(define-map reward-claims
  { user: principal, claim-id: uint }
  {
    waste-type:          (string-ascii 20),
    waste-tokens-burned: uint,
    sbtc-amount:         uint,
    claimed-at-block:    uint
  }
)
(define-map user-claim-count principal uint)
```

### Core Functions

```clarity
;; Called by: Supabase /claim-reward Edge Function.
;; The Edge Function first verifies rewards.status = 'claimable' in Supabase
;; before calling this, ensuring double-spend protection at the application layer.
(define-public (claim-rewards
    (waste-type   (string-ascii 20))
    (token-amount uint)
  )
  (let (
    (sbtc-sats (/ (* token-amount u100000000) (var-get conversion-rate)))
    (claim-id  (default-to u0 (map-get? user-claim-count tx-sender)))
  )
    (asserts! (> token-amount u0) err-invalid-amount)
    (asserts! (>= (stx-get-balance (as-contract tx-sender)) sbtc-sats) err-pool-empty)

    ;; Cross-contract burn — rewards-pool must be registered as authorized burner
    (try! (contract-call? .waste-tokens burn-waste-token waste-type token-amount tx-sender))

    ;; Transfer sBTC to claimant
    (try! (as-contract (stx-transfer? sbtc-sats tx-sender tx-sender)))

    (map-set reward-claims { user: tx-sender, claim-id: claim-id }
      { waste-type: waste-type, waste-tokens-burned: token-amount,
        sbtc-amount: sbtc-sats, claimed-at-block: block-height }
    )
    (map-set user-claim-count tx-sender (+ claim-id u1))
    (var-set total-rewards-distributed (+ (var-get total-rewards-distributed) sbtc-sats))

    (print { event: "reward-claimed", user: tx-sender, waste-type: waste-type,
             tokens-burned: token-amount, sbtc-amount: sbtc-sats })
    (ok sbtc-sats)
  )
)

;; Fund pool — called by admin when seeding initial sBTC reserve
(define-public (fund-pool (amount uint))
  (begin
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    (print { event: "pool-funded", funder: tx-sender, amount: amount })
    (ok amount)
  )
)

;; Admin: update conversion rate.
;; Phase 3: this will be called by a Supabase Edge Function when
;; platform_config.sbtc_conversion_rate changes, so no manual admin step is needed.
(define-public (set-conversion-rate (new-rate uint))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (var-set conversion-rate new-rate)
    (print { event: "conversion-rate-updated", new-rate: new-rate })
    (ok new-rate)
  )
)
```

### Read-Only Functions

```clarity
(define-read-only (get-pool-balance)
  (ok (stx-get-balance (as-contract tx-sender)))
)
(define-read-only (get-conversion-rate)
  (ok (var-get conversion-rate))
)
(define-read-only (estimate-reward (token-amount uint))
  (ok (/ (* token-amount u100000000) (var-get conversion-rate)))
)
(define-read-only (get-claim-record (user principal) (claim-id uint))
  (ok (map-get? reward-claims { user: user, claim-id: claim-id }))
)
(define-read-only (get-user-claim-count (user principal))
  (ok (default-to u0 (map-get? user-claim-count user)))
)
(define-read-only (get-total-rewards-distributed)
  (ok (var-get total-rewards-distributed))
)
```

---

## 7. Contract 4: carbon-credits.clar

### Purpose
Track verified carbon offset credits as SIP-010 tokens. 1 credit = 1 gram CO₂ offset. Minted by `waste-tokens.clar` during `mint-waste-token`. Phase 3 adds the marketplace and corporate purchase functions.

```clarity
(define-constant contract-owner     tx-sender)
(define-constant err-owner-only     (err u400))
(define-constant err-not-authorized (err u401))

(define-fungible-token carbon-credit)
(define-map authorized-credit-minters principal bool)

(define-map carbon-records
  { submission-id: (buff 32) }
  {
    user:            principal,
    waste-type:      (string-ascii 20),
    carbon-offset-g: uint,
    tokens-issued:   uint,
    issued-at-block: uint
  }
)
```

### Core Functions

```clarity
;; Called by: waste-tokens.clar (cross-contract) during mint-waste-token.
;; waste-tokens contract must be registered via add-credit-minter post-deploy.
(define-public (mint-credits
    (submission-id   (buff 32))
    (user            principal)
    (waste-type      (string-ascii 20))
    (carbon-offset-g uint)
  )
  (begin
    (asserts!
      (default-to false (map-get? authorized-credit-minters contract-caller))
      err-not-authorized
    )
    (try! (ft-mint? carbon-credit carbon-offset-g user))
    (map-set carbon-records { submission-id: submission-id }
      { user: user, waste-type: waste-type, carbon-offset-g: carbon-offset-g,
        tokens-issued: carbon-offset-g, issued-at-block: block-height }
    )
    (print { event: "carbon-credits-issued", user: user, amount: carbon-offset-g })
    (ok carbon-offset-g)
  )
)

(define-public (transfer
    (amount    uint)
    (sender    principal)
    (recipient principal)
    (memo      (optional (buff 34)))
  )
  (begin
    (asserts! (is-eq tx-sender sender) err-not-authorized)
    (try! (ft-transfer? carbon-credit amount sender recipient))
    (match memo memo-val (print { event: "transfer", memo: memo-val }) true)
    (ok true)
  )
)

(define-public (add-credit-minter (minter principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-set authorized-credit-minters minter true))
  )
)

;; SIP-010
(define-read-only (get-name)         (ok "SatsVerdant Carbon Credit"))
(define-read-only (get-symbol)       (ok "CARBON"))
(define-read-only (get-decimals)     (ok u0))
(define-read-only (get-total-supply) (ok (ft-get-supply carbon-credit)))
(define-read-only (get-balance (account principal))
  (ok (ft-get-balance carbon-credit account))
)
(define-read-only (get-token-uri)
  (ok (some u"https://satsverdant.com/carbon-metadata.json"))
)
(define-read-only (get-carbon-record (submission-id (buff 32)))
  (ok (map-get? carbon-records { submission-id: submission-id }))
)
```

---

## 8. Testing Strategy

### Unit Tests (Clarinet + Vitest)

```typescript
// tests/waste-tokens.test.ts
import { Clarinet, Tx, Chain, Account } from "@stacks/clarinet-sdk";
import { describe, it, expect } from "vitest";

describe("waste-tokens v2.0", () => {

  it("mints glass tokens — confirming glass replaces electronic", () => {
    Clarinet.test(({ chain, accounts }) => {
      const deployer = accounts.get("deployer")!;
      const user     = accounts.get("wallet_1")!;

      const block = chain.mineBlock([
        Tx.contractCall("waste-tokens", "add-minter",
          [`'${deployer.address}`], deployer.address),
        Tx.contractCall("waste-tokens", "mint-waste-token",
          [`"glass"`, `u80`, `'${user.address}`,
           `0x1234567890abcdef1234567890abcdef12345678`,
           `u240`, `'${deployer.address}`],
          deployer.address)
      ]);

      block.receipts[1].result.expectOk().expectUint(80);

      chain.callReadOnlyFn("waste-tokens", "get-balance",
        [`"glass"`, `'${user.address}`], user.address
      ).result.expectOk().expectUint(80);
    });
  });

  it("rejects electronic as invalid waste type (err u102)", () => {
    Clarinet.test(({ chain, accounts }) => {
      const deployer = accounts.get("deployer")!;
      const user     = accounts.get("wallet_1")!;

      const block = chain.mineBlock([
        Tx.contractCall("waste-tokens", "add-minter",
          [`'${deployer.address}`], deployer.address),
        Tx.contractCall("waste-tokens", "mint-waste-token",
          [`"electronic"`, `u100`, `'${user.address}`,
           `0xabcd`, `u500`, `'${deployer.address}`],
          deployer.address)
      ]);

      block.receipts[1].result.expectErr().expectUint(102);
    });
  });

  it("rejects unauthorized minter (err u101)", () => {
    Clarinet.test(({ chain, accounts }) => {
      const attacker = accounts.get("wallet_2")!;
      const user     = accounts.get("wallet_1")!;

      const block = chain.mineBlock([
        Tx.contractCall("waste-tokens", "mint-waste-token",
          [`"plastic"`, `u100`, `'${user.address}`,
           `0xabcd`, `u500`, `'${attacker.address}`],
          attacker.address)
      ]);

      block.receipts[0].result.expectErr().expectUint(101);
    });
  });

  it("full flow: mint glass → claim reward → balance zero", () => {
    Clarinet.test(({ chain, accounts }) => {
      const deployer   = accounts.get("deployer")!;
      const user       = accounts.get("wallet_1")!;
      const rewardsPool = "ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM.rewards-pool";

      chain.mineBlock([
        Tx.contractCall("waste-tokens", "add-minter",
          [`'${deployer.address}`], deployer.address),
        Tx.contractCall("waste-tokens", "add-burner",
          [`'${rewardsPool}`], deployer.address),
        Tx.contractCall("rewards-pool", "fund-pool",
          [`u10000000`], deployer.address),
        Tx.contractCall("waste-tokens", "mint-waste-token",
          [`"glass"`, `u1000`, `'${user.address}`,
           `0xabcdef1234567890abcdef1234567890abcdef12`,
           `u3000`, `'${deployer.address}`],
          deployer.address)
      ]);

      const claim = chain.mineBlock([
        Tx.contractCall("rewards-pool", "claim-rewards",
          [`"glass"`, `u1000`], user.address)
      ]);
      claim.receipts[0].result.expectOk();

      chain.callReadOnlyFn("waste-tokens", "get-balance",
        [`"glass"`, `'${user.address}`], user.address
      ).result.expectOk().expectUint(0);
    });
  });

});
```

---

## 9. Security

| Concern | Mitigated | How |
|---|---|---|
| Unauthorized minting | Yes | `authorized-minters` map; only registered Supabase service role key |
| Unauthorized burning | Yes | `authorized-burners` map; only `rewards-pool` contract |
| Reentrancy | N/A | Clarity deterministic execution — no reentrancy possible |
| Integer overflow | N/A | Clarity `uint` is bounded and safe |
| Front-running | Minimal | Stacks block finality makes front-running impractical |
| `electronic` category | Eliminated | No token defined; any call returns `err-invalid-waste-type` (u102) |
| Owner key compromise | Phase 4 | Move to multisig (2-of-3) for high-value operations in Phase 4 |
| Conversion rate manipulation | Yes | Admin-only `set-conversion-rate`; Phase 3 automates via Edge Function |

---

## 10. Deployment

### Post-Deployment Initialization Sequence

```clarity
;; Run these calls in order immediately after deployment.
;; SP_SERVICE_ACCOUNT = Supabase /mint-tokens Edge Function service role key principal.

;; 1. Initialize token metadata (one-time)
(contract-call? .waste-tokens initialize-metadata)

;; 2. Register Supabase service account as the sole authorized minter
(contract-call? .waste-tokens add-minter 'SP_SERVICE_ACCOUNT)

;; 3. Authorize rewards-pool to burn tokens during reward claims
(contract-call? .waste-tokens add-burner .rewards-pool)

;; 4. Authorize waste-tokens to mint carbon credits on each submission
(contract-call? .carbon-credits add-credit-minter .waste-tokens)

;; 5. Fund rewards pool with initial sBTC reserve
(contract-call? .rewards-pool fund-pool u100000000)  ;; 100 STX

;; 6. Set initial conversion rate (1,000 tokens = 0.0001 sBTC)
(contract-call? .rewards-pool set-conversion-rate u10000000)
```

### Clarinet Commands

```bash
# Run all tests
clarinet test

# Deploy to testnet
clarinet deployments generate --testnet
clarinet deployments apply --testnet

# Verify on explorer
# https://explorer.hiro.so/?chain=testnet
```

---

## 11. MVP Acceptance Criteria

### Functionality
- [ ] All 5 waste token types mint correctly: plastic, paper, metal, organic, **glass**
- [ ] `"electronic"` returns `err-invalid-waste-type` (u102) — never silently mints
- [ ] Validators can stake, have validations recorded, and unstake
- [ ] Users can claim sBTC rewards (waste tokens burned to zero)
- [ ] Carbon credits mint 1:1 with `carbon-offset-g`
- [ ] Batch mint works for up to 10 submissions per tx

### Security
- [ ] Unauthorized mint attempt: `err-not-authorized` (u101)
- [ ] Unauthorized burn attempt: `err-not-authorized` (u101)
- [ ] Only `contract-owner` can register/remove minters and burners
- [ ] Post-conditions pass on all token transfers

### Integration with Supabase Edge Functions
- [ ] `/mint-tokens` Edge Function can call `mint-waste-token` with all 6 required args
- [ ] `/claim-reward` Edge Function can call `claim-rewards` on behalf of user wallet
- [ ] `record-validation` called and fee paid on every validator decision
- [ ] On-chain `submission-records` entry matches Supabase `submissions` row by ID

### Tests
- [ ] All Clarinet unit tests pass
- [ ] Full mint → claim → zero balance integration test passes
- [ ] `"electronic"` rejection test passes
- [ ] Unauthorized minter rejection test passes

---

*SatsVerdant Contracts PRD v2.0 — March 2026. Supersedes v1.0. Critical change: `electronic-token` removed, `glass-token` added across all match blocks, metadata, and tests. governance.clar moved to Phase 3. All callers updated to Supabase Edge Functions.*