import numpy as np
import cv2
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image
import io
import logging
from pathlib import Path
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


class WasteClassifier:
    """AI-powered waste classification service."""

    def __init__(self):
        self.model_path = settings.MODEL_PATH
        self.input_shape = (224, 224, 3)
        self.classes = ['plastic', 'paper', 'metal', 'organic', 'electronic']
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load ML model if available."""
        try:
            model_file = Path(self.model_path) / "waste_classifier.h5"
            if model_file.exists():
                # TODO: Uncomment when TensorFlow is properly configured
                # import tensorflow as tf
                # self.model = tf.keras.models.load_model(str(model_file))
                logger.info(f"Model loaded from {model_file}")
            else:
                logger.warning(f"Model file not found at {model_file}. Using mock classification.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}. Using mock classification.")

    def classify_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Classify waste in image.
        Returns classification results.
        """
        try:
            # Preprocess image
            processed_image = self._preprocess_image(image_bytes)

            # TODO: Run model inference
            # For MVP, return mock results
            waste_type, confidence = self._mock_classification()

            return {
                'waste_type': waste_type,
                'confidence': confidence,
                'all_probabilities': self._mock_probabilities(),
                'is_confident': confidence >= 0.7,
                'processing_time_ms': 150
            }

        except Exception as e:
            raise Exception(f"Classification failed: {str(e)}")

    def _preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Preprocess image for model input."""
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize
        image = image.resize(self.input_shape[:2])

        # Convert to numpy array
        image_array = np.array(image)

        # Normalize to [0, 1]
        image_array = image_array.astype(np.float32) / 255.0

        return image_array

    def _mock_classification(self) -> Tuple[str, float]:
        """Mock classification for MVP."""
        # Random classification with realistic confidence
        waste_type = np.random.choice(self.classes, p=[0.4, 0.3, 0.15, 0.1, 0.05])
        confidence = np.random.uniform(0.6, 0.95)
        return waste_type, confidence

    def _mock_probabilities(self) -> Dict[str, float]:
        """Mock probability distribution."""
        # Create random probabilities that sum to 1
        probs = np.random.dirichlet([2, 2, 1, 1, 0.5])
        return dict(zip(self.classes, probs))


class WeightEstimator:
    """Weight estimation service."""

    def __init__(self):
        self.base_weights = {
            'plastic': 0.5,
            'paper': 1.0,
            'metal': 0.8,
            'organic': 1.5,
            'electronic': 0.3
        }

    def estimate_weight(self, waste_type: str, image_metadata: Optional[Dict] = None) -> float:
        """
        Estimate weight of waste from type and optional metadata.
        """
        base_weight = self.base_weights.get(waste_type, 1.0)

        # Add some variance
        variance = np.random.uniform(0.8, 1.2)
        estimated_weight = base_weight * variance

        # If object count available, adjust
        if image_metadata and 'object_count' in image_metadata:
            count = min(image_metadata['object_count'], 5)
            multiplier = {1: 1.0, 2: 1.8, 3: 2.5, 4: 3.2, 5: 4.0}.get(count, 1.0)
            estimated_weight *= multiplier

        return round(estimated_weight, 1)


class QualityGrader:
    """Image quality assessment service."""

    def __init__(self):
        self.grade_thresholds = {
            'A': {'blur_variance': 100, 'brightness': (50, 200), 'contrast': 40},
            'B': {'blur_variance': 50, 'brightness': (30, 220), 'contrast': 25},
            'C': {'blur_variance': 20, 'brightness': (20, 240), 'contrast': 15},
            'D': {'blur_variance': 0, 'brightness': (0, 255), 'contrast': 0}
        }

    def grade_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Assess image quality and assign grade.
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Calculate metrics
            blur_score = self._calculate_blur(image_cv)
            brightness = self._calculate_brightness(image_cv)
            contrast = self._calculate_contrast(image_cv)

            # Determine grade
            grade = self._determine_grade(blur_score, brightness, contrast)

            return {
                'grade': grade,
                'blur_score': float(blur_score),
                'brightness': float(brightness),
                'contrast': float(contrast),
                'quality_details': {
                    'is_blurry': blur_score < 50,
                    'is_too_dark': brightness < 30,
                    'is_too_bright': brightness > 220,
                    'is_low_contrast': contrast < 25
                }
            }

        except Exception as e:
            raise Exception(f"Quality grading failed: {str(e)}")

    def _calculate_blur(self, image: np.ndarray) -> float:
        """Calculate blur score using Laplacian variance."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def _calculate_brightness(self, image: np.ndarray) -> float:
        """Calculate average brightness."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return np.mean(gray)

    def _calculate_contrast(self, image: np.ndarray) -> float:
        """Calculate contrast using standard deviation."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return np.std(gray)

    def _determine_grade(self, blur: float, brightness: float, contrast: float) -> str:
        """Determine quality grade based on metrics."""
        if (blur >= 100 and 50 <= brightness <= 200 and contrast >= 40):
            return 'A'
        elif (blur >= 50 and 30 <= brightness <= 220 and contrast >= 25):
            return 'B'
        elif (blur >= 20 and 20 <= brightness <= 240 and contrast >= 15):
            return 'C'
        else:
            return 'D'


