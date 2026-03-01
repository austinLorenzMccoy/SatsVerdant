# SatsVerdant Smart Contracts Deployment Guide

## Overview

This guide covers deploying the three core smart contracts for SatsVerdant to Stacks testnet and mainnet.

## Contracts

1. **waste-tokens.clar** - SIP-010 fungible tokens for 5 waste types
2. **validator-pool.clar** - Validator staking and reputation management
3. **rewards-pool.clar** - sBTC reward distribution

## Prerequisites

- Clarinet installed (`brew install clarinet` or download from Hiro)
- Stacks wallet with testnet/mainnet STX
- Node.js and npm for testing

## Contract Verification

All contracts have been verified to compile successfully:

```bash
cd /Users/a/Documents/stacks/ascent/mvp_folder/contracts
clarinet check
# ✔ 3 contracts checked
```

## Deployment Steps

### 1. Local Testing (Devnet)

```bash
# Start local devnet
clarinet integrate

# Run tests
npm install
npm test
```

### 2. Testnet Deployment

#### Generate Deployment Plan

```bash
clarinet deployments generate --testnet
```

This creates `deployments/default.testnet-plan.yaml`

#### Review and Edit Deployment Plan

Edit the generated plan to set deployment order:
1. waste-tokens (no dependencies)
2. validator-pool (no dependencies)
3. rewards-pool (depends on waste-tokens for burning)

#### Deploy to Testnet

```bash
clarinet deployments apply --testnet
```

This will:
- Deploy all three contracts
- Output contract addresses (e.g., `ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM.waste-tokens`)

### 3. Post-Deployment Configuration

#### Initialize waste-tokens Contract

```bash
# Call initialize-metadata to set up token metadata
stx call <DEPLOYER_ADDRESS>.waste-tokens initialize-metadata
```

#### Add Backend as Authorized Minter

```bash
# Add backend service account as authorized minter
stx call <DEPLOYER_ADDRESS>.waste-tokens add-minter <BACKEND_PRINCIPAL>
```

#### Add rewards-pool as Authorized Burner

```bash
# Allow rewards-pool to burn tokens for redemption
stx call <DEPLOYER_ADDRESS>.waste-tokens add-burner <DEPLOYER_ADDRESS>.rewards-pool
```

#### Fund Rewards Pool

```bash
# Transfer STX to rewards pool for sBTC payouts
stx call <DEPLOYER_ADDRESS>.rewards-pool fund-pool u100000000000
# (100,000 STX = 100,000,000,000 micro-STX)
```

### 4. Update Backend Configuration

Update `backend/.env` with deployed contract addresses:

```env
# Stacks Blockchain Configuration
STACKS_NETWORK=testnet
STACKS_API_URL=https://api.testnet.hiro.so
STACKS_CONTRACT_DEPLOYER=ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM

# Contract Names
STACKS_WASTE_TOKENS_CONTRACT=waste-tokens
STACKS_VALIDATOR_POOL_CONTRACT=validator-pool
STACKS_REWARDS_POOL_CONTRACT=rewards-pool

# Backend Service Account (for minting)
STACKS_BACKEND_PRIVATE_KEY=your_backend_private_key_here
```

### 5. Verify Deployment

#### Check Contract Deployment

```bash
# Verify waste-tokens contract
curl https://api.testnet.hiro.so/v2/contracts/interface/ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM/waste-tokens

# Verify validator-pool contract
curl https://api.testnet.hiro.so/v2/contracts/interface/ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM/validator-pool

# Verify rewards-pool contract
curl https://api.testnet.hiro.so/v2/contracts/interface/ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM/rewards-pool
```

#### Test Read-Only Functions

```bash
# Get token metadata
stx call-read <DEPLOYER>.waste-tokens get-token-metadata "plastic"

# Get total staked in validator pool
stx call-read <DEPLOYER>.validator-pool get-total-staked

# Get rewards pool balance
stx call-read <DEPLOYER>.rewards-pool get-pool-balance
```

