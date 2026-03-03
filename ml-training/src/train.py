#!/usr/bin/env python3
"""
SatsVerdant ML Training Script with MLflow Integration
Implements EfficientNetB0 training with full experiment tracking

Usage:
    python src/train.py [--export-only] [--resume]
"""

import os
import sys
import yaml
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix
import mlflow
import mlflow.tensorflow
import dagshub

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_params():
    """Load hyperparameters from params.yaml"""
    with open("params.yaml") as f:
        return yaml.safe_load(f)

def setup_mlflow(params):
    """Initialize MLflow and DagsHub tracking"""
    dagshub.init(
        repo_owner="satsverdant",
        repo_name="satsverdant-ml", 
        mlflow=True
    )
    
    mlflow.set_experiment(params["mlflow"]["experiment_name"])
    
    return mlflow.start_run(
        run_name=f"effnetb0-bs{params['train']['batch_size']}-"
        f"p1ep{params['train']['epochs_phase1']}-"
        f"p2ep{params['train']['epochs_phase2']}"
    )

def create_data_generators(params):
    """Create training and validation data generators"""
    train_params = params["train"]
    aug_params = params["augmentation"]
    prep_params = params["prepare"]
    
    # Training data generator with augmentation
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=aug_params["rotation_range"],
        zoom_range=aug_params["zoom_range"],
        brightness_range=[aug_params["brightness_min"], aug_params["brightness_max"]],
        horizontal_flip=aug_params["horizontal_flip"],
        vertical_flip=aug_params["vertical_flip"],
        shear_range=aug_params["shear_range"],
        width_shift_range=aug_params["width_shift_range"],
        height_shift_range=aug_params["height_shift_range"],
        channel_shift_range=aug_params["channel_shift_range"],
        fill_mode=aug_params["fill_mode"]
    )
    
    # Validation data generator (no augmentation)
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    # Create generators
    img_size = prep_params["img_size"]
    batch_size = train_params["batch_size"]
    
    train_gen = train_datagen.flow_from_directory(
        f"data/processed/train",
        target_size=(img_size, img_size),
        batch_size=batch_size,
        class_mode="categorical"
    )
    
    val_gen = val_datagen.flow_from_directory(
        f"data/processed/val",
        target_size=(img_size, img_size),
        batch_size=batch_size,
        class_mode="categorical"
    )
    
    return train_gen, val_gen

