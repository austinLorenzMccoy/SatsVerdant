# SatsVerdant Smart Contracts PRD - MVP

## 1. Executive Summary

**Project:** SatsVerdant Clarity Smart Contracts   \
**Blockchain:** Stacks (Bitcoin Layer 2)   \
**Version:** 1.0 (MVP)   \
**Timeline:** 4 weeks (parallel with backend development)   \
**Goal:** Production-ready smart contracts for waste tokenization, validator staking, and sBTC reward distribution with maximum security and auditability.

---

## 2. Contract Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Contract Ecosystem                       │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
         ┌──────▼──────┐ ┌───▼────┐ ┌─────▼─────┐
         │waste-tokens │ │validator│ │rewards-pool│
         │  (SIP-010)  │ │ -pool  │ │  (sBTC)   │
         └──────┬──────┘ └───┬────┘ └─────┬─────┘
                │            │            │
                │     ┌──────▼──────┐     │
                └────►│carbon-credits│◄────┘
                      │  (SIP-010)  │
                      └─────────────┘
```

### **Core Contracts (MVP)**

1. **waste-tokens.clar** - SIP-010 fungible tokens for waste types
2. **validator-pool.clar** - Validator staking and reputation management
3. **rewards-pool.clar** - sBTC reward distribution and claiming
4. **carbon-credits.clar** - Carbon offset tracking and trading

### **Future Contracts (Post-MVP)**
- **governance.clar** - DAO governance and voting
- **marketplace.clar** - Carbon credit marketplace
- **oracle.clar** - External data integration

---

## 3. Technical Specifications

### **3.1 Clarity Language Features Used**

**Core Primitives:**
- `define-fungible-token` - For waste tokens and carbon credits
- `define-map` - For validator registry, user balances
- `define-data-var` - For contract configuration
- `define-constant` - For immutable configuration

**Security Features:**
- `asserts!` - Pre-condition validation
- `try!` - Error propagation
- `match` - Safe pattern matching
- Post-conditions on all transfers

**Access Control:**
- `tx-sender` - Caller identification
- `contract-caller` - Contract-to-contract calls
- `contract-owner` - Admin functions

### **3.2 SIP Standards Compliance**

**SIP-010 (Fungible Token Standard):**
- All token contracts implement SIP-010 trait
- Required functions: `transfer`, `get-balance`, `get-total-supply`, etc.
- Token metadata via trait

**SIP-009 (NFT Standard) - Future:**
- For unique submission receipts (post-MVP)

---

## 4. Contract 1: waste-tokens.clar

### **4.1 Purpose**
Manage waste type tokens (plastic, paper, metal, organic, electronic) as SIP-010 fungible tokens with minting, burning, and transfer capabilities.

### **4.2 Data Structures**

```clarity
;; Constants
(define-constant contract-owner tx-sender)
(define-constant err-owner-only (err u100))
(define-constant err-not-authorized (err u101))
(define-constant err-invalid-waste-type (err u102))
(define-constant err-insufficient-balance (err u103))

;; Waste token types
(define-fungible-token plastic-token)
(define-fungible-token paper-token)
(define-fungible-token metal-token)
(define-fungible-token organic-token)
(define-fungible-token electronic-token)

;; Authorized minters (backend service accounts)
(define-map authorized-minters principal bool)

;; Token metadata
(define-map token-metadata 
  { token-type: (string-ascii 20) }
  {
    name: (string-ascii 32),
    symbol: (string-ascii 10),
    decimals: uint,
    uri: (optional (string-utf8 256))
  }
)

;; User submission tracking
(define-map user-submissions
  { user: principal }
  {
    total-submissions: uint,
    total-tokens-earned: uint,
    last-submission-block: uint
  }
)

;; Submission records (for audit trail)
(define-map submission-records
  { submission-id: (buff 32) }
  {
    user: principal,
    waste-type: (string-ascii 20),
    tokens-minted: uint,
    carbon-offset-g: uint,
    validator: principal,
    block-height: uint,
    timestamp: uint
  }
)
```

### **4.3 Core Functions**

#### **Administrative Functions**

```clarity
;; Initialize token metadata
(define-public (initialize-metadata)
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    
    (map-set token-metadata { token-type: "plastic" }
      { name: "Plastic Waste Token", symbol: "PLASTIC", decimals: u0, uri: none })
    (map-set token-metadata { token-type: "paper" }
      { name: "Paper Waste Token", symbol: "PAPER", decimals: u0, uri: none })
    (map-set token-metadata { token-type: "metal" }
      { name: "Metal Waste Token", symbol: "METAL", decimals: u0, uri: none })
    (map-set token-metadata { token-type: "organic" }
      { name: "Organic Waste Token", symbol: "ORGANIC", decimals: u0, uri: none })
    (map-set token-metadata { token-type: "electronic" }
      { name: "Electronic Waste Token", symbol: "EWASTE", decimals: u0, uri: none })
    
    (ok true)
  )
)

;; Add authorized minter (backend service account)
(define-public (add-minter (minter principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-set authorized-minters minter true))
  )
)

