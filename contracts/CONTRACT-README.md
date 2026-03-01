# SatsVerdant Smart Contracts

Production-ready Clarity smart contracts for waste tokenization on Stacks blockchain.

## Contracts

### 1. waste-tokens.clar
SIP-010 compliant fungible tokens for 5 waste types:
- Plastic (PLASTIC)
- Paper (PAPER)
- Metal (METAL)
- Organic (ORGANIC)
- Electronic (EWASTE)

**Features:**
- Minting with audit trail
- Transfer with memo support
- Burning for reward redemption
- User submission tracking
- Authorized minter/burner system

### 2. validator-pool.clar
Validator staking and reputation management.

**Features:**
- STX staking (minimum 500 STX)
- Validation tracking
- Reputation scoring
- Admin controls for suspension
- Unstaking mechanism

### 3. rewards-pool.clar
sBTC reward distribution and claiming.

**Features:**
- Pool funding
- Token-to-sBTC conversion
- Claim processing
- User claim tracking
- Configurable conversion rates

## Quick Start

```bash
# Install dependencies
npm install

# Check contracts
clarinet check

# Run tests
npm test

# Deploy to testnet
clarinet deployments generate --testnet
clarinet deployments apply --testnet
```

## Documentation

- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [Contracts PRD](../docs/SatsVerdant_Contracts_PRD_MVP.md) - Detailed specifications

## Contract Addresses

### Testnet
```
waste-tokens: ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM.waste-tokens
validator-pool: ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM.validator-pool
rewards-pool: ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM.rewards-pool
```

(Update after deployment)

### Mainnet
TBD

## Architecture

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
                └────────────┴────────────┘
                      Backend API
```

## Development

### Prerequisites
- Clarinet 2.0+
- Node.js 18+
- Stacks wallet

### Testing
```bash
# Unit tests
npm test

# Integration tests
clarinet integrate
```

### Linting
Contracts compile with 44 warnings (expected for function parameters). All warnings are related to "potentially unchecked data" which is acceptable for public function parameters in Clarity.

## Security

- All admin functions restricted to contract owner
- Authorization checks for minting and burning
- Input validation on all public functions
- Audit trail for all token operations

## License

MIT
