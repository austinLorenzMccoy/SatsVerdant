#!/usr/bin/env python3
"""
SatsVerdant Model Evaluation Script
Evaluates trained model and generates comprehensive metrics

Usage:
    python src/evaluate.py [--model-path PATH] [--output-dir DIR]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    precision_recall_fscore_support, roc_auc_score
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tqdm import tqdm

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_model(model_path: str = "models/waste_classifier.h5"):
    """Load trained model"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    model = tf.keras.models.load_model(model_path)
    print(f"✅ Model loaded from {model_path}")
    return model

def create_test_generator(img_size: int = 224, batch_size: int = 32):
    """Create test data generator"""
    test_datagen = ImageDataGenerator(rescale=1./255)
    
    test_gen = test_datagen.flow_from_directory(
        "data/processed/test",
        target_size=(img_size, img_size),
        batch_size=batch_size,
        class_mode="categorical",
        shuffle=False
    )
    
    return test_gen

def evaluate_model(model, test_gen):
    """Evaluate model and return metrics"""
    print("🔍 Evaluating model...")
    
    # Basic evaluation
    test_loss, test_acc = model.evaluate(test_gen)
    print(f"📊 Test Loss: {test_loss:.4f}")
    print(f"📊 Test Accuracy: {test_acc:.4f}")
    
    # Get predictions
    print("🔮 Generating predictions...")
    y_true = test_gen.classes
    y_pred_proba = model.predict(test_gen)
    y_pred = np.argmax(y_pred_proba, axis=1)
    
    # Class names
    class_names = list(test_gen.class_indices.keys())
    
    return {
        "test_loss": test_loss,
        "test_accuracy": test_acc,
        "y_true": y_true,
        "y_pred": y_pred,
        "y_pred_proba": y_pred_proba,
        "class_names": class_names
    }

def calculate_per_class_metrics(y_true, y_pred, class_names):
    """Calculate per-class precision, recall, F1"""
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, zero_division=0
    )
    
    per_class_metrics = {}
    for i, class_name in enumerate(class_names):
        per_class_metrics[class_name] = {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1_score": float(f1[i]),
            "support": int(support[i])
        }
    
    return per_class_metrics