## Contract Functions Reference

### waste-tokens.clar

**Admin Functions:**
- `initialize-metadata()` - Set up token metadata (call once)
- `add-minter(principal)` - Authorize backend to mint tokens
- `remove-minter(principal)` - Remove minter authorization
- `add-burner(principal)` - Authorize contract to burn tokens

**Core Functions:**
- `mint-waste-token(waste-type, amount, recipient, submission-id, carbon-offset-g, validator)` - Mint tokens after validation
- `transfer(waste-type, amount, sender, recipient, memo)` - Transfer tokens
- `burn-waste-token(waste-type, amount, owner)` - Burn tokens for rewards

**Read-Only Functions:**
- `get-balance(waste-type, account)` - Get token balance
- `get-total-supply(waste-type)` - Get total supply
- `get-user-stats(user)` - Get user submission stats
- `get-submission-record(submission-id)` - Get submission details

### validator-pool.clar

**Core Functions:**
- `stake-as-validator(amount)` - Stake STX to become validator (min 500 STX)
- `record-validation(submission-id, validator, decision)` - Record validation
- `unstake()` - Unstake and leave validator pool
- `update-reputation(validator, new-score)` - Admin: Update reputation
- `suspend-validator(validator)` - Admin: Suspend validator

**Read-Only Functions:**
- `get-validator(validator)` - Get validator info
- `is-active-validator(validator)` - Check if validator is active
- `get-validation-record(submission-id)` - Get validation record
- `get-total-staked()` - Get total staked amount

### rewards-pool.clar

**Core Functions:**
- `fund-pool(amount)` - Fund rewards pool with STX
- `claim-rewards(claim-id, waste-type, token-amount, user)` - Process reward claim
- `set-conversion-rate(new-rate)` - Admin: Update token-to-sBTC rate
- `withdraw-funds(amount, recipient)` - Admin: Emergency withdrawal

**Read-Only Functions:**
- `get-pool-balance()` - Get pool STX balance
- `get-conversion-rate()` - Get current conversion rate
- `get-claim-record(claim-id)` - Get claim details
- `get-user-totals(user)` - Get user claim totals
- `estimate-reward(token-amount)` - Calculate reward estimate

## Mainnet Deployment

For mainnet deployment, follow the same steps but use `--mainnet` flag:

```bash
clarinet deployments generate --mainnet
clarinet deployments apply --mainnet
```

**Important Mainnet Considerations:**
1. Use a secure hardware wallet for contract deployment
2. Fund rewards pool with sufficient sBTC/STX
3. Set appropriate conversion rates based on market conditions
4. Implement multi-sig for admin functions (post-MVP)
5. Complete security audit before mainnet deployment

## Monitoring

Monitor contract activity using:
- Stacks Explorer: https://explorer.hiro.so/
- Backend logs for transaction confirmations
- Contract event logs for minting, staking, and claims

## Troubleshooting

### Contract Not Found
- Verify contract address and network (testnet vs mainnet)
- Check deployment transaction status

### Unauthorized Errors
- Ensure backend principal is added as authorized minter
- Verify contract-caller permissions for inter-contract calls

### Insufficient Balance
- Check rewards pool has sufficient STX for payouts
- Verify user has sufficient tokens for burning

## Security Notes

1. **Private Keys**: Never commit private keys to version control
2. **Admin Functions**: Restrict to contract owner only
3. **Rate Limiting**: Implement backend rate limiting for minting
4. **Monitoring**: Set up alerts for unusual contract activity
5. **Upgrades**: Plan for contract upgrades via proxy pattern (post-MVP)

## Next Steps

1. Deploy contracts to testnet
2. Test end-to-end flow with backend
3. Run security audit
4. Deploy to mainnet
5. Monitor and iterate based on usage

## Support

For issues or questions:
- Clarity Documentation: https://docs.stacks.co/clarity
- Clarinet Documentation: https://docs.hiro.so/clarinet
- Stacks Discord: https://discord.gg/stacks