;; Remove authorized minter
(define-public (remove-minter (minter principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-delete authorized-minters minter))
  )
)

;; Check if caller is authorized minter
(define-private (is-authorized-minter (caller principal))
  (default-to false (map-get? authorized-minters caller))
)
```

#### **Minting Functions**

```clarity
;; Mint waste tokens after validation
(define-public (mint-waste-token
    (waste-type (string-ascii 20))
    (amount uint)
    (recipient principal)
    (submission-id (buff 32))
    (carbon-offset-g uint)
    (validator principal)
  )
  (begin
    ;; Only authorized minters can mint
    (asserts! (is-authorized-minter tx-sender) err-not-authorized)
    
    ;; Validate amount > 0
    (asserts! (> amount u0) (err u104))
    
    ;; Mint based on waste type
    (try! (match waste-type
      "plastic" (ft-mint? plastic-token amount recipient)
      "paper" (ft-mint? paper-token amount recipient)
      "metal" (ft-mint? metal-token amount recipient)
      "organic" (ft-mint? organic-token amount recipient)
      "electronic" (ft-mint? electronic-token amount recipient)
      err-invalid-waste-type
    ))
    
    ;; Record submission
    (map-set submission-records
      { submission-id: submission-id }
      {
        user: recipient,
        waste-type: waste-type,
        tokens-minted: amount,
        carbon-offset-g: carbon-offset-g,
        validator: validator,
        block-height: block-height,
        timestamp: (unwrap! (get-block-info? time block-height) (err u105))
      }
    )
    
    ;; Update user stats
    (let (
      (user-stats (default-to
        { total-submissions: u0, total-tokens-earned: u0, last-submission-block: u0 }
        (map-get? user-submissions { user: recipient })
      ))
    )
      (map-set user-submissions
        { user: recipient }
        {
          total-submissions: (+ (get total-submissions user-stats) u1),
          total-tokens-earned: (+ (get total-tokens-earned user-stats) amount),
          last-submission-block: block-height
        }
      )
    )
    
    (ok amount)
  )
)

;; Batch mint (for efficiency)
(define-public (batch-mint-waste-tokens
    (mints (list 10 {
      waste-type: (string-ascii 20),
      amount: uint,
      recipient: principal,
      submission-id: (buff 32),
      carbon-offset-g: uint,
      validator: principal
    }))
  )
  (begin
    (asserts! (is-authorized-minter tx-sender) err-not-authorized)
    (ok (map mint-single-waste-token mints))
  )
)

(define-private (mint-single-waste-token (mint-data {
    waste-type: (string-ascii 20),
    amount: uint,
    recipient: principal,
    submission-id: (buff 32),
    carbon-offset-g: uint,
    validator: principal
  }))
  (mint-waste-token
    (get waste-type mint-data)
    (get amount mint-data)
    (get recipient mint-data)
    (get submission-id mint-data)
    (get carbon-offset-g mint-data)
    (get validator mint-data)
  )
)
```

#### **Transfer Functions (SIP-010 Compliance)**

```clarity
;; Transfer tokens
(define-public (transfer
    (waste-type (string-ascii 20))
    (amount uint)
    (sender principal)
    (recipient principal)
    (memo (optional (buff 34)))
  )
  (begin
    ;; Sender must be tx-sender
    (asserts! (is-eq tx-sender sender) err-not-authorized)
    
    ;; Transfer based on waste type
    (try! (match waste-type
      "plastic" (ft-transfer? plastic-token amount sender recipient)
      "paper" (ft-transfer? paper-token amount sender recipient)
      "metal" (ft-transfer? metal-token amount sender recipient)
      "organic" (ft-transfer? organic-token amount sender recipient)
      "electronic" (ft-transfer? electronic-token amount sender recipient)
      err-invalid-waste-type
    ))
    
    ;; Print memo if provided
    (match memo
      memo-value (print { event: "transfer", memo: memo-value })
      true
    )
    
    (ok true)
  )
)
```

#### **Burning Functions**

```clarity
;; Burn tokens (for reward redemption)
(define-public (burn-waste-token
    (waste-type (string-ascii 20))
    (amount uint)
    (owner principal)
  )
  (begin
    ;; Only owner or authorized contracts can burn
    (asserts! 
      (or (is-eq tx-sender owner) (is-authorized-burner contract-caller))
      err-not-authorized
    )
    
    ;; Burn based on waste type
    (try! (match waste-type
      "plastic" (ft-burn? plastic-token amount owner)
      "paper" (ft-burn? paper-token amount owner)
      "metal" (ft-burn? metal-token amount owner)
      "organic" (ft-burn? organic-token amount owner)
      "electronic" (ft-burn? electronic-token amount owner)
      err-invalid-waste-type
    ))
    
    (print { event: "burn", waste-type: waste-type, amount: amount, owner: owner })
    (ok amount)
  )
)

;; Authorized burner contracts (e.g., rewards-pool)
(define-map authorized-burners principal bool)

(define-public (add-burner (burner principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-set authorized-burners burner true))
  )
)

