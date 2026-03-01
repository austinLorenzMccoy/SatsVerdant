#!/usr/bin/env python3
"""
Test trained model on sample images.
"""
import numpy as np
import cv2
from pathlib import Path
from tensorflow import keras
import sys

# Categories
CATEGORIES = ['plastic', 'paper', 'metal', 'organic', 'electronic']
IMG_SIZE = 224


def load_model():
    """Load trained model."""
    model_path = Path("../backend/models/waste_classifier.h5")
    
    if not model_path.exists():
        print(f"❌ Model not found at {model_path}")
        print("Please train the model first: python scripts/train_model.py")
        sys.exit(1)
    
    print(f"📦 Loading model from {model_path}")
    model = keras.models.load_model(str(model_path))
    print("✅ Model loaded successfully")
    
    return model


def preprocess_image(image_path):
    """Preprocess image for model input."""
    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    
    # Normalize
    img = img.astype(np.float32) / 255.0
    
    # Add batch dimension
    img = np.expand_dims(img, axis=0)
    
    return img


def predict_image(model, image_path):
    """Predict waste type for an image."""
    # Preprocess
    img = preprocess_image(image_path)
    if img is None:
        print(f"❌ Failed to load image: {image_path}")
        return None
    
    # Predict
    predictions = model.predict(img, verbose=0)[0]
    
    # Get top prediction
    top_idx = np.argmax(predictions)
    top_category = CATEGORIES[top_idx]
    top_confidence = predictions[top_idx]
    
    # Get top 3 predictions
    top_3_idx = np.argsort(predictions)[-3:][::-1]
    
    results = {
        'predicted_class': top_category,
        'confidence': float(top_confidence),
        'all_probabilities': {cat: float(prob) for cat, prob in zip(CATEGORIES, predictions)},
        'top_3': [(CATEGORIES[idx], float(predictions[idx])) for idx in top_3_idx]
    }
    
    return results


def test_sample_images(model):
    """Test model on sample images from dataset."""
    print("\n" + "="*60)
    print("🧪 Testing Model on Sample Images")
    print("="*60)
    
    # Get sample images from each category
    unified_dir = Path("data/unified")
    
    if not unified_dir.exists():
        print("⚠️  No test images found")
        return
    
    for category in CATEGORIES:
        category_dir = unified_dir / category
        if not category_dir.exists():
            continue
        
        # Get first image
        images = list(category_dir.glob("*.jpg"))
        if not images:
            continue
        
        test_image = images[0]
        
        print(f"\n📸 Testing {category} image: {test_image.name}")
        results = predict_image(model, test_image)
        
        if results:
            predicted = results['predicted_class']
            confidence = results['confidence']
            
            # Check if correct
            is_correct = predicted == category
            status = "✅" if is_correct else "❌"
            
            print(f"  {status} Predicted: {predicted} ({confidence:.2%})")
            print(f"  Top 3 predictions:")
            for cat, prob in results['top_3']:
                print(f"    - {cat}: {prob:.2%}")


def interactive_test(model):
    """Interactive testing mode."""
    print("\n" + "="*60)
    print("🎯 Interactive Testing Mode")
    print("="*60)
    print("\nEnter image path to test (or 'quit' to exit)")
    
    while True:
        image_path = input("\n📸 Image path: ").strip()
        
        if image_path.lower() in ['quit', 'exit', 'q']:
            break
        
        if not Path(image_path).exists():
            print(f"❌ File not found: {image_path}")
            continue
        
        results = predict_image(model, image_path)
        
        if results:
            print(f"\n✅ Prediction: {results['predicted_class']}")
            print(f"   Confidence: {results['confidence']:.2%}")
            print(f"\n   All probabilities:")
            for cat, prob in results['all_probabilities'].items():
                bar = "█" * int(prob * 50)
                print(f"   {cat:12s}: {prob:.2%} {bar}")


def main():
    """Main testing function."""
    print("🧪 SatsVerdant Model Testing")
    print("="*60)
    
    # Load model
    model = load_model()
    
    # Test on sample images
    test_sample_images(model)
    
    # Interactive mode
    print("\n" + "="*60)
    response = input("\nEnter interactive testing mode? (y/n): ").strip().lower()
    if response == 'y':
        interactive_test(model)
    
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    main()
