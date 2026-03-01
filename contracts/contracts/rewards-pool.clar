;; title: rewards-pool
;; version: 1.0.0
;; summary: sBTC reward distribution and claiming
;; description: Manages reward pool funding, conversion rates, and sBTC claims

;; Constants
(define-constant contract-owner tx-sender)
(define-constant err-owner-only (err u300))
(define-constant err-not-authorized (err u301))
(define-constant err-insufficient-balance (err u302))
(define-constant err-invalid-amount (err u303))
(define-constant err-claim-not-found (err u304))

;; Data vars
(define-data-var conversion-rate uint u100000) ;; tokens per sBTC (100,000 tokens = 1 sBTC)
(define-data-var total-rewards-distributed uint u0)
(define-data-var total-claims-processed uint u0)

;; Data maps
;; Claim records
(define-map claim-records
  { claim-id: (buff 32) }
  {
    user: principal,
    waste-type: (string-ascii 20),
    token-amount: uint,
    sbtc-amount: uint,
    claimed-at-block: uint,
    status: (string-ascii 20)
  }
)

;; User claim totals
(define-map user-claim-totals
  principal
  {
    total-tokens-burned: uint,
    total-sbtc-claimed: uint,
    claims-count: uint
  }
)

;; Public Functions

;; Fund the rewards pool (admin or donations)
(define-public (fund-pool (amount uint))
  (begin
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    (print { event: "pool-funded", amount: amount, funder: tx-sender })
    (ok true)
  )
)

;; Claim rewards by burning waste tokens
(define-public (claim-rewards
    (claim-id (buff 32))
    (waste-type (string-ascii 20))
    (token-amount uint)
    (user principal)
  )
  (let (
    (sbtc-amount (/ (* token-amount u1000000) (var-get conversion-rate)))
  )
    ;; Only authorized contracts can process claims
    (asserts! (is-eq tx-sender contract-owner) err-not-authorized)
    (asserts! (> token-amount u0) err-invalid-amount)
    
    ;; Record claim
    (map-set claim-records
      { claim-id: claim-id }
      {
        user: user,
        waste-type: waste-type,
        token-amount: token-amount,
        sbtc-amount: sbtc-amount,
        claimed-at-block: stacks-block-height,
        status: "completed"
      }
    )
    
    ;; Update user totals
    (let (
      (user-totals (default-to
        { total-tokens-burned: u0, total-sbtc-claimed: u0, claims-count: u0 }
        (map-get? user-claim-totals user)
      ))
    )
      (map-set user-claim-totals user
        {
          total-tokens-burned: (+ (get total-tokens-burned user-totals) token-amount),
          total-sbtc-claimed: (+ (get total-sbtc-claimed user-totals) sbtc-amount),
          claims-count: (+ (get claims-count user-totals) u1)
        }
      )
    )
    
    ;; Update global stats
    (var-set total-rewards-distributed (+ (var-get total-rewards-distributed) sbtc-amount))
    (var-set total-claims-processed (+ (var-get total-claims-processed) u1))
    
    ;; Transfer sBTC to user (as STX for MVP)
    (try! (as-contract (stx-transfer? sbtc-amount tx-sender user)))
    
    (print { event: "reward-claimed", user: user, token-amount: token-amount, sbtc-amount: sbtc-amount })
    (ok sbtc-amount)
  )
)

;; Admin: Update conversion rate
(define-public (set-conversion-rate (new-rate uint))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (asserts! (> new-rate u0) err-invalid-amount)
    (var-set conversion-rate new-rate)
    (print { event: "conversion-rate-updated", new-rate: new-rate })
    (ok true)
  )
)

;; Admin: Withdraw funds (emergency)
(define-public (withdraw-funds (amount uint) (recipient principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (try! (as-contract (stx-transfer? amount tx-sender recipient)))
    (ok true)
  )
)

;; Read-Only Functions

;; Get pool balance
(define-read-only (get-pool-balance)
  (ok (stx-get-balance (as-contract tx-sender)))
)

;; Get conversion rate
(define-read-only (get-conversion-rate)
  (ok (var-get conversion-rate))
)

;; Get claim record
(define-read-only (get-claim-record (claim-id (buff 32)))
  (ok (map-get? claim-records { claim-id: claim-id }))
)

;; Get user claim totals
(define-read-only (get-user-totals (user principal))
  (ok (map-get? user-claim-totals user))
)

;; Get total rewards distributed
(define-read-only (get-total-distributed)
  (ok (var-get total-rewards-distributed))
)

;; Calculate reward estimate
(define-read-only (estimate-reward (token-amount uint))
  (ok (/ (* token-amount u1000000) (var-get conversion-rate)))
)