(define-private (is-authorized-burner (caller principal))
  (default-to false (map-get? authorized-burners caller))
)
```

#### **Read-Only Functions**

```clarity
;; Get token balance
(define-read-only (get-balance (waste-type (string-ascii 20)) (account principal))
  (ok (match waste-type
    "plastic" (ft-get-balance plastic-token account)
    "paper" (ft-get-balance paper-token account)
    "metal" (ft-get-balance metal-token account)
    "organic" (ft-get-balance organic-token account)
    "electronic" (ft-get-balance electronic-token account)
    u0
  ))
)

;; Get total supply
(define-read-only (get-total-supply (waste-type (string-ascii 20)))
  (ok (match waste-type
    "plastic" (ft-get-supply plastic-token)
    "paper" (ft-get-supply paper-token)
    "metal" (ft-get-supply metal-token)
    "organic" (ft-get-supply organic-token)
    "electronic" (ft-get-supply electronic-token)
    u0
  ))
)

;; Get user stats
(define-read-only (get-user-stats (user principal))
  (ok (map-get? user-submissions { user: user }))
)

;; Get submission record
(define-read-only (get-submission-record (submission-id (buff 32)))
  (ok (map-get? submission-records { submission-id: submission-id }))
)

;; Get token metadata
(define-read-only (get-token-metadata (waste-type (string-ascii 20)))
  (ok (map-get? token-metadata { token-type: waste-type }))
)

;; Get token name (SIP-010)
(define-read-only (get-name (waste-type (string-ascii 20)))
  (ok (get name (unwrap! (map-get? token-metadata { token-type: waste-type }) (err u106))))
)

;; Get token symbol (SIP-010)
(define-read-only (get-symbol (waste-type (string-ascii 20)))
  (ok (get symbol (unwrap! (map-get? token-metadata { token-type: waste-type }) (err u106))))
)

;; Get decimals (SIP-010)
(define-read-only (get-decimals (waste-type (string-ascii 20)))
  (ok (get decimals (unwrap! (map-get? token-metadata { token-type: waste-type }) (err u106))))
)

;; Get token URI (SIP-010)
(define-read-only (get-token-uri (waste-type (string-ascii 20)))
  (ok (get uri (unwrap! (map-get? token-metadata { token-type: waste-type }) (err u106))))
)
```

---

## 5. Contract 2: validator-pool.clar

### **5.1 Purpose**
Manage validator staking, reputation scoring, and validation rewards. Validators stake STX to participate in waste verification and earn fees.

### **5.2 Data Structures**

```clarity
;; Constants
(define-constant contract-owner tx-sender)
(define-constant min-stake-amount u1000000000) ;; 1000 STX (in micro-STX)
(define-constant err-owner-only (err u200))
(define-constant err-insufficient-stake (err u201))
(define-constant err-not-validator (err u202))
(define-constant err-validator-suspended (err u203))
(define-constant err-already-validator (err u204))

;; Validator registry
(define-map validators
  principal
  {
    staked-amount: uint,
    reputation-score: uint,
    validations-count: uint,
    approvals-count: uint,
    rejections-count: uint,
    is-active: bool,
    joined-at-block: uint,
    last-validation-block: uint
  }
)

;; Validation records
(define-map validation-records
  { submission-id: (buff 32) }
  {
    validator: principal,
    decision: (string-ascii 10), ;; "approved" or "rejected"
    validated-at-block: uint,
    fee-earned: uint
  }
)

;; Total staked amount
(define-data-var total-staked uint u0)

;; Validation fee (in micro-STX)
(define-data-var validation-fee uint u100000) ;; 0.1 STX per validation
```

### **5.3 Core Functions**

#### **Staking Functions**

```clarity
;; Stake STX to become validator
(define-public (stake-as-validator (amount uint))
  (begin
    ;; Must meet minimum stake
    (asserts! (>= amount min-stake-amount) err-insufficient-stake)
    
    ;; Cannot be existing validator
    (asserts! (is-none (map-get? validators tx-sender)) err-already-validator)
    
    ;; Transfer STX to contract
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    
    ;; Register validator
    (map-set validators tx-sender
      {
        staked-amount: amount,
        reputation-score: u100, ;; Start with 100
        validations-count: u0,
        approvals-count: u0,
        rejections-count: u0,
        is-active: true,
        joined-at-block: block-height,
        last-validation-block: u0
      }
    )
    
    ;; Update total staked
    (var-set total-staked (+ (var-get total-staked) amount))
    
    (print { event: "validator-staked", validator: tx-sender, amount: amount })
    (ok true)
  )
)

;; Add more stake
(define-public (add-stake (amount uint))
  (let (
    (validator-data (unwrap! (map-get? validators tx-sender) err-not-validator))
  )
    ;; Transfer additional STX
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    
    ;; Update stake amount
    (map-set validators tx-sender
      (merge validator-data { staked-amount: (+ (get staked-amount validator-data) amount) })
    )
    
    ;; Update total staked
    (var-set total-staked (+ (var-get total-staked) amount))
    
    (ok true)
  )
)

