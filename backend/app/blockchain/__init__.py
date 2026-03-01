import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings


class StacksRPCClient:
    """Client for interacting with Stacks blockchain RPC."""

    def __init__(self):
        self.base_url = settings.STACKS_API_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_account_balance(self, address: str) -> Dict[str, Any]:
        """Get account balance."""
        url = f"{self.base_url}/extended/v1/address/{address}/balances"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_transaction(self, tx_id: str) -> Dict[str, Any]:
        """Get transaction details."""
        url = f"{self.base_url}/extended/v1/tx/{tx_id}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def broadcast_transaction(self, tx_hex: str) -> Dict[str, Any]:
        """Broadcast transaction to network."""
        url = f"{self.base_url}/v2/transactions"
        headers = {"Content-Type": "application/octet-stream"}
        response = await self.client.post(url, content=bytes.fromhex(tx_hex), headers=headers)
        response.raise_for_status()
        return response.json()

    async def get_contract_info(self, contract_address: str) -> Dict[str, Any]:
        """Get contract information."""
        url = f"{self.base_url}/extended/v1/contract/{contract_address}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def call_read_only_function(
        self,
        contract_address: str,
        function_name: str,
        function_args: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Call read-only contract function."""
        url = f"{self.base_url}/v2/contracts/call-read/{contract_address}/{function_name}"
        payload = {"arguments": function_args}
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


class WasteTokensContract:
    """Wrapper for waste-tokens.clar contract interactions."""

    def __init__(self, rpc_client: StacksRPCClient):
        self.rpc = rpc_client
        self.contract_address = f"{settings.STACKS_CONTRACT_DEPLOYER}.waste-tokens"

    async def get_balance(self, token_type: str, account: str) -> int:
        """Get token balance for account."""
        try:
            result = await self.rpc.call_read_only_function(
                self.contract_address,
                "get-balance",
                [
                    {"type": "string-ascii", "value": token_type},
                    {"type": "principal", "value": account}
                ]
            )
            return int(result["result"]["value"]["value"])
        except Exception:
            return 0

    async def get_total_supply(self, token_type: str) -> int:
        """Get total supply of token type."""
        try:
            result = await self.rpc.call_read_only_function(
                self.contract_address,
                "get-total-supply",
                [{"type": "string-ascii", "value": token_type}]
            )
            return int(result["result"]["value"]["value"])
        except Exception:
            return 0

    def prepare_mint_transaction(
        self,
        waste_type: str,
        amount: int,
        recipient: str,
        submission_id: str,
        carbon_offset_g: int,
        validator: str
    ) -> Dict[str, Any]:
        """
        Prepare mint transaction data.
        In production, this would create actual Stacks transaction.
        """
        return {
            "contract_address": self.contract_address,
            "function_name": "mint-waste-token",
            "function_args": [
                {"type": "string-ascii", "value": waste_type},
                {"type": "uint", "value": amount},
                {"type": "principal", "value": recipient},
                {"type": "buff", "value": submission_id.encode().hex()},
                {"type": "uint", "value": carbon_offset_g},
                {"type": "principal", "value": validator}
            ]
        }


class ValidatorPoolContract:
    """Wrapper for validator-pool.clar contract interactions."""

    def __init__(self, rpc_client: StacksRPCClient):
        self.rpc = rpc_client
        self.contract_address = f"{settings.STACKS_CONTRACT_DEPLOYER}.validator-pool"

    async def get_validator_info(self, validator_address: str) -> Optional[Dict[str, Any]]:
        """Get validator information."""
        try:
            result = await self.rpc.call_read_only_function(
                self.contract_address,
                "get-validator",
                [{"type": "principal", "value": validator_address}]
            )
            if result["result"]["type"] == "some":
                return result["result"]["value"]["value"]
            return None
        except Exception:
            return None

    async def is_active_validator(self, validator_address: str) -> bool:
        """Check if address is an active validator."""
        try:
            result = await self.rpc.call_read_only_function(
                self.contract_address,
                "is-active-validator",
                [{"type": "principal", "value": validator_address}]
            )
            return result["result"]["value"]["value"]
        except Exception:
            return False

    def prepare_stake_transaction(self, amount: int) -> Dict[str, Any]:
        """Prepare stake transaction data."""
        return {
            "contract_address": self.contract_address,
            "function_name": "stake-as-validator",
            "function_args": [{"type": "uint", "value": amount}]
        }


class RewardsPoolContract:
    """Wrapper for rewards-pool.clar contract interactions."""

    def __init__(self, rpc_client: StacksRPCClient):
        self.rpc = rpc_client
        self.contract_address = f"{settings.STACKS_CONTRACT_DEPLOYER}.rewards-pool"

    async def get_pool_balance(self) -> int:
        """Get rewards pool balance."""
        try:
            account_info = await self.rpc.get_account_balance(self.contract_address)
            return int(account_info["stx"]["balance"])
        except Exception:
            return 0

    async def get_conversion_rate(self) -> int:
        """Get current conversion rate."""
        try:
            result = await self.rpc.call_read_only_function(
                self.contract_address,
                "get-conversion-rate",
                []
            )
            return int(result["result"]["value"]["value"])
        except Exception:
            return 100000  # Default fallback

    def prepare_claim_transaction(self, waste_type: str, token_amount: int) -> Dict[str, Any]:
        """Prepare claim transaction data."""
        return {
            "contract_address": self.contract_address,
            "function_name": "claim-rewards",
            "function_args": [
                {"type": "string-ascii", "value": waste_type},
                {"type": "uint", "value": token_amount}
            ]
        }


class BlockchainService:
    """Main blockchain service coordinating all contract interactions."""

    def __init__(self):
        self.rpc_client = StacksRPCClient()
        self.waste_tokens = WasteTokensContract(self.rpc_client)
        self.validator_pool = ValidatorPoolContract(self.rpc_client)
        self.rewards_pool = RewardsPoolContract(self.rpc_client)

    async def initialize(self):
        """Initialize the service."""
        pass

    async def close(self):
        """Close connections."""
        await self.rpc_client.client.aclose()

    async def mint_waste_tokens(
        self,
        waste_type: str,
        amount: int,
        recipient: str,
        submission_id: str,
        carbon_offset_g: int,
        validator: str
    ) -> Dict[str, Any]:
        """
        Mint waste tokens for a validated submission.
        Returns transaction data (in production, would broadcast).
        """
        tx_data = self.waste_tokens.prepare_mint_transaction(
            waste_type, amount, recipient, submission_id, carbon_offset_g, validator
        )

        # In MVP, just return transaction data
        # In production: sign and broadcast transaction
        return {
            "tx_data": tx_data,
            "estimated_gas": 50000,
            "status": "prepared"
        }

    async def stake_as_validator(self, validator_address: str, amount: int) -> Dict[str, Any]:
        """
        Stake STX to become a validator.
        """
        tx_data = self.validator_pool.prepare_stake_transaction(amount)

        return {
            "tx_data": tx_data,
            "estimated_gas": 30000,
            "status": "prepared"
        }

    async def claim_rewards(self, waste_type: str, token_amount: int) -> Dict[str, Any]:
        """
        Claim sBTC rewards by burning waste tokens.
        """
        tx_data = self.rewards_pool.prepare_claim_transaction(waste_type, token_amount)

        return {
            "tx_data": tx_data,
            "estimated_gas": 40000,
            "status": "prepared"
        }

    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get blockchain-related platform statistics."""
        try:
            pool_balance = await self.rewards_pool.get_pool_balance()
            conversion_rate = await self.rewards_pool.get_conversion_rate()

            return {
                "rewards_pool_balance": pool_balance,
                "conversion_rate": conversion_rate,
                "network": settings.STACKS_NETWORK
            }
        except Exception as e:
            return {
                "error": str(e),
                "network": settings.STACKS_NETWORK
            }


# Global blockchain service instance
blockchain_service = BlockchainService()
