#!/usr/bin/env python3
"""
Train waste classification model with MLflow tracking.
"""
import os
import sys
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV3Large
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import mlflow
import mlflow.tensorflow
from datetime import datetime
import json

# Configuration
UNIFIED_DATA_DIR = Path("data/unified")
SYNTHETIC_DATA_DIR = Path("data/synthetic")
MODEL_OUTPUT_DIR = Path("models")
MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Hyperparameters
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 0.001
VALIDATION_SPLIT = 0.2
NUM_CLASSES = 5

# Categories
CATEGORIES = ['plastic', 'paper', 'metal', 'organic', 'electronic']


def create_combined_dataset():
    """Combine original and synthetic datasets."""
    print("\n" + "="*60)
    print("📁 Creating Combined Dataset")
    print("="*60)
    
    combined_dir = Path("data/combined")
    
    # Create combined directory structure
    for category in CATEGORIES:
        (combined_dir / category).mkdir(parents=True, exist_ok=True)
    
    # Copy/symlink images from both sources
    import shutil
    
    total_images = 0
    for category in CATEGORIES:
        # Original images
        original_dir = UNIFIED_DATA_DIR / category
        if original_dir.exists():
            for img in original_dir.glob("*.jpg"):
                dest = combined_dir / category / img.name
                if not dest.exists():
                    shutil.copy2(img, dest)
                    total_images += 1
        
        # Synthetic images
        synthetic_dir = SYNTHETIC_DATA_DIR / category
        if synthetic_dir.exists():
            for img in synthetic_dir.glob("*.jpg"):
                dest = combined_dir / category / img.name
                if not dest.exists():
                    shutil.copy2(img, dest)
                    total_images += 1
    
    # Print statistics
    print("\n📊 Combined Dataset:")
    for category in CATEGORIES:
        count = len(list((combined_dir / category).glob("*.jpg")))
        print(f"  {category:12s}: {count:6,} images")
    
    print(f"\n  {'TOTAL':12s}: {total_images:6,} images")
    
    return combined_dir


def create_data_generators(data_dir):
    """Create training and validation data generators."""
    print("\n" + "="*60)
    print("🔄 Creating Data Generators")
    print("="*60)
    
    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=VALIDATION_SPLIT
    )
    
    # Only rescaling for validation
    val_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=VALIDATION_SPLIT
    )
    
    # Training generator
    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training',
        shuffle=True
    )
    
    # Validation generator
    val_generator = val_datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation',
        shuffle=False
    )
    
    print(f"\n✅ Training samples: {train_generator.samples}")
    print(f"✅ Validation samples: {val_generator.samples}")
    print(f"✅ Classes: {train_generator.class_indices}")
    
    return train_generator, val_generator


def create_model():
    """Create MobileNetV3-Large based classifier."""
    print("\n" + "="*60)
    print("🏗️  Building Model Architecture")
    print("="*60)
    
    # Load pre-trained MobileNetV3-Large
    base_model = MobileNetV3Large(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model layers initially
    base_model.trainable = False
    
    # Build model
    model = keras.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.3),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(NUM_CLASSES, activation='softmax')
    ])
    
    # Compile model
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='categorical_crossentropy',
        metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=2, name='top_2_accuracy')]
    )
    
    print("\n📋 Model Summary:")
    model.summary()
    
    return model


