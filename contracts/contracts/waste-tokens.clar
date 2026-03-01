;; title: waste-tokens
;; version: 1.0.0
;; summary: SIP-010 fungible tokens for waste types (plastic, paper, metal, organic, electronic)
;; description: Manages waste token minting, burning, and transfers with audit trail

;; Constants
(define-constant contract-owner tx-sender)
(define-constant err-owner-only (err u100))
(define-constant err-not-authorized (err u101))
(define-constant err-invalid-waste-type (err u102))
(define-constant err-insufficient-balance (err u103))
(define-constant err-invalid-amount (err u104))
(define-constant err-metadata-not-found (err u106))

;; Token definitions for each waste type
(define-fungible-token plastic-token)
(define-fungible-token paper-token)
(define-fungible-token metal-token)
(define-fungible-token organic-token)
(define-fungible-token electronic-token)

;; Data maps
;; Authorized minters (backend service accounts)
(define-map authorized-minters principal bool)

;; Authorized burners (rewards-pool contract)
(define-map authorized-burners principal bool)

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

;; Submission records (audit trail)
(define-map submission-records
  { submission-id: (buff 32) }
  {
    user: principal,
    waste-type: (string-ascii 20),
    tokens-minted: uint,
    carbon-offset-g: uint,
    validator: principal,
    block-height: uint
  }
)

;; Administrative Functions

;; Initialize token metadata (call once after deployment)
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

;; Add authorized burner (rewards-pool contract)
(define-public (add-burner (burner principal))
  (begin
    (asserts! (is-eq tx-sender contract-owner) err-owner-only)
    (ok (map-set authorized-burners burner true))
  )
)

;; Minting Functions

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
    (asserts! (> amount u0) err-invalid-amount)
    
    ;; Mint based on waste type
    (try! (if (is-eq waste-type "plastic")
      (ft-mint? plastic-token amount recipient)
      (if (is-eq waste-type "paper")
        (ft-mint? paper-token amount recipient)
        (if (is-eq waste-type "metal")
          (ft-mint? metal-token amount recipient)
          (if (is-eq waste-type "organic")
            (ft-mint? organic-token amount recipient)
            (if (is-eq waste-type "electronic")
              (ft-mint? electronic-token amount recipient)
              err-invalid-waste-type
            )
          )
        )
      )
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
        block-height: stacks-block-height
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
          last-submission-block: stacks-block-height
        }
      )
    )
    
    (print { event: "mint", waste-type: waste-type, amount: amount, recipient: recipient, submission-id: submission-id })
    (ok amount)
  )
)

;; Transfer Functions (SIP-010 Compliance)

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
    (try! (if (is-eq waste-type "plastic")
      (ft-transfer? plastic-token amount sender recipient)
      (if (is-eq waste-type "paper")
        (ft-transfer? paper-token amount sender recipient)
        (if (is-eq waste-type "metal")
          (ft-transfer? metal-token amount sender recipient)
          (if (is-eq waste-type "organic")
            (ft-transfer? organic-token amount sender recipient)
            (if (is-eq waste-type "electronic")
              (ft-transfer? electronic-token amount sender recipient)
              err-invalid-waste-type
            )
          )
        )
      )
    ))
    
    ;; Print memo if provided
    (match memo
      memo-value (begin (print { event: "transfer", memo: memo-value }) (ok true))
      (ok true)
    )
  )
)

;; Burning Functions

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
    (try! (if (is-eq waste-type "plastic")
      (ft-burn? plastic-token amount owner)
      (if (is-eq waste-type "paper")
        (ft-burn? paper-token amount owner)
        (if (is-eq waste-type "metal")
          (ft-burn? metal-token amount owner)
          (if (is-eq waste-type "organic")
            (ft-burn? organic-token amount owner)
            (if (is-eq waste-type "electronic")
              (ft-burn? electronic-token amount owner)
              err-invalid-waste-type
            )
          )
        )
      )
    ))
    
    (print { event: "burn", waste-type: waste-type, amount: amount, owner: owner })
    (ok amount)
  )
)

;; Read-Only Functions

;; Get token balance
(define-read-only (get-balance (waste-type (string-ascii 20)) (account principal))
  (ok (if (is-eq waste-type "plastic")
    (ft-get-balance plastic-token account)
    (if (is-eq waste-type "paper")
      (ft-get-balance paper-token account)
      (if (is-eq waste-type "metal")
        (ft-get-balance metal-token account)
        (if (is-eq waste-type "organic")
          (ft-get-balance organic-token account)
          (if (is-eq waste-type "electronic")
            (ft-get-balance electronic-token account)
            u0
          )
        )
      )
    )
  ))
)

;; Get total supply
(define-read-only (get-total-supply (waste-type (string-ascii 20)))
  (ok (if (is-eq waste-type "plastic")
    (ft-get-supply plastic-token)
    (if (is-eq waste-type "paper")
      (ft-get-supply paper-token)
      (if (is-eq waste-type "metal")
        (ft-get-supply metal-token)
        (if (is-eq waste-type "organic")
          (ft-get-supply organic-token)
          (if (is-eq waste-type "electronic")
            (ft-get-supply electronic-token)
            u0
          )
        )
      )
    )
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
  (ok (get name (unwrap! (map-get? token-metadata { token-type: waste-type }) err-metadata-not-found)))
)

;; Get token symbol (SIP-010)
(define-read-only (get-symbol (waste-type (string-ascii 20)))
  (ok (get symbol (unwrap! (map-get? token-metadata { token-type: waste-type }) err-metadata-not-found)))
)

;; Get decimals (SIP-010)
(define-read-only (get-decimals (waste-type (string-ascii 20)))
  (ok (get decimals (unwrap! (map-get? token-metadata { token-type: waste-type }) err-metadata-not-found)))
)

;; Get token URI (SIP-010)
(define-read-only (get-token-uri (waste-type (string-ascii 20)))
  (ok (get uri (unwrap! (map-get? token-metadata { token-type: waste-type }) err-metadata-not-found)))
)

;; Private Functions

;; Check if caller is authorized minter
(define-private (is-authorized-minter (caller principal))
  (default-to false (map-get? authorized-minters caller))
)

;; Check if caller is authorized burner
(define-private (is-authorized-burner (caller principal))
  (default-to false (map-get? authorized-burners caller))
)