def create_confusion_matrix(y_true, y_pred, class_names):
    """Create and save confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    
    # Create heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    
    # Save plot
    os.makedirs("metrics/plots", exist_ok=True)
    plt.savefig("metrics/plots/confusion_matrix.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save CSV for DVC tracking
    cm_data = []
    for i, true_class in enumerate(class_names):
        for j, pred_class in enumerate(class_names):
            cm_data.append({
                "actual": true_class,
                "predicted": pred_class,
                "count": int(cm[i][j])
            })
    
    cm_df = pd.DataFrame(cm_data)
    cm_df.to_csv("metrics/confusion_matrix.csv", index=False)
    
    return cm

def analyze_errors(y_true, y_pred, y_pred_proba, class_names):
    """Analyze prediction errors"""
    errors = []
    
    for i, (true, pred) in enumerate(zip(y_true, y_pred)):
        if true != pred:
            confidence = float(np.max(y_pred_proba[i]))
            true_class = class_names[true]
            pred_class = class_names[pred]
            
            errors.append({
                "index": i,
                "true_class": true_class,
                "pred_class": pred_class,
                "confidence": confidence,
                "true_prob": float(y_pred_proba[i][true]),
                "pred_prob": float(y_pred_proba[i][pred])
            })
    
    # Sort by confidence
    errors.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Error analysis
    error_analysis = {
        "total_errors": len(errors),
        "error_rate": len(errors) / len(y_true),
        "high_confidence_errors": len([e for e in errors if e["confidence"] > 0.8]),
        "low_confidence_correct": len([
            i for i in range(len(y_true)) 
            if y_true[i] == y_pred[i] and np.max(y_pred_proba[i]) < 0.6
        ]),
        "common_confusions": {}
    }
    
    # Find common confusions
    for error in errors:
        confusion = f"{error['true_class']} → {error['pred_class']}"
        if confusion not in error_analysis["common_confusions"]:
            error_analysis["common_confusions"][confusion] = 0
        error_analysis["common_confusions"][confusion] += 1
    
    # Sort common confusions
    error_analysis["common_confusions"] = dict(
        sorted(error_analysis["common_confusions"].items(), 
               key=lambda x: x[1], reverse=True)[:10]
    )
    
    return errors, error_analysis

def create_class_performance_plot(per_class_metrics):
    """Create per-class performance plot"""
    classes = list(per_class_metrics.keys())
    precision = [per_class_metrics[cls]["precision"] for cls in classes]
    recall = [per_class_metrics[cls]["recall"] for cls in classes]
    f1 = [per_class_metrics[cls]["f1_score"] for cls in classes]
    
    x = np.arange(len(classes))
    width = 0.25
    
    plt.figure(figsize=(12, 6))
    plt.bar(x - width, precision, width, label='Precision', alpha=0.8)
    plt.bar(x, recall, width, label='Recall', alpha=0.8)
    plt.bar(x + width, f1, width, label='F1-Score', alpha=0.8)
    
    plt.xlabel('Classes')
    plt.ylabel('Score')
    plt.title('Per-Class Performance Metrics')
    plt.xticks(x, classes, rotation=45)
    plt.legend()
    plt.tight_layout()
    
    os.makedirs("metrics/plots", exist_ok=True)
    plt.savefig("metrics/plots/per_class_metrics.png", dpi=300, bbox_inches='tight')
    plt.close()

def save_evaluation_results(results, per_class_metrics, error_analysis):
    """Save comprehensive evaluation results"""
    # Main metrics
    eval_metrics = {
        "test_loss": results["test_loss"],
        "test_accuracy": results["test_accuracy"],
        "test_precision": np.mean([m["precision"] for m in per_class_metrics.values()]),
        "test_recall": np.mean([m["recall"] for m in per_class_metrics.values()]),
        "test_f1": np.mean([m["f1_score"] for m in per_class_metrics.values()]),
        "target_met": results["test_accuracy"] >= 0.80,
        "per_class_metrics": per_class_metrics,
        "error_analysis": error_analysis,
        "class_distribution": {
            class_name: per_class_metrics[class_name]["support"]
            for class_name in per_class_metrics.keys()
        }
    }
    
    # Save metrics
    os.makedirs("metrics", exist_ok=True)
    with open("metrics/eval_metrics.json", "w") as f:
        json.dump(eval_metrics, f, indent=2)
    
    # Save per-class CSV
    per_class_data = []
    for class_name, metrics in per_class_metrics.items():
        per_class_data.append({
            "class": class_name,
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1_score"],
            "support": metrics["support"]
        })
    
    per_class_df = pd.DataFrame(per_class_data)
    per_class_df.to_csv("metrics/per_class_metrics.csv", index=False)
    
    print("📋 Evaluation results saved to metrics/eval_metrics.json")
    print("📊 Per-class metrics saved to metrics/per_class_metrics.csv")

def print_summary(results, per_class_metrics, error_analysis):
    """Print evaluation summary"""
    print("\n" + "="*60)
    print("🎯 SATSVERDANT MODEL EVALUATION SUMMARY")
    print("="*60)
    
    print(f"\n📊 Overall Performance:")
    print(f"  Test Accuracy: {results['test_accuracy']:.4f} ({results['test_accuracy']:.2%})")
    print(f"  Test Loss: {results['test_loss']:.4f}")
    print(f"  Target Met (≥80%): {'✅ YES' if results['test_accuracy'] >= 0.80 else '❌ NO'}")
    
    print(f"\n📈 Average Metrics:")
    avg_precision = np.mean([m["precision"] for m in per_class_metrics.values()])
    avg_recall = np.mean([m["recall"] for m in per_class_metrics.values()])
    avg_f1 = np.mean([m["f1_score"] for m in per_class_metrics.values()])
    
    print(f"  Precision: {avg_precision:.4f}")
    print(f"  Recall: {avg_recall:.4f}")
    print(f"  F1-Score: {avg_f1:.4f}")
    
    print(f"\n🏆 Best Performing Classes:")
    sorted_by_f1 = sorted(per_class_metrics.items(), key=lambda x: x[1]["f1_score"], reverse=True)
    for class_name, metrics in sorted_by_f1[:3]:
        print(f"  {class_name}: F1={metrics['f1_score']:.3f}, P={metrics['precision']:.3f}, R={metrics['recall']:.3f}")
    
    print(f"\n⚠️  Worst Performing Classes:")
    for class_name, metrics in sorted_by_f1[-3:]:
        print(f"  {class_name}: F1={metrics['f1_score']:.3f}, P={metrics['precision']:.3f}, R={metrics['recall']:.3f}")
    
    print(f"\n🔍 Error Analysis:")
    print(f"  Total Errors: {error_analysis['total_errors']} ({error_analysis['error_rate']:.2%})")
    print(f"  High Confidence Errors: {error_analysis['high_confidence_errors']}")
    print(f"  Low Confidence Correct: {error_analysis['low_confidence_correct']}")
    
    print(f"\n🔄 Common Confusions:")
    for confusion, count in list(error_analysis['common_confusions'].items())[:5]:
        print(f"  {confusion}: {count} times")
    
    print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description="Evaluate SatsVerdant model")
    parser.add_argument("--model-path", default="models/waste_classifier.h5", help="Path to trained model")
    parser.add_argument("--output-dir", default="metrics", help="Output directory for results")
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Load model
        model = load_model(args.model_path)
        
        # Create test generator
        test_gen = create_test_generator()
        
        # Evaluate model
        results = evaluate_model(model, test_gen)
        
        # Calculate per-class metrics
        per_class_metrics = calculate_per_class_metrics(
            results["y_true"], results["y_pred"], results["class_names"]
        )
        
        # Create confusion matrix
        confusion_mat = create_confusion_matrix(
            results["y_true"], results["y_pred"], results["class_names"]
        )
        
        # Analyze errors
        errors, error_analysis = analyze_errors(
            results["y_true"], results["y_pred"], 
            results["y_pred_proba"], results["class_names"]
        )
        
        # Create performance plots
        create_class_performance_plot(per_class_metrics)
        
        # Save results
        save_evaluation_results(results, per_class_metrics, error_analysis)
        
        # Print summary
        print_summary(results, per_class_metrics, error_analysis)
        
        print(f"\n✅ Evaluation complete! Results saved to {args.output_dir}/")
        
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
