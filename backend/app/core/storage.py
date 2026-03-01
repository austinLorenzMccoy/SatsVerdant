from google.cloud import storage
from typing import Optional, Dict, Any
from app.core.config import settings
import logging
import io
from datetime import timedelta

logger = logging.getLogger(__name__)


class GCPStorageClient:
    """Client for interacting with Google Cloud Storage."""

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.bucket_name = settings.GCP_STORAGE_BUCKET
        self.credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        
        # Initialize GCS client
        if self.credentials_path:
            self.client = storage.Client.from_service_account_json(self.credentials_path)
        else:
            # Use default credentials (for GCP environments)
            self.client = storage.Client(project=self.project_id)
        
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_file(
        self,
        file_bytes: bytes,
        destination_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to GCS.
        
        Args:
            file_bytes: File content as bytes
            destination_path: Path in bucket (e.g., 'uploads/image.jpg')
            content_type: MIME type of the file
            metadata: Optional metadata to attach
            
        Returns:
            Dict with upload details including public URL
        """
        try:
            blob = self.bucket.blob(destination_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            # Set metadata if provided
            if metadata:
                blob.metadata = metadata
            
            # Upload the file
            blob.upload_from_string(file_bytes)
            
            logger.info(f"Successfully uploaded file to GCS: {destination_path}")
            
            return {
                "bucket": self.bucket_name,
                "path": destination_path,
                "public_url": blob.public_url,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created
            }
            
        except Exception as e:
            logger.error(f"GCS upload error: {str(e)}")
            raise Exception(f"Failed to upload to GCS: {str(e)}")

    def download_file(self, source_path: str) -> bytes:
        """
        Download a file from GCS.
        
        Args:
            source_path: Path in bucket
            
        Returns:
            File content as bytes
        """
        try:
            blob = self.bucket.blob(source_path)
            file_bytes = blob.download_as_bytes()
            
            logger.info(f"Successfully downloaded file from GCS: {source_path}")
            return file_bytes
            
        except Exception as e:
            logger.error(f"GCS download error: {str(e)}")
            raise Exception(f"Failed to download from GCS: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from GCS.
        
        Args:
            file_path: Path in bucket
            
        Returns:
            True if successful
        """
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            
            logger.info(f"Successfully deleted file from GCS: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"GCS delete error: {str(e)}")
            return False

    def generate_signed_url(
        self,
        file_path: str,
        expiration_minutes: int = 60,
        method: str = "GET"
    ) -> str:
        """
        Generate a signed URL for temporary access to a file.
        
        Args:
            file_path: Path in bucket
            expiration_minutes: URL expiration time in minutes
            method: HTTP method (GET, PUT, etc.)
            
        Returns:
            Signed URL string
        """
        try:
            blob = self.bucket.blob(file_path)
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method=method
            )
            
            logger.info(f"Generated signed URL for {file_path}")
            return url
            
        except Exception as e:
            logger.error(f"GCS signed URL error: {str(e)}")
            raise Exception(f"Failed to generate signed URL: {str(e)}")

    def list_files(self, prefix: Optional[str] = None, max_results: int = 100) -> list:
        """
        List files in the bucket.
        
        Args:
            prefix: Filter by prefix (folder path)
            max_results: Maximum number of results
            
        Returns:
            List of file paths
        """
        try:
            blobs = self.client.list_blobs(
                self.bucket_name,
                prefix=prefix,
                max_results=max_results
            )
            
            file_list = [blob.name for blob in blobs]
            logger.info(f"Listed {len(file_list)} files from GCS")
            
            return file_list
            
        except Exception as e:
            logger.error(f"GCS list error: {str(e)}")
            raise Exception(f"Failed to list files: {str(e)}")

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in GCS.
        
        Args:
            file_path: Path in bucket
            
        Returns:
            True if file exists
        """
        try:
            blob = self.bucket.blob(file_path)
            return blob.exists()
            
        except Exception as e:
            logger.error(f"GCS exists check error: {str(e)}")
            return False

    def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file.
        
        Args:
            file_path: Path in bucket
            
        Returns:
            Dict with file metadata or None if not found
        """
        try:
            blob = self.bucket.blob(file_path)
            blob.reload()
            
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created,
                "updated": blob.updated,
                "metadata": blob.metadata,
                "public_url": blob.public_url
            }
            
        except Exception as e:
            logger.error(f"GCS metadata error: {str(e)}")
            return None


# Global GCS client instance
gcs_client = GCPStorageClient()
