;; title: validator-pool
;; version: 1.0.0
;; summary: Validator staking and reputation management
;; description: Manages validator registration, staking, and validation tracking

;; Constants
(define-constant contract-owner tx-sender)
(define-constant min-stake-amount u500000000) ;; 500 STX (in micro-STX)
(define-constant err-owner-only (err u200))
(define-constant err-insufficient-stake (err u201))
(define-constant err-not-validator (err u202))
(define-constant err-validator-suspended (err u203))
(define-constant err-already-validator (err u204))

;; Data vars
(define-data-var total-staked uint u0)
(define-data-var validation-fee uint u100000) ;; 0.1 STX per validation

;; Data maps
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

(define-map validation-records
  { submission-id: (buff 32) }
  {
    validator: principal,
    decision: (string-ascii 10),
    validated-at-block: uint,
    fee-earned: uint
  }
)

;; Public Functions

;; Stake STX to become validator
(define-public (stake-as-validator (amount uint))
  (begin
    (asserts! (>= amount min-stake-amount) err-insufficient-stake)
    (asserts! (is-none (map-get? validators tx-sender)) err-already-validator)
    
    (try! (stx-transfer? amount tx-sender (as-contract tx-sender)))
    
    (map-set validators tx-sender
      {
        staked-amount: amount,
        reputation-score: u100,
        validations-count: u0,
        approvals-count: u0,
        rejections-count: u0,
        is-active: true,
        joined-at-block: stacks-block-height,
        last-validation-block: u0
      }
    )
    
    (var-set total-staked (+ (var-get total-staked) amount))
    (print { event: "validator-staked", validator: tx-sender, amount: amount })
    (ok true)
  )
)

;; Record validation
(define-public (record-validation
    (submission-id (buff 32))
    (validator principal)
    (decision (string-ascii 10))
  )
  (let (
    (validator-data (unwrap! (map-get? validators validator) err-not-validator))
  )
    (asserts! (get is-active validator-data) err-validator-suspended)
    
    (map-set validation-records
      { submission-id: submission-id }
      {
        validator: validator,
        decision: decision,
        validated-at-block: stacks-block-height,
        fee-earned: (var-get validation-fee)
      }
    )
    
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
          last-validation-block: stacks-block-height
        }
      )
    )
    
    (ok true)
  )
)

;; Unstake and leave validator pool
(define-public (unstake)
  (let (
    (validator-data (unwrap! (map-get? validators tx-sender) err-not-validator))
    (staked-amount (get staked-amount validator-data))
  )
    (try! (as-contract (stx-transfer? staked-amount tx-sender tx-sender)))
    (map-delete validators tx-sender)
    (var-set total-staked (- (var-get total-staked) staked-amount))
    (ok staked-amount)
  )
)

;; Admin: Update reputation
(define-public (update-reputation (validator principal) (new-score uint))
  (let (
    (validator-data (unwrap! (map-get? validators validator) err-not-validator))
  )
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (map-set validators validator (merge validator-data { reputation-score: new-score }))
    (ok true)
  )
)

;; Admin: Suspend validator
(define-public (suspend-validator (validator principal))
  (let (
    (validator-data (unwrap! (map-get? validators validator) err-not-validator))
  )
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (map-set validators validator (merge validator-data { is-active: false }))
    (ok true)
  )
)

;; Read-Only Functions

(define-read-only (get-validator (validator principal))
  (ok (map-get? validators validator))
)

(define-read-only (is-active-validator (validator principal))
  (match (map-get? validators validator)
    validator-data (ok (get is-active validator-data))
    (ok false)
  )
)

(define-read-only (get-validation-record (submission-id (buff 32)))
  (ok (map-get? validation-records { submission-id: submission-id }))
)

(define-read-only (get-total-staked)
  (ok (var-get total-staked))
)