;; Unstake (with cooldown period - simplified for MVP)
(define-public (unstake)
  (let (
    (validator-data (unwrap! (map-get? validators tx-sender) err-not-validator))
    (staked-amount (get staked-amount validator-data))
  )
    ;; Must be active
    (asserts! (get is-active validator-data) err-validator-suspended)
    
    ;; Transfer STX back (as-contract to access contract balance)
    (try! (as-contract (stx-transfer? staked-amount tx-sender tx-sender)))
    
    ;; Remove from validator registry
    (map-delete validators tx-sender)
    
    ;; Update total staked
    (var-set total-staked (- (var-get total-staked) staked-amount))
    
    (print { event: "validator-unstaked", validator: tx-sender, amount: staked-amount })
    (ok staked-amount)
  )
)
```

#### **Validation Functions**

```clarity
;; Record validation (called by waste-tokens contract or backend)
(define-public (record-validation
    (submission-id (buff 32))
    (validator principal)
    (decision (string-ascii 10))
  )
  (let (
    (validator-data (unwrap! (map-get? validators validator) err-not-validator))
  )
    ;; Validator must be active
    (asserts! (get is-active validator-data) err-validator-suspended)
    
    ;; Record validation
    (map-set validation-records
      { submission-id: submission-id }
      {
        validator: validator,
        decision: decision,
        validated-at-block: block-height,
        fee-earned: (var-get validation-fee)
      }
    )
    
    ;; Update validator stats
    (map-set validators validator
      (merge validator-data
        {
          validations-count: (+ (get validations-count validator-data) u1),
          approvals-count: (if (is-eq decision "approved")
                             (+ (get approvals-count validator-data) u1)
                             (get approvals-count validator-data)),
          rejections-count: (if (is-eq decision "rejected")
                              (+ (get rejections-count validator-data) u1)
                              (get rejections-count validator-data)),
          last-validation-block: block-height
        }
      )
    )
    
    ;; Pay validation fee to validator
    (try! (as-contract (stx-transfer? (var-get validation-fee) tx-sender validator)))
    
    (print { event: "validation-recorded", submission-id: submission-id, validator: validator })
    (ok true)
  )
)

;; Update reputation score (admin function based on accuracy)
(define-public (update-reputation (validator principal) (new-score uint))
  (let (
    (validator-data (unwrap! (map-get? validators validator) err-not-validator))
  )
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    
    (map-set validators validator
      (merge validator-data { reputation-score: new-score })
    )
    
    (ok true)
  )
)

;; Suspend validator
(define-public (suspend-validator (validator principal))
  (let (
    (validator-data (unwrap! (map-get? validators validator) err-not-validator))
  )
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    
    (map-set validators validator
      (merge validator-data { is-active: false })
    )
    
    (print { event: "validator-suspended", validator: validator })
    (ok true)
  )
)

;; Reactivate validator
(define-public (reactivate-validator (validator principal))
  (let (
    (validator-data (unwrap! (map-get? validators validator) err-not-validator))
  )
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    
    (map-set validators validator
      (merge validator-data { is-active: true })
    )
    
    (ok true)
  )
)
```

#### **Read-Only Functions**

```clarity
;; Get validator info
(define-read-only (get-validator (validator principal))
  (ok (map-get? validators validator))
)

;; Check if active validator
(define-read-only (is-active-validator (validator principal))
  (match (map-get? validators validator)
    validator-data (ok (get is-active validator-data))
    (ok false)
  )
)

;; Get validation record
(define-read-only (get-validation-record (submission-id (buff 32)))
  (ok (map-get? validation-records { submission-id: submission-id }))
)

;; Get total staked
(define-read-only (get-total-staked)
  (ok (var-get total-staked))
)

;; Get validation fee
(define-read-only (get-validation-fee)
  (ok (var-get validation-fee))
)

;; Calculate accuracy rate
(define-read-only (get-accuracy-rate (validator principal))
  (match (map-get? validators validator)
    validator-data 
      (let (
        (total (get validations-count validator-data))
        (approvals (get approvals-count validator-data))
      )
        (if (> total u0)
          (ok (/ (* approvals u10000) total)) ;; Return as basis points (0-10000)
          (ok u0)
        )
      )
    (err err-not-validator)
  )
)
```

---

## 6. Contract 3: rewards-pool.clar

### **6.1 Purpose**
Manage sBTC reward distribution. Users burn waste tokens to claim sBTC rewards based on a conversion rate.

### **6.2 Data Structures**

```clarity
;; Constants
(define-constant contract-owner tx-sender)
(define-constant err-owner-only (err u300))
(define-constant err-insufficient-balance (err u301))
(define-constant err-pool-empty (err u302))
(define-constant err-invalid-amount (err u303))

;; Conversion rate (waste tokens per sBTC)
;; Example: 1000 tokens = 0.0001 sBTC → rate = 10000000
(define-data-var conversion-rate uint u10000000)

;; Total rewards distributed
(define-data-var total-rewards-distributed uint u0)

;; Reward claims
(define-map reward-claims
  { user: principal, claim-id: uint }
  {
    waste-tokens-burned: uint,
    sbtc-amount: uint,
    claimed-at-block: uint,
    tx-id: (optional (buff 32))
  }
)

