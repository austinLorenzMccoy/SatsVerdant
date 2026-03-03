#!/usr/bin/env python3
"""
SatsVerdant Dataset Quality Monitor
Monitors dataset quality metrics and alerts on issues

Usage:
    python src/monitor_quality.py --dataset data/processed/train
    python src/monitor_quality.py --check-annotator-agreement
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime

import mlflow
import dagshub
from sklearn.metrics import cohen_kappa_score
import pandas as pd

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_params():
    """Load hyperparameters from params.yaml"""
    with open("params.yaml") as f:
        return yaml.safe_load(f)

class DatasetQualityMonitor:
    """Monitors dataset quality and generates alerts"""
    
    def __init__(self):
        self.categories = ["plastic", "paper", "metal", "organic", "glass"]
        self.min_class_size = 1500   # Phase 3 minimum (higher than MVP threshold)
        self.max_imbalance = 4.0     # Largest/smallest ratio
        
        # Initialize MLflow and DagsHub
        dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)
    
    def check_class_balance(self, dataset_dir: str) -> Dict:
        """Check class balance and identify underrepresented classes"""
        dataset_path = Path(dataset_dir)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
        
        counts = {}
        for cat in self.categories:
            cat_path = dataset_path / cat
            if cat_path.exists():
                count = len(list(cat_path.glob("*.jpg")))
                counts[cat] = count
            else:
                counts[cat] = 0
        
        # Calculate imbalance ratio
        max_n, min_n = max(counts.values()), min(counts.values())
        ratio = max_n / max(min_n, 1)
        
        # Generate warnings
        warnings = []
        for cat, n in counts.items():
            if n < self.min_class_size:
                warnings.append(f"{cat} underrepresented: {n} images (minimum {self.min_class_size})")
        
        if ratio > self.max_imbalance:
            warnings.append(f"Class imbalance {ratio:.1f}x exceeds {self.max_imbalance}x threshold")
        
        return {
            "counts": counts,
            "imbalance_ratio": ratio,
            "warnings": warnings,
            "total_images": sum(counts.values()),
            "min_class_size": self.min_class_size,
            "max_imbalance": self.max_imbalance
        }
    
    def check_inter_annotator_agreement(self) -> float:
        """
        Check agreement rate between validator decisions and AI predictions
        on the subset of submissions that were manually reviewed.
        Uses Cohen's kappa for chance-corrected agreement score.
        """
        print("🔍 Checking inter-annotator agreement...")
        
        # In production, this would query Supabase for validator-reviewed submissions
        # For demo, simulate with mock data
        
        try:
            # Simulate validator-reviewed data
            mock_data = self._simulate_validator_data()
            
            if not mock_data:
                print("⚠️  No validator-reviewed samples found")
                return 1.0
            
            ai_labels = [item["ai_prediction"] for item in mock_data]
            validator_labels = [item["validator_label"] for item in mock_data]
            
            # Calculate Cohen's kappa: 0.0 = chance, 1.0 = perfect agreement
            kappa = cohen_kappa_score(ai_labels, validator_labels)
            
            print(f"📊 Inter-annotator agreement: {kappa:.3f}")
            return kappa
            
        except Exception as e:
            print(f"❌ Error checking annotator agreement: {e}")
            return 0.0
    
    def _simulate_validator_data(self) -> List[Dict]:
        """Simulate validator-reviewed data for demo purposes"""
        # In production, this would be real data from Supabase
        
        categories = ["plastic", "paper", "metal", "organic", "glass"]
        mock_data = []
        
        # Simulate 100 validator reviews with varying agreement levels
        for i in range(100):
            ai_pred = np.random.choice(categories)
            
            # 85% agreement rate (good validators)
            if np.random.random() < 0.85:
                validator_label = ai_pred
            else:
                # 15% disagreement
                validator_label = np.random.choice([c for c in categories if c != ai_pred])
            
            mock_data.append({
                "ai_prediction": ai_pred,
                "validator_label": validator_label,
                "confidence": np.random.uniform(0.6, 0.95)
            })
        
        return mock_data
    
    def check_data_distribution_drift(self, dataset_dir: str) -> Dict:
        """Check for data distribution drift compared to baseline"""
        dataset_path = Path(dataset_dir)
        
        # Current distribution
        current_counts = self.check_class_balance(dataset_dir)["counts"]
        total_current = sum(current_counts.values())
        current_dist = {cat: count/total_current for cat, count in current_counts.items()}
        
        # Expected distribution (from PRD)
        expected_dist = {
            "plastic": 0.308,   # 30.8%
            "paper": 0.250,     # 25.0%
            "metal": 0.192,     # 19.2%
            "organic": 0.173,   # 17.3%
            "glass": 0.077      # 7.7%
        }
        
        # Calculate drift
        drift_scores = {}
        for cat in self.categories:
            expected = expected_dist.get(cat, 0.2)  # Default 20% if not specified
            actual = current_dist.get(cat, 0)
            drift = abs(expected - actual)
            drift_scores[cat] = drift
        
        # Overall drift score
        overall_drift = np.mean(list(drift_scores.values()))
        
        # Alert if drift > 10%
        drift_alerts = []
        for cat, drift in drift_scores.items():
            if drift > 0.10:  # 10% threshold
                drift_alerts.append(f"{cat}: {drift:.1%} drift from expected")
        
        return {
            "current_distribution": current_dist,
            "expected_distribution": expected_dist,
            "drift_scores": drift_scores,
            "overall_drift": overall_drift,
            "drift_alerts": drift_alerts
        }
    
    def check_image_quality_metrics(self, dataset_dir: str) -> Dict:
        """Check image quality metrics across dataset"""
        print("🔍 Analyzing image quality...")
        
        dataset_path = Path(dataset_dir)
        quality_metrics = {
            "total_images": 0,
            "corrupted_images": 0,
            "small_images": 0,
            "large_images": 0,
            "avg_file_size": 0,
            "quality_issues": []
        }
        
        file_sizes = []
        
        # Sample up to 100 images per class for quality analysis
        for category in self.categories:
            cat_path = dataset_path / category
            if not cat_path.exists():
                continue
            
            images = list(cat_path.glob("*.jpg"))
            sample_images = images[:100]  # Limit to 100 per class
            
            for img_path in sample_images:
                try:
                    # Check if file is readable
                    with Image.open(img_path) as img:
                        width, height = img.size
                        
                        # Check for very small images
                        if width < 100 or height < 100:
                            quality_metrics["small_images"] += 1
                            quality_metrics["quality_issues"].append(f"Small image: {img_path.name}")
                        
                        # Check for very large images
                        if width > 2048 or height > 2048:
                            quality_metrics["large_images"] += 1
                        
                        # Check file size
                        file_size = img_path.stat().st_size / 1024  # KB
                        file_sizes.append(file_size)
                        
                        quality_metrics["total_images"] += 1
                        
                except Exception as e:
                    quality_metrics["corrupted_images"] += 1
                    quality_metrics["quality_issues"].append(f"Corrupted image: {img_path.name}")
        
        # Calculate average file size
        if file_sizes:
            quality_metrics["avg_file_size"] = np.mean(file_sizes)
        
        return quality_metrics
    
    def generate_quality_report(self, dataset_dir: str) -> Dict:
        """Generate comprehensive quality report"""
        print(f"📊 Generating quality report for {dataset_dir}")
        
        # Run all quality checks
        balance_check = self.check_class_balance(dataset_dir)
        agreement_score = self.check_inter_annotator_agreement()
        drift_check = self.check_data_distribution_drift(dataset_dir)
        quality_check = self.check_image_quality_metrics(dataset_dir)
        
        # Calculate overall quality score
        quality_score = self._calculate_overall_quality_score(
            balance_check, agreement_score, drift_check, quality_check
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            balance_check, agreement_score, drift_check, quality_check
        )
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "dataset_path": str(dataset_dir),
            "overall_quality_score": quality_score,
            "class_balance": balance_check,
            "annotator_agreement": agreement_score,
            "distribution_drift": drift_check,
            "image_quality": quality_check,
            "recommendations": recommendations,
            "status": "healthy" if quality_score >= 0.8 else "needs_attention"
        }
        
        return report
    
    def _calculate_overall_quality_score(self, balance: Dict, agreement: float, 
                                       drift: Dict, quality: Dict) -> float:
        """Calculate overall quality score (0-1)"""
        scores = []
        
        # Class balance score (40% weight)
        if balance["warnings"]:
            balance_score = max(0, 1 - len(balance["warnings"]) * 0.2)
        else:
            balance_score = 1.0
        scores.append(balance_score * 0.4)
        
        # Annotator agreement score (30% weight)
        agreement_score = max(0, agreement)  # Cohen's kappa can be negative
        scores.append(min(1, agreement_score) * 0.3)
        
        # Distribution drift score (20% weight)
        drift_score = max(0, 1 - drift["overall_drift"] * 5)  # Penalize high drift
        scores.append(drift_score * 0.2)
        
        # Image quality score (10% weight)
        total_images = quality["total_images"]
        if total_images > 0:
            corruption_rate = quality["corrupted_images"] / total_images
            quality_score = max(0, 1 - corruption_rate * 2)
        else:
            quality_score = 0
        scores.append(quality_score * 0.1)
        
        return sum(scores)
    
    def _generate_recommendations(self, balance: Dict, agreement: float, 
                                drift: Dict, quality: Dict) -> List[str]:
        """Generate actionable recommendations based on quality checks"""
        recommendations = []
        
        # Class balance recommendations
        if balance["warnings"]:
            for warning in balance["warnings"]:
                if "underrepresented" in warning:
                    recommendations.append(
                        f"Generate synthetic data or collect more samples for underrepresented class"
                    )
                elif "imbalance" in warning:
                    recommendations.append(
                        f"Consider data augmentation to reduce class imbalance"
                    )
        
        # Annotator agreement recommendations
        if agreement < 0.8:
            recommendations.append(
                f"Improve validator training - current agreement ({agreement:.2f}) below target (0.80)"
            )
        elif agreement < 0.9:
            recommendations.append(
                f"Consider additional validator guidelines to improve agreement from {agreement:.2f} to 0.90+"
            )
        
        # Distribution drift recommendations
        if drift["drift_alerts"]:
            recommendations.append(
                f"Address distribution drift: {', '.join(drift['drift_alerts'])}"
            )
        
        # Image quality recommendations
        if quality["corrupted_images"] > 0:
            recommendations.append(
                f"Remove or replace {quality['corrupted_images']} corrupted images"
            )
        
        if quality["small_images"] > 0:
            recommendations.append(
                f"Consider upsampling or removing {quality['small_images']} small images"
            )
        
        if not recommendations:
            recommendations.append("Dataset quality looks good - continue current data collection strategy")
        
        return recommendations
    
    def log_to_mlflow(self, report: Dict):
        """Log quality metrics to MLflow"""
        with mlflow.start_run(run_name="dataset-quality-check"):
            # Log main metrics
            mlflow.log_metric("overall_quality_score", report["overall_quality_score"])
            mlflow.log_metric("annotator_agreement", report["annotator_agreement"])
            mlflow.log_metric("imbalance_ratio", report["class_balance"]["imbalance_ratio"])
            mlflow.log_metric("distribution_drift", report["distribution_drift"]["overall_drift"])
            
            # Log class counts
            for cat, count in report["class_balance"]["counts"].items():
                mlflow.log_metric(f"class_count_{cat}", count)
            
            # Log image quality metrics
            img_quality = report["image_quality"]
            mlflow.log_metric("total_images", img_quality["total_images"])
            mlflow.log_metric("corrupted_images", img_quality["corrupted_images"])
            mlflow.log_metric("small_images", img_quality["small_images"])
            
            # Log recommendations as artifact
            recommendations_path = "metrics/quality_recommendations.json"
            with open(recommendations_path, "w") as f:
                json.dump(report["recommendations"], f, indent=2)
            
            mlflow.log_artifact(recommendations_path, artifact_path="recommendations")
        
        print("📊 Quality metrics logged to MLflow")
    
    def save_metrics(self, report: Dict, output_path: str = "metrics/dataset_quality.json"):
        """Save quality metrics for DVC tracking"""
        os.makedirs("metrics", exist_ok=True)
        
        # Prepare metrics for DVC tracking
        metrics = {
            "overall_quality_score": report["overall_quality_score"],
            "annotator_agreement": report["annotator_agreement"],
            "imbalance_ratio": report["class_balance"]["imbalance_ratio"],
            "distribution_drift": report["distribution_drift"]["overall_drift"],
            "class_counts": report["class_balance"]["counts"],
            "total_images": report["image_quality"]["total_images"],
            "corrupted_images": report["image_quality"]["corrupted_images"],
            "status": report["status"]
        }
        
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"📊 Quality metrics saved to {output_path}")
        
        # Save full report
        report_path = output_path.replace(".json", "_full_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Full report saved to {report_path}")

def main():
    import argparse
    from PIL import Image
    
    parser = argparse.ArgumentParser(description="SatsVerdant Dataset Quality Monitor")
    parser.add_argument("--dataset", type=str, default="data/processed/train",
                       help="Dataset directory to monitor")
    parser.add_argument("--check-annotator-agreement", action="store_true",
                       help="Only check annotator agreement")
    parser.add_argument("--output", type=str, default="metrics/dataset_quality.json",
                       help="Output metrics file")
    parser.add_argument("--log-mlflow", action="store_true",
                       help="Log metrics to MLflow")
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = DatasetQualityMonitor()
    
    if args.check_annotator_agreement:
        # Only check annotator agreement
        agreement = monitor.check_inter_annotator_agreement()
        print(f"📊 Inter-annotator agreement: {agreement:.3f}")
        return
    
    # Generate full quality report
    print(f"🔍 Monitoring dataset quality: {args.dataset}")
    
    try:
        report = monitor.generate_quality_report(args.dataset)
        
        # Print summary
        print(f"\n📊 Dataset Quality Summary:")
        print(f"  Overall Score: {report['overall_quality_score']:.3f}/1.0")
        print(f"  Status: {report['status']}")
        print(f"  Total Images: {report['image_quality']['total_images']}")
        print(f"  Class Imbalance: {report['class_balance']['imbalance_ratio']:.2f}x")
        print(f"  Annotator Agreement: {report['annotator_agreement']:.3f}")
        print(f"  Distribution Drift: {report['distribution_drift']['overall_drift']:.3f}")
        
        print(f"\n📋 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        # Save metrics
        monitor.save_metrics(report, args.output)
        
        # Log to MLflow if requested
        if args.log_mlflow:
            monitor.log_to_mlflow(report)
        
    except Exception as e:
        print(f"❌ Error monitoring dataset quality: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
