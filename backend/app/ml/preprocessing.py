"""
Image preprocessing utilities for ML models.
Handles image normalization, augmentation, and feature extraction.
"""
import numpy as np
import cv2
from PIL import Image
import io
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Image preprocessing for waste classification."""

    def __init__(self, target_size: Tuple[int, int] = (224, 224)):
        self.target_size = target_size

    def preprocess_for_classification(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess image for classification model.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Preprocessed numpy array ready for model input
        """
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to target size
        image = image.resize(self.target_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        image_array = np.array(image, dtype=np.float32)
        
        # Normalize to [0, 1]
        image_array = image_array / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array

    def extract_features(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract visual features from image.
        
        Returns:
            Dictionary of extracted features
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Extract features
            features = {
                'width': image.width,
                'height': image.height,
                'aspect_ratio': image.width / image.height if image.height > 0 else 0,
                'file_size_kb': len(image_bytes) / 1024,
                'color_channels': len(image.getbands()),
                'dominant_colors': self._get_dominant_colors(image_cv),
                'edge_density': self._calculate_edge_density(image_cv),
                'brightness': self._calculate_brightness(image_cv),
                'contrast': self._calculate_contrast(image_cv)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {}

    def _get_dominant_colors(self, image: np.ndarray, k: int = 3) -> list:
        """Extract dominant colors using k-means clustering."""
        try:
            # Reshape image to list of pixels
            pixels = image.reshape(-1, 3).astype(np.float32)
            
            # Sample pixels for efficiency
            if len(pixels) > 10000:
                indices = np.random.choice(len(pixels), 10000, replace=False)
                pixels = pixels[indices]
            
            # K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
            
            # Convert to list of RGB tuples
            dominant_colors = [tuple(map(int, color)) for color in centers]
            return dominant_colors
            
        except Exception as e:
            logger.error(f"Dominant color extraction failed: {e}")
            return []

    def _calculate_edge_density(self, image: np.ndarray) -> float:
        """Calculate edge density using Canny edge detection."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size
            return float(edge_density)
        except Exception as e:
            logger.error(f"Edge density calculation failed: {e}")
            return 0.0

    def _calculate_brightness(self, image: np.ndarray) -> float:
        """Calculate average brightness."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return float(np.mean(gray))
        except Exception as e:
            logger.error(f"Brightness calculation failed: {e}")
            return 0.0

    def _calculate_contrast(self, image: np.ndarray) -> float:
        """Calculate contrast using standard deviation."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return float(np.std(gray))
        except Exception as e:
            logger.error(f"Contrast calculation failed: {e}")
            return 0.0

    def augment_image(self, image_bytes: bytes, augmentation_type: str = 'random') -> bytes:
        """
        Apply data augmentation to image.
        
        Args:
            image_bytes: Original image bytes
            augmentation_type: Type of augmentation to apply
            
        Returns:
            Augmented image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            if augmentation_type == 'flip':
                image_cv = cv2.flip(image_cv, 1)
            elif augmentation_type == 'rotate':
                angle = np.random.uniform(-15, 15)
                h, w = image_cv.shape[:2]
                M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
                image_cv = cv2.warpAffine(image_cv, M, (w, h))
            elif augmentation_type == 'brightness':
                alpha = np.random.uniform(0.8, 1.2)
                image_cv = cv2.convertScaleAbs(image_cv, alpha=alpha, beta=0)
            elif augmentation_type == 'random':
                # Apply random augmentation
                aug_type = np.random.choice(['flip', 'rotate', 'brightness'])
                return self.augment_image(image_bytes, aug_type)
            
            # Convert back to bytes
            image_pil = Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))
            output = io.BytesIO()
            image_pil.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Image augmentation failed: {e}")
            return image_bytes


# Global preprocessor instance
image_preprocessor = ImagePreprocessor()