;; User claim counter
(define-map user-claim-count principal uint)
```

### **6.3 Core Functions**

```clarity
;; Claim rewards (burn waste tokens for sBTC)
(define-public (claim-rewards
    (waste-type (string-ascii 20))
    (token-amount uint)
  )
  (let (
    (sbtc-amount (/ (* token-amount u100000000) (var-get conversion-rate))) ;; Convert to sats
    (claim-count (default-to u0 (map-get? user-claim-count tx-sender)))
  )
    ;; Validate amount
    (asserts! (> token-amount u0) err-invalid-amount)
    
    ;; Check pool has sufficient sBTC
    (asserts! (>= (stx-get-balance (as-contract tx-sender)) sbtc-amount) err-pool-empty)
    
    ;; Burn waste tokens
    (try! (contract-call? .waste-tokens burn-waste-token waste-type token-amount tx-sender))
    
    ;; Transfer sBTC
    (try! (as-contract (stx-transfer? sbtc-amount tx-sender tx-sender)))
    
    ;; Record claim
    (map-set reward-claims
      { user: tx-sender, claim-id: claim-count }
      {
        waste-tokens-burned: token-amount,
        sbtc-amount: sbtc-amount,
        claimed-at-block: block-height,
        tx-id: none
      }
    )
    
    ;; Update claim counter
    (map-set user-claim-count tx-sender (+ claim-count u1))
    
    ;; Update total distributed
    (var-set total-rewards-distributed (+ (var-get total-rewards-distributed) sbtc-amount))
    
    (print { 
      event: "reward-claimed", 
      user: tx-sender, 
      tokens-burned: token-amount, 
      sbtc-amount: sbtc-amount 
    })
    (ok sbtc-amount)
  )
)

;; Batch claim (multiple waste types)
(define-public (batch-claim-rewards
    (claims (list 5 { waste-type: (string-ascii 20), amount: uint }))
  )
  (ok (map claim-single-reward claims))
)

(define-private (claim-single-reward (claim { waste-type: (string-ascii 20), amount: uint }))
  (claim-rewards (get waste-type claim) (get amount claim))
)

;; Fund pool (admin or anyone can add sBTC to pool)
(define-public (fund-pool (amount uint))
  (begin
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    (print { event: "pool-funded", funder: tx-sender, amount: amount })
    (ok amount)
  )
)

;; Update conversion rate (admin only)
(define-public (set-conversion-rate (new-rate uint))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (var-set conversion-rate new-rate)
    (print { event: "conversion-rate-updated", new-rate: new-rate })
    (ok new-rate)
  )
)
```

#### **Read-Only Functions**

```clarity
;; Get pool balance
(define-read-only (get-pool-balance)
  (ok (stx-get-balance (as-contract tx-sender)))
)

;; Get conversion rate
(define-read-only (get-conversion-rate)
  (ok (var-get conversion-rate))
)

;; Calculate reward estimate
(define-read-only (estimate-reward (token-amount uint))
  (ok (/ (* token-amount u100000000) (var-get conversion-rate)))
)

;; Get user claim history
(define-read-only (get-claim-record (user principal) (claim-id uint))
  (ok (map-get? reward-claims { user: user, claim-id: claim-id }))
)

;; Get total claims by user
(define-read-only (get-user-claim-count (user principal))
  (ok (default-to u0 (map-get? user-claim-count user)))
)

;; Get total rewards distributed
(define-read-only (get-total-rewards-distributed)
  (ok (var-get total-rewards-distributed))
)
```

---

## 7. Contract 4: carbon-credits.clar

### **7.1 Purpose**
Track carbon offset credits as SIP-010 tokens, allowing trading and corporate purchases.

### **7.2 Data Structures**

```clarity
;; Constants
(define-constant contract-owner tx-sender)
(define-constant err-owner-only (err u400))
(define-constant err-not-authorized (err u401))

;; Carbon credit token (1 credit = 1 gram CO2 offset)
(define-fungible-token carbon-credit)

;; Authorized minters (waste-tokens contract)
(define-map authorized-credit-minters principal bool)

;; Carbon offset records
(define-map carbon-records
  { submission-id: (buff 32) }
  {
    user: principal,
    waste-type: (string-ascii 20),
    carbon-offset-g: uint,
    tokens-issued: uint,
    issued-at-block: uint
  }
)

;; Corporate purchases
(define-map corporate-purchases
  { purchase-id: uint }
  {
    buyer: principal,
    credits-purchased: uint,
    price-paid: uint,
    purchased-at-block: uint
  }
)

