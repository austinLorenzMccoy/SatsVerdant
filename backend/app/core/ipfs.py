import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class IPFSClient:
    """Client for interacting with IPFS via Pinata pinning service."""

    def __init__(self):
        self.api_key = settings.IPFS_PINATA_API_KEY
        self.secret_key = settings.IPFS_PINATA_SECRET_KEY
        self.gateway_url = settings.IPFS_GATEWAY_URL
        self.base_url = "https://api.pinata.cloud"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def pin_file(self, file_bytes: bytes, filename: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Pin a file to IPFS via Pinata.
        
        Args:
            file_bytes: File content as bytes
            filename: Name of the file
            metadata: Optional metadata to attach
            
        Returns:
            Dict with IPFS hash and pinning details
        """
        try:
            url = f"{self.base_url}/pinning/pinFileToIPFS"
            
            headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.secret_key
            }
            
            files = {
                "file": (filename, file_bytes)
            }
            
            # Add metadata if provided
            pinata_metadata = {}
            if metadata:
                pinata_metadata = {
                    "name": filename,
                    "keyvalues": metadata
                }
            
            data = {}
            if pinata_metadata:
                import json
                data["pinataMetadata"] = json.dumps(pinata_metadata)
            
            response = await self.client.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            ipfs_hash = result.get("IpfsHash")
            
            logger.info(f"Successfully pinned file {filename} to IPFS: {ipfs_hash}")
            
            return {
                "ipfs_hash": ipfs_hash,
                "ipfs_url": f"{self.gateway_url}{ipfs_hash}",
                "pin_size": result.get("PinSize"),
                "timestamp": result.get("Timestamp")
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"IPFS pinning failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"IPFS pinning failed: {str(e)}")
        except Exception as e:
            logger.error(f"IPFS pinning error: {str(e)}")
            raise

    async def pin_json(self, json_data: Dict[str, Any], name: str) -> Dict[str, Any]:
        """
        Pin JSON data to IPFS via Pinata.
        
        Args:
            json_data: JSON data to pin
            name: Name for the pinned content
            
        Returns:
            Dict with IPFS hash and pinning details
        """
        try:
            url = f"{self.base_url}/pinning/pinJSONToIPFS"
            
            headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.secret_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "pinataContent": json_data,
                "pinataMetadata": {
                    "name": name
                }
            }
            
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            ipfs_hash = result.get("IpfsHash")
            
            logger.info(f"Successfully pinned JSON {name} to IPFS: {ipfs_hash}")
            
            return {
                "ipfs_hash": ipfs_hash,
                "ipfs_url": f"{self.gateway_url}{ipfs_hash}",
                "pin_size": result.get("PinSize"),
                "timestamp": result.get("Timestamp")
            }
            
        except Exception as e:
            logger.error(f"IPFS JSON pinning error: {str(e)}")
            raise

    async def unpin(self, ipfs_hash: str) -> bool:
        """
        Unpin content from IPFS.
        
        Args:
            ipfs_hash: IPFS hash to unpin
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.base_url}/pinning/unpin/{ipfs_hash}"
            
            headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.secret_key
            }
            
            response = await self.client.delete(url, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully unpinned {ipfs_hash} from IPFS")
            return True
            
        except Exception as e:
            logger.error(f"IPFS unpinning error: {str(e)}")
            return False

    async def get_pin_list(self, status: str = "pinned", limit: int = 10) -> Dict[str, Any]:
        """
        Get list of pinned files.
        
        Args:
            status: Pin status filter (pinned, unpinned, all)
            limit: Maximum number of results
            
        Returns:
            Dict with pin list
        """
        try:
            url = f"{self.base_url}/data/pinList"
            
            headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.secret_key
            }
            
            params = {
                "status": status,
                "pageLimit": limit
            }
            
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"IPFS pin list error: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global IPFS client instance
ipfs_client = IPFSClient()
