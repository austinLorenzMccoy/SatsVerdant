"""
Model loading utilities for ML services.
Handles model initialization, caching, and version management.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pickle
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelLoader:
    """Utility class for loading and managing ML models."""

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir or settings.MODEL_PATH)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_models: Dict[str, Any] = {}

    def load_tensorflow_model(self, model_name: str) -> Optional[Any]:
        """Load TensorFlow/Keras model."""
        try:
            import tensorflow as tf
            model_path = self.model_dir / f"{model_name}.h5"
            
            if not model_path.exists():
                logger.warning(f"Model {model_name} not found at {model_path}")
                return None
            
            model = tf.keras.models.load_model(str(model_path))
            self.loaded_models[model_name] = model
            logger.info(f"Successfully loaded TensorFlow model: {model_name}")
            return model
            
        except ImportError:
            logger.error("TensorFlow not installed. Cannot load model.")
            return None
        except Exception as e:
            logger.error(f"Failed to load TensorFlow model {model_name}: {e}")
            return None

    def load_pytorch_model(self, model_name: str, model_class: Any) -> Optional[Any]:
        """Load PyTorch model."""
        try:
            import torch
            model_path = self.model_dir / f"{model_name}.pth"
            
            if not model_path.exists():
                logger.warning(f"Model {model_name} not found at {model_path}")
                return None
            
            model = model_class()
            model.load_state_dict(torch.load(str(model_path)))
            model.eval()
            
            self.loaded_models[model_name] = model
            logger.info(f"Successfully loaded PyTorch model: {model_name}")
            return model
            
        except ImportError:
            logger.error("PyTorch not installed. Cannot load model.")
            return None
        except Exception as e:
            logger.error(f"Failed to load PyTorch model {model_name}: {e}")
            return None

    def load_sklearn_model(self, model_name: str) -> Optional[Any]:
        """Load scikit-learn model."""
        try:
            model_path = self.model_dir / f"{model_name}.pkl"
            
            if not model_path.exists():
                logger.warning(f"Model {model_name} not found at {model_path}")
                return None
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            self.loaded_models[model_name] = model
            logger.info(f"Successfully loaded scikit-learn model: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load scikit-learn model {model_name}: {e}")
            return None

    def get_model(self, model_name: str) -> Optional[Any]:
        """Get cached model or return None."""
        return self.loaded_models.get(model_name)

    def unload_model(self, model_name: str):
        """Unload model from memory."""
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            logger.info(f"Unloaded model: {model_name}")

    def list_available_models(self) -> list:
        """List all available model files."""
        model_files = []
        for ext in ['*.h5', '*.pth', '*.pkl', '*.joblib']:
            model_files.extend(self.model_dir.glob(ext))
        return [f.stem for f in model_files]


# Global model loader instance
model_loader = ModelLoader()