def train_model_with_mlflow(model, train_gen, val_gen):
    """Train model with MLflow tracking."""
    print("\n" + "="*60)
    print("🚀 Starting Training with MLflow Tracking")
    print("="*60)
    
    # Set MLflow experiment
    mlflow.set_experiment("waste-classification")
    
    with mlflow.start_run(run_name=f"mobilenetv3_large_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        # Log parameters
        mlflow.log_param("model_architecture", "MobileNetV3-Large")
        mlflow.log_param("input_size", IMG_SIZE)
        mlflow.log_param("batch_size", BATCH_SIZE)
        mlflow.log_param("epochs", EPOCHS)
        mlflow.log_param("learning_rate", LEARNING_RATE)
        mlflow.log_param("optimizer", "Adam")
        mlflow.log_param("num_classes", NUM_CLASSES)
        mlflow.log_param("train_samples", train_gen.samples)
        mlflow.log_param("val_samples", val_gen.samples)
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=1e-7
            ),
            keras.callbacks.ModelCheckpoint(
                str(MODEL_OUTPUT_DIR / 'best_model.h5'),
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
        
        # Train model
        print("\n🏋️  Training model...")
        history = model.fit(
            train_gen,
            validation_data=val_gen,
            epochs=EPOCHS,
            callbacks=callbacks,
            verbose=1
        )
        
        # Log metrics
        final_train_acc = history.history['accuracy'][-1]
        final_val_acc = history.history['val_accuracy'][-1]
        final_train_loss = history.history['loss'][-1]
        final_val_loss = history.history['val_loss'][-1]
        
        mlflow.log_metric("final_train_accuracy", final_train_acc)
        mlflow.log_metric("final_val_accuracy", final_val_acc)
        mlflow.log_metric("final_train_loss", final_train_loss)
        mlflow.log_metric("final_val_loss", final_val_loss)
        
        # Log all epoch metrics
        for epoch in range(len(history.history['accuracy'])):
            mlflow.log_metric("train_accuracy", history.history['accuracy'][epoch], step=epoch)
            mlflow.log_metric("val_accuracy", history.history['val_accuracy'][epoch], step=epoch)
            mlflow.log_metric("train_loss", history.history['loss'][epoch], step=epoch)
            mlflow.log_metric("val_loss", history.history['val_loss'][epoch], step=epoch)
        
        # Save model
        model_version = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = MODEL_OUTPUT_DIR / f"waste_classifier_{model_version}.h5"
        model.save(str(model_path))
        
        # Log model to MLflow
        mlflow.tensorflow.log_model(model, "model")
        
        # Save for backend
        backend_model_path = Path("../backend/models/waste_classifier.h5")
        backend_model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(backend_model_path))
        
        print(f"\n✅ Model saved to: {model_path}")
        print(f"✅ Backend model saved to: {backend_model_path}")
        print(f"\n📊 Final Results:")
        print(f"  Training Accuracy:   {final_train_acc:.4f}")
        print(f"  Validation Accuracy: {final_val_acc:.4f}")
        print(f"  Training Loss:       {final_train_loss:.4f}")
        print(f"  Validation Loss:     {final_val_loss:.4f}")
        
        # Save training history
        history_path = MODEL_OUTPUT_DIR / f"training_history_{model_version}.json"
        with open(history_path, 'w') as f:
            json.dump(history.history, f, indent=2)
        
        mlflow.log_artifact(str(history_path))
        
        return history, model_path


def evaluate_model(model, val_gen):
    """Evaluate model performance."""
    print("\n" + "="*60)
    print("📊 Evaluating Model")
    print("="*60)
    
    # Evaluate on validation set
    results = model.evaluate(val_gen, verbose=1)
    
    print(f"\n✅ Validation Loss: {results[0]:.4f}")
    print(f"✅ Validation Accuracy: {results[1]:.4f}")
    print(f"✅ Top-2 Accuracy: {results[2]:.4f}")
    
    # Per-class accuracy (optional, requires predictions)
    print("\n🔍 Generating predictions for detailed analysis...")
    predictions = model.predict(val_gen, verbose=1)
    predicted_classes = np.argmax(predictions, axis=1)
    true_classes = val_gen.classes
    
    # Confusion matrix
    from sklearn.metrics import classification_report, confusion_matrix
    
    print("\n📋 Classification Report:")
    print(classification_report(
        true_classes,
        predicted_classes,
        target_names=CATEGORIES
    ))
    
    print("\n📊 Confusion Matrix:")
    cm = confusion_matrix(true_classes, predicted_classes)
    print(cm)
    
    return results


def main():
    """Main training pipeline."""
    print("🚀 SatsVerdant Model Training Pipeline")
    print("="*60)
    
    # Check if data exists
    if not UNIFIED_DATA_DIR.exists():
        print("❌ Unified dataset not found!")
        print("Please run: python scripts/remap_datasets.py")
        sys.exit(1)
    
    # Create combined dataset
    combined_dir = create_combined_dataset()
    
    # Create data generators
    train_gen, val_gen = create_data_generators(combined_dir)
    
    # Create model
    model = create_model()
    
    # Train model with MLflow
    history, model_path = train_model_with_mlflow(model, train_gen, val_gen)
    
    # Evaluate model
    evaluate_model(model, val_gen)
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE!")
    print("="*60)
    print(f"\n📦 Model saved to: {model_path}")
    print(f"📦 Backend model: ../backend/models/waste_classifier.h5")
    print(f"\n📊 View MLflow UI:")
    print(f"  cd ml-training")
    print(f"  mlflow ui")
    print(f"  Open: http://localhost:5000")
    print("\n🚀 Ready to deploy!")


if __name__ == "__main__":
    # Set random seeds for reproducibility
    np.random.seed(42)
    tf.random.set_seed(42)
    
    main()