class FraudDetector:
    """Fraud detection service."""

    def __init__(self):
        self.duplicate_threshold = 5
        self.location_radius_m = 50
        self.rapid_submission_threshold = 5
        self.low_confidence_threshold = 0.7

    def detect_fraud(self, submission_data: Dict[str, Any], user_id: str, db_session) -> Dict[str, Any]:
        """
        Run fraud detection on submission.
        """
        fraud_score = 0.0
        flags = []

        # Check for duplicate images
        duplicate_check = self._check_duplicate_images(user_id, submission_data, db_session)
        if duplicate_check['is_duplicate']:
            fraud_score += 0.5
            flags.append({
                'type': 'duplicate_image',
                'severity': 'high',
                'details': duplicate_check
            })

        # Check location clustering
        if submission_data.get('latitude') and submission_data.get('longitude'):
            location_flag = self._check_location_clustering(
                user_id, submission_data['latitude'], submission_data['longitude'], db_session
            )
            if location_flag:
                fraud_score += 0.2
                flags.append(location_flag)

        # Check rapid submissions
        rapid_flag = self._check_rapid_submissions(user_id, db_session)
        if rapid_flag:
            fraud_score += 0.3
            flags.append(rapid_flag)

        # Check low confidence classification
        if submission_data.get('ai_confidence', 1.0) < self.low_confidence_threshold:
            fraud_score += 0.15
            flags.append({
                'type': 'low_confidence',
                'severity': 'medium',
                'details': {'confidence': submission_data.get('ai_confidence')}
            })

        return {
            'score': min(fraud_score, 1.0),
            'flags': flags,
            'is_suspicious': fraud_score >= 0.5,
            'requires_manual_review': fraud_score >= 0.7
        }

    def _check_duplicate_images(self, user_id: str, submission_data: Dict, db_session) -> Dict:
        """Check for duplicate images using perceptual hashing."""
        # TODO: Implement perceptual hashing (pHash, dHash)
        # For MVP, simplified check
        try:
            from app.models import Submission
            recent_submissions = db_session.query(Submission).filter(
                Submission.user_id == user_id,
                Submission.created_at >= datetime.utcnow() - timedelta(days=7)
            ).limit(10).all()
            
            # In production: compare image hashes
            return {'is_duplicate': False, 'similar_submissions': []}
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return {'is_duplicate': False}

    def _check_location_clustering(self, user_id: str, lat: float, lon: float, db_session) -> Optional[Dict]:
        """Check if submissions cluster at same location."""
        try:
            from app.models import Submission
            from sqlalchemy import func
            
            # Count submissions within radius in last 24 hours
            recent_nearby = db_session.query(func.count(Submission.id)).filter(
                Submission.user_id == user_id,
                Submission.latitude.isnot(None),
                Submission.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).scalar()
            
            if recent_nearby and recent_nearby > 5:
                return {
                    'type': 'location_clustering',
                    'severity': 'medium',
                    'details': {'nearby_count': recent_nearby}
                }
        except Exception as e:
            logger.error(f"Location clustering check failed: {e}")
        return None

    def _check_rapid_submissions(self, user_id: str, db_session) -> Optional[Dict]:
        """Check for suspiciously rapid submissions."""
        try:
            from app.models import Submission
            from sqlalchemy import func
            
            # Count submissions in last hour
            recent_count = db_session.query(func.count(Submission.id)).filter(
                Submission.user_id == user_id,
                Submission.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).scalar()
            
            if recent_count and recent_count >= self.rapid_submission_threshold:
                return {
                    'type': 'rapid_submission',
                    'severity': 'high',
                    'details': {'submissions_last_hour': recent_count}
                }
        except Exception as e:
            logger.error(f"Rapid submission check failed: {e}")
        return None


# Global service instances
waste_classifier = WasteClassifier()
weight_estimator = WeightEstimator()
quality_grader = QualityGrader()
fraud_detector = FraudDetector()