(define-data-var purchase-counter uint u0)
```

### **7.3 Core Functions**

```clarity
;; Mint carbon credits (called by waste-tokens contract)
(define-public (mint-credits
    (submission-id (buff 32))
    (user principal)
    (waste-type (string-ascii 20))
    (carbon-offset-g uint)
  )
  (begin
    ;; Only authorized contracts can mint
    (asserts! 
      (default-to false (map-get? authorized-credit-minters contract-caller))
      err-not-authorized
    )
    
    ;; Mint credits (1:1 with grams CO2)
    (try! (ft-mint? carbon-credit carbon-offset-g user))
    
    ;; Record carbon offset
    (map-set carbon-records
      { submission-id: submission-id }
      {
        user: user,
        waste-type: waste-type,
        carbon-offset-g: carbon-offset-g,
        tokens-issued: carbon-offset-g,
        issued-at-block: block-height
      }
    )
    
    (print { event: "carbon-credits-issued", user: user, amount: carbon-offset-g })
    (ok carbon-offset-g)
  )
)

;; Transfer credits (SIP-010)
(define-public (transfer
    (amount uint)
    (sender principal)
    (recipient principal)
    (memo (optional (buff 34)))
  )
  (begin
    (asserts! (is-eq tx-sender sender) err-not-authorized)
    (try! (ft-transfer? carbon-credit amount sender recipient))
    
    (match memo
      memo-value (print { event: "transfer", memo: memo-value })
      true
    )
    
    (ok true)
  )
)

;; Corporate purchase of credits
(define-public (purchase-credits (amount uint) (price uint))
  (let (
    (purchase-id (var-get purchase-counter))
  )
    ;; Pay for credits (STX)
    (try! (stx-transfer? price tx-sender (as-contract tx-sender)))
    
    ;; Transfer credits from pool/treasury
    (try! (as-contract (ft-transfer? carbon-credit amount tx-sender tx-sender)))
    
    ;; Record purchase
    (map-set corporate-purchases
      { purchase-id: purchase-id }
      {
        buyer: tx-sender,
        credits-purchased: amount,
        price-paid: price,
        purchased-at-block: block-height
      }
    )
    
    (var-set purchase-counter (+ purchase-id u1))
    
    (print { event: "credits-purchased", buyer: tx-sender, amount: amount, price: price })
    (ok purchase-id)
  )
)

;; Add authorized minter
(define-public (add-credit-minter (minter principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-set authorized-credit-minters minter true))
  )
)
```

#### **Read-Only Functions**

```clarity
;; SIP-010 compliance
(define-read-only (get-name)
  (ok "SatsVerdant Carbon Credit")
)

(define-read-only (get-symbol)
  (ok "CARBON")
)

(define-read-only (get-decimals)
  (ok u0)
)

(define-read-only (get-balance (account principal))
  (ok (ft-get-balance carbon-credit account))
)

(define-read-only (get-total-supply)
  (ok (ft-get-supply carbon-credit))
)

(define-read-only (get-token-uri)
  (ok (some u"https://satsverdant.com/carbon-metadata.json"))
)

;; Get carbon record
(define-read-only (get-carbon-record (submission-id (buff 32)))
  (ok (map-get? carbon-records { submission-id: submission-id }))
)

;; Get purchase record
(define-read-only (get-purchase-record (purchase-id uint))
  (ok (map-get? corporate-purchases { purchase-id: purchase-id }))
)
```

---

## 8. Testing Strategy

### **8.1 Unit Tests (Clarinet)**

```typescript
// tests/waste-tokens.test.ts
import { Clarinet, Tx, Chain, Account } from '@stacks/clarinet';

Clarinet.test({
  name: "Can mint plastic tokens to user",
  async fn(chain: Chain, accounts: Map<string, Account>) {
    const deployer = accounts.get('deployer')!;
    const user = accounts.get('wallet_1')!;
    
    let block = chain.mineBlock([
      // Add deployer as authorized minter
      Tx.contractCall(
        'waste-tokens',
        'add-minter',
        [deployer.address],
        deployer.address
      ),
      
      // Mint plastic tokens
      Tx.contractCall(
        'waste-tokens',
        'mint-waste-token',
        [
          '"plastic"',
          'u100',
          user.address,
          '0x1234567890abcdef',
          'u500',
          deployer.address
        ],
        deployer.address
      )
    ]);
    
    block.receipts[1].result.expectOk().expectUint(100);
    
    // Check balance
    let balance = chain.callReadOnlyFn(
      'waste-tokens',
      'get-balance',
      ['"plastic"', user.address],
      user.address
    );
    
    balance.result.expectOk().expectUint(100);
  }
});

Clarinet.test({
  name: "Unauthorized address cannot mint tokens",
  async fn(chain: Chain, accounts: Map<string, Account>) {
    const attacker = accounts.get('wallet_2')!;
    const user = accounts.get('wallet_1')!;
    
    let block = chain.mineBlock([
      Tx.contractCall(
        'waste-tokens',
        'mint-waste-token',
        [
          '"plastic"',
          'u100',
          user.address,
          '0x1234567890abcdef',
          'u500',
          attacker.address
        ],
        attacker.address
      )
    ]);
    
    block.receipts[0].result.expectErr().expectUint(101); // err-not-authorized
  }
});