def create_model(params):
    """Create EfficientNetB0 model with custom head"""
    train_params = params["train"]
    prep_params = params["prepare"]
    
    # Load base model
    base_model = EfficientNetB0(
        weights="imagenet",
        include_top=False,
        input_shape=(prep_params["img_size"], prep_params["img_size"], 3)
    )
    base_model.trainable = False
    
    # Create model architecture
    inputs = layers.Input(shape=(prep_params["img_size"], prep_params["img_size"], 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(train_params["dropout"])(x)
    outputs = layers.Dense(train_params["num_classes"], activation="softmax")(x)
    
    model = models.Model(inputs, outputs, name="satsverdant_waste_classifier")
    
    return model, base_model

def train_phase1(model, train_gen, val_gen, params, mlflow_run):
    """Phase 1: Train classifier head with frozen base"""
    train_params = params["train"]
    
    model.compile(
        optimizer=optimizers.Adam(train_params["lr_phase1"]),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    callbacks = [
        EarlyStopping(
            patience=4,
            restore_best_weights=True,
            monitor="val_accuracy"
        ),
        ReduceLROnPlateau(
            factor=0.5,
            patience=2,
            min_lr=1e-7,
            monitor="val_accuracy"
        ),
        ModelCheckpoint(
            "models/waste_classifier_phase1.h5",
            save_best_only=True,
            monitor="val_accuracy"
        )
    ]
    
    print("🔄 Phase 1: Training classifier head (frozen base)")
    history = model.fit(
        train_gen,
        epochs=train_params["epochs_phase1"],
        validation_data=val_gen,
        callbacks=callbacks,
        verbose=1
    )
    
    # Log metrics per epoch
    for i, (tl, ta, vl, va) in enumerate(zip(
        history.history["loss"],
        history.history["accuracy"],
        history.history["val_loss"],
        history.history["val_accuracy"]
    )):
        mlflow.log_metrics({
            "p1_loss": tl,
            "p1_acc": ta,
            "p1_val_loss": vl,
            "p1_val_acc": va
        }, step=i)
    
    return history

def train_phase2(model, base_model, train_gen, val_gen, params, mlflow_run):
    """Phase 2: Fine-tune top layers"""
    train_params = params["train"]
    
    # Unfreeze top layers
    base_model.trainable = True
    for layer in base_model.layers[:-train_params["fine_tune_layers"]]:
        layer.trainable = False
    
    model.compile(
        optimizer=optimizers.Adam(train_params["lr_phase2"]),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    callbacks = [
        EarlyStopping(
            patience=6,
            restore_best_weights=True,
            monitor="val_accuracy"
        ),
        ReduceLROnPlateau(
            factor=0.3,
            patience=3,
            min_lr=1e-8,
            monitor="val_accuracy"
        ),
        ModelCheckpoint(
            "models/waste_classifier.h5",
            save_best_only=True,
            monitor="val_accuracy"
        )
    ]
    
    print("🔄 Phase 2: Fine-tuning top layers")
    history = model.fit(
        train_gen,
        epochs=train_params["epochs_phase2"],
        validation_data=val_gen,
        callbacks=callbacks,
        verbose=1
    )
    
    # Log metrics per epoch
    for i, (tl, ta, vl, va) in enumerate(zip(
        history.history["loss"],
        history.history["accuracy"],
        history.history["val_loss"],
        history.history["val_accuracy"]
    )):
        mlflow.log_metrics({
            "p2_loss": tl,
            "p2_acc": ta,
            "p2_val_loss": vl,
            "p2_val_acc": va
        }, step=i)
    
    return history

def evaluate_model(model, params, mlflow_run):
    """Evaluate model and log metrics"""
    prep_params = params["prepare"]
    
    # Create test generator
    test_datagen = ImageDataGenerator(rescale=1./255)
    test_gen = test_datagen.flow_from_directory(
        f"data/processed/test",
        target_size=(prep_params["img_size"], prep_params["img_size"]),
        batch_size=params["train"]["batch_size"],
        class_mode="categorical",
        shuffle=False
    )
    
    # Load best model
    model.load_weights("models/waste_classifier.h5")
    
    # Evaluate
    test_loss, test_acc = model.evaluate(test_gen)
    print(f"\n📊 Test Accuracy: {test_acc:.2%}")
    
    # Get predictions
    y_true = test_gen.classes
    y_pred = np.argmax(model.predict(test_gen), axis=1)
    
    # Classification report
    class_names = list(test_gen.class_indices.keys())
    report = classification_report(
        y_true, y_pred,
        target_names=class_names,
        output_dict=True
    )
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred).tolist()
    
    # Log final metrics
    final_metrics = {
        "test_accuracy": test_acc,
        "test_loss": test_loss,
        "test_precision": report["weighted avg"]["precision"],
        "test_recall": report["weighted avg"]["recall"],
        "test_f1": report["weighted avg"]["f1-score"],
        "target_met": test_acc >= 0.80
    }
    
    mlflow.log_metrics(final_metrics)
    
    # Log per-class metrics
    for cls in class_names:
        mlflow.log_metrics({
            f"{cls}_precision": report[cls]["precision"],
            f"{cls}_recall": report[cls]["recall"],
            f"{cls}_f1": report[cls]["f1-score"],
        })
    
    # Save metrics
    os.makedirs("metrics", exist_ok=True)
    with open("metrics/train_metrics.json", "w") as f:
        json.dump(final_metrics, f, indent=2)
    
    # Save confusion matrix
    import csv
    with open("metrics/confusion_matrix.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["actual", "predicted", "count"])
        for i, row in enumerate(cm):
            for j, count in enumerate(row):
                writer.writerow([class_names[i], class_names[j], count])
    
    return test_acc, report, cm

def export_models(model, params, mlflow_run):
    """Export models in different formats"""
    export_params = params["export"]
    
    # Save H5 model
    model.save(export_params["h5_path"])
    print(f"💾 H5 model saved: {export_params['h5_path']}")
    
    # Convert to TensorFlow Lite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    if export_params["optimize_for_mobile"]:
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    if export_params["quantize"]:
        converter.target_spec.supported_types = [tf.float16]
    
    tflite_model = converter.convert()
    
    with open(export_params["tflite_path"], "wb") as f:
        f.write(tflite_model)
    
    print(f"💾 TFLite model saved: {export_params['tflite_path']}")
    
    # Log artifacts to MLflow
    mlflow.log_artifact(export_params["h5_path"], artifact_path="models")
    mlflow.log_artifact(export_params["tflite_path"], artifact_path="models")
    mlflow.log_artifact("params.yaml")
    mlflow.log_artifact("metrics/confusion_matrix.csv", artifact_path="plots")
    
    # Register model in MLflow registry
    model_uri = f"runs:/{mlflow_run.info.run_id}/models/waste_classifier.h5"
    mv = mlflow.register_model(
        model_uri,
        params["mlflow"]["registry_name"]
    )
    
    # Promote to Staging if target met
    test_acc = json.load(open("metrics/train_metrics.json"))["test_accuracy"]
    if test_acc >= 0.80:
        client = mlflow.MlflowClient()
        client.transition_model_version_stage(
            name=params["mlflow"]["registry_name"],
            version=mv.version,
            stage="Staging"
        )
        print(f"🎯 Model v{mv.version} promoted to Staging")
    
    return mv

def get_dvc_hash():
    """Get current DVC/git hash for reproducibility"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"

def main():
    parser = argparse.ArgumentParser(description="Train SatsVerdant waste classifier")
    parser.add_argument("--export-only", action="store_true", help="Only export models")
    parser.add_argument("--resume", action="store_true", help="Resume training from checkpoint")
    args = parser.parse_args()
    
    # Load parameters
    params = load_params()
    
    # Create directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("metrics", exist_ok=True)
    
    if args.export_only:
        # Load existing model and export
        if os.path.exists("models/waste_classifier.h5"):
            model = tf.keras.models.load_model("models/waste_classifier.h5")
            export_models(model, params, None)
            print("✅ Models exported successfully")
        else:
            print("❌ No trained model found. Run training first.")
        return
    
    # Setup MLflow
    mlflow_run = setup_mlflow(params)
    
    with mlflow_run:
        # Log all parameters
        train_params = params["train"]
        aug_params = params["augmentation"]
        prep_params = params["prepare"]
        
        mlflow.log_params({
            "base_model": train_params["base_model"],
            "img_size": prep_params["img_size"],
            "batch_size": train_params["batch_size"],
            "epochs_phase1": train_params["epochs_phase1"],
            "epochs_phase2": train_params["epochs_phase2"],
            "lr_phase1": train_params["lr_phase1"],
            "lr_phase2": train_params["lr_phase2"],
            "dropout": train_params["dropout"],
            "fine_tune_layers": train_params["fine_tune_layers"],
            "dataset_size": 26000,
            "dataset_version": get_dvc_hash(),
            **{f"aug_{k}": v for k, v in aug_params.items()}
        })
        
        # Create data generators
        train_gen, val_gen = create_data_generators(params)
        
        # Create model
        model, base_model = create_model(params)
        
        # Phase 1 training
        train_phase1(model, train_gen, val_gen, params, mlflow_run)
        
        # Phase 2 training
        train_phase2(model, base_model, train_gen, val_gen, params, mlflow_run)
        
        # Evaluate model
        test_acc, report, cm = evaluate_model(model, params, mlflow_run)
        
        # Export models
        mv = export_models(model, params, mlflow_run)
        
        # Print final results
        print(f"\n🎉 Training Complete!")
        print(f"📊 Test Accuracy: {test_acc:.2%}")
        print(f"🎯 Target Met: {'✅ YES' if test_acc >= 0.80 else '❌ NO -- iterate'}")
        print(f"📝 MLflow Run: {mlflow_run.info.run_id}")
        print(f"🌐 DagsHub URL: https://dagshub.com/satsverdant/satsverdant-ml/mlflow")
        print(f"📦 Model Version: {mv.version}")

if __name__ == "__main__":
    main()