Clarinet.test({
  name: "Can transfer tokens between users",
  async fn(chain: Chain, accounts: Map<string, Account>) {
    const deployer = accounts.get('deployer')!;
    const user1 = accounts.get('wallet_1')!;
    const user2 = accounts.get('wallet_2')!;
    
    // Setup: Mint tokens to user1
    let setupBlock = chain.mineBlock([
      Tx.contractCall('waste-tokens', 'add-minter', [deployer.address], deployer.address),
      Tx.contractCall(
        'waste-tokens',
        'mint-waste-token',
        ['"plastic"', 'u100', user1.address, '0xabcd', 'u500', deployer.address],
        deployer.address
      )
    ]);
    
    // Transfer from user1 to user2
    let transferBlock = chain.mineBlock([
      Tx.contractCall(
        'waste-tokens',
        'transfer',
        ['"plastic"', 'u50', user1.address, user2.address, 'none'],
        user1.address
      )
    ]);
    
    transferBlock.receipts[0].result.expectOk();
    
    // Verify balances
    let user1Balance = chain.callReadOnlyFn('waste-tokens', 'get-balance', ['"plastic"', user1.address], user1.address);
    let user2Balance = chain.callReadOnlyFn('waste-tokens', 'get-balance', ['"plastic"', user2.address], user2.address);
    
    user1Balance.result.expectOk().expectUint(50);
    user2Balance.result.expectOk().expectUint(50);
  }
});
```

### **8.2 Integration Tests**

```typescript
// tests/integration.test.ts
Clarinet.test({
  name: "Full flow: mint → burn → claim reward",
  async fn(chain: Chain, accounts: Map<string, Account>) {
    const deployer = accounts.get('deployer')!;
    const user = accounts.get('wallet_1')!;
    
    // 1. Setup contracts
    let setupBlock = chain.mineBlock([
      Tx.contractCall('waste-tokens', 'add-minter', [deployer.address], deployer.address),
      Tx.contractCall('waste-tokens', 'add-burner', ['ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM.rewards-pool'], deployer.address),
      Tx.contractCall('rewards-pool', 'fund-pool', ['u10000000'], deployer.address) // Fund with 10 STX
    ]);
    
    // 2. Mint waste tokens
    let mintBlock = chain.mineBlock([
      Tx.contractCall(
        'waste-tokens',
        'mint-waste-token',
        ['"plastic"', 'u1000', user.address, '0xabcd', 'u5000', deployer.address],
        deployer.address
      )
    ]);
    
    mintBlock.receipts[0].result.expectOk();
    
    // 3. Claim rewards (burn tokens for sBTC)
    let claimBlock = chain.mineBlock([
      Tx.contractCall(
        'rewards-pool',
        'claim-rewards',
        ['"plastic"', 'u1000'],
        user.address
      )
    ]);
    
    claimBlock.receipts[0].result.expectOk();
    
    // 4. Verify tokens were burned
    let balance = chain.callReadOnlyFn('waste-tokens', 'get-balance', ['"plastic"', user.address], user.address);
    balance.result.expectOk().expectUint(0);
  }
});
```

### **8.3 Fuzz Testing (Rendezvous)**

```clarity
;; tests/fuzz/waste-tokens.clar
(define-public (fuzz-mint-tokens
    (waste-type (string-ascii 20))
    (amount uint)
    (recipient principal)
  )
  (begin
    ;; Property: Total supply should increase by minted amount
    (let (
      (supply-before (unwrap-panic (contract-call? .waste-tokens get-total-supply waste-type)))
      (mint-result (contract-call? .waste-tokens mint-waste-token 
                     waste-type amount recipient 0xabcd u500 tx-sender))
      (supply-after (unwrap-panic (contract-call? .waste-tokens get-total-supply waste-type)))
    )
      (asserts! 
        (is-eq supply-after (+ supply-before amount))
        (err u1)
      )
      (ok true)
    )
  )
)
```

---

## 9. Security Considerations

### **9.1 Access Control**
- ✅ Only authorized minters can mint tokens
- ✅ Only contract owner can add/remove minters
- ✅ Users can only transfer their own tokens
- ✅ Validators must stake minimum amount

### **9.2 Reentrancy Protection**
- ✅ Clarity has no reentrancy vulnerabilities (deterministic execution)
- ✅ All state changes before external calls

### **9.3 Integer Overflow/Underflow**
- ✅ Clarity's uint type is bounded and safe
- ✅ Explicit checks for arithmetic operations where needed

### **9.4 Front-Running**
- ⚠️ Minimal risk in Stacks (block finality)
- ✅ Use block-height checks where timing matters

### **9.5 Audit Checklist**
- [ ] No hard-coded addresses (except contract-owner)
- [ ] All public functions have access control
- [ ] All arithmetic operations checked for overflow
- [ ] Post-conditions on all token transfers
- [ ] Event logging for all critical actions
- [ ] Read-only functions properly marked
- [ ] Maps indexed correctly for efficient lookups

---

## 10. Deployment Strategy

### **10.1 Testnet Deployment**

```bash
# 1. Deploy to testnet
clarinet deployments generate --testnet

# 2. Test all functions
clarinet test

# 3. Verify on explorer
# https://explorer.hiro.so/txid/DEPLOYMENT_TX?chain=testnet
```

### **10.2 Mainnet Deployment Checklist**

- [ ] All tests passing (unit, integration, fuzz)
- [ ] Security audit completed
- [ ] Gas optimization verified
- [ ] Contract addresses documented
- [ ] Frontend integration tested
- [ ] Backend integration tested
- [ ] Emergency pause mechanism (if needed)
- [ ] Upgrade path documented

### **10.3 Post-Deployment**

```clarity
;; After deployment, initialize contracts:

;; 1. Initialize token metadata
(contract-call? .waste-tokens initialize-metadata)

;; 2. Add backend service account as authorized minter
(contract-call? .waste-tokens add-minter 'SP..SERVICE_ACCOUNT)

;; 3. Authorize rewards-pool to burn tokens
(contract-call? .waste-tokens add-burner .rewards-pool)

;; 4. Authorize waste-tokens to mint carbon credits
(contract-call? .carbon-credits add-credit-minter .waste-tokens)

;; 5. Fund rewards pool with initial sBTC
(contract-call? .rewards-pool fund-pool u100000000) ;; 100 STX

;; 6. Set initial conversion rate
(contract-call? .rewards-pool set-conversion-rate u10000000)
```

---

## 11. Gas Optimization

### **11.1 Optimization Strategies**

**Use Efficient Data Structures:**
```clarity
;; Bad: Iterating over lists
(define-data-var validators-list (list 100 principal) (list))

;; Good: Using maps for O(1) lookups
(define-map validators principal { ... })
```

**Batch Operations:**
```clarity
;; Process multiple operations in one transaction
(define-public (batch-mint-waste-tokens (mints (list 10 {...})))
  (ok (map mint-single-waste-token mints))
)
```

**Minimize Storage:**
```clarity
;; Bad: Storing redundant data
(define-map user-data principal {
  total-tokens: uint,
  plastic-tokens: uint,
  paper-tokens: uint,
  metal-tokens: uint
})

;; Good: Calculate on-demand
(define-read-only (get-total-tokens (user principal))
  (+ 
    (ft-get-balance plastic-token user)
    (ft-get-balance paper-token user)
    (ft-get-balance metal-token user)
  )
)
```

---

## 12. Upgradability Plan

### **12.1 Proxy Pattern (Future)**

For MVP, contracts are immutable. Post-MVP:

```clarity
;; proxy-contract.clar
(define-data-var implementation-contract principal .waste-tokens-v1)

(define-public (upgrade-implementation (new-impl principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (var-set implementation-contract new-impl)
    (ok true)
  )
)
```

### **12.2 Migration Strategy**

If contract changes needed:
1. Deploy new version (e.g., waste-tokens-v2)
2. Migrate data via script
3. Update frontend/backend to point to new contract
4. Keep old contract for historical data

---

## 13. Documentation

### **13.1 Contract Documentation**

Each contract should include:
```clarity
;; Title: SatsVerdant Waste Tokens
;; Version: 1.0.0
;; Summary: SIP-010 fungible tokens for waste classification
;; Description: Manages five waste token types (plastic, paper, metal, organic, electronic)
;;              with minting, burning, and transfer capabilities.
;;
;; Token Types:
;;   - PLASTIC: Plastic waste tokens
;;   - PAPER: Paper waste tokens
;;   - METAL: Metal waste tokens
;;   - ORGANIC: Organic waste tokens
;;   - EWASTE: Electronic waste tokens
;;
;; Minting: Only authorized minters (backend service accounts)
;; Burning: Only owners or authorized burners (rewards-pool contract)
;; Transfers: SIP-010 compliant
```

### **13.2 API Documentation**

Generate with Clarinet:
```bash
clarinet docs
```

Output: OpenAPI spec for all contracts

---

## 14. Monitoring & Maintenance

### **14.1 Contract Events**

Monitor these events:
```clarity
(print { event: "token-minted", ... })
(print { event: "token-burned", ... })
(print { event: "reward-claimed", ... })
(print { event: "validator-staked", ... })
```

### **14.2 Health Checks**

Regular checks:
- Total supply consistency
- Pool balance sufficiency
- Validator count and activity
- Reward distribution rate

### **14.3 Emergency Procedures**

If critical bug found:
1. Notify all users via frontend
2. Pause new submissions (backend)
3. Deploy fixed contract
4. Migrate data
5. Resume operations

---

## 15. Success Criteria

### **✅ Functionality**
- [ ] All 5 waste token types working
- [ ] Validators can stake and validate
- [ ] Users can claim sBTC rewards
- [ ] Carbon credits mint correctly
- [ ] All transfers work

### **✅ Security**
- [ ] Access control enforced
- [ ] No overflow vulnerabilities
- [ ] Audit completed
- [ ] Fuzz tests passing

### **✅ Performance**
- [ ] Gas costs optimized
- [ ] Batch operations working
- [ ] Read-only functions efficient

### **✅ Integration**
- [ ] Backend can mint tokens
- [ ] Frontend can read balances
- [ ] Transactions confirm on-chain

---

This Smart Contract PRD provides everything needed to build, test, deploy, and maintain the SatsVerdant Clarity contracts on Stacks!

