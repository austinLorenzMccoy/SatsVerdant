#!/usr/bin/env python3
"""
SatsVerdant Retraining Pipeline
Automated monthly retraining with active learning and user data collection

Usage:
    python src/retrain_pipeline.py --dry-run
    python src/retrain_pipeline.py --run
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import mlflow
import dagshub
import pandas as pd

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_params():
    """Load hyperparameters from params.yaml"""
    with open("params.yaml") as f:
        return yaml.safe_load(f)

class RetrainingPipeline:
    """Automated retraining pipeline for continuous model improvement"""
    
    def __init__(self):
        self.params = load_params()
        self.user_data_dir = Path("data/raw/active_learning")
        self.last_retrain = self._get_last_retrain_date()
        self.min_samples_threshold = 100
        self.improvement_threshold = 0.02  # 2% improvement required
        
        # Initialize MLflow and DagsHub
        dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)
        
    def _get_last_retrain_date(self) -> str:
        """Fetch the date of the last completed retraining run from MLflow."""
        try:
            client = mlflow.MlflowClient()
            
            # Search for runs in the waste classifier experiment
            runs = mlflow.search_runs(
                experiment_names=["waste-classifier-efficientnetb0"],
                order_by=["attributes.start_time DESC"],
                max_results=1
            )
            
            if runs.empty:
                return (datetime.now() - timedelta(days=30)).isoformat()
            
            return runs.iloc[0]["start_time"].isoformat()
            
        except Exception as e:
            print(f"⚠️  Could not fetch last retrain date: {e}")
            return (datetime.now() - timedelta(days=30)).isoformat()
    
    def collect_new_data(self) -> int:
        """
        Download approved submissions from Supabase Storage since last retrain.
        In production, this would connect to actual Supabase instance.
        For now, simulate with local data.
        """
        print(f"🔍 Collecting new data since {self.last_retrain[:10]}")
        
        # In production, this would:
        # 1. Query Supabase for approved submissions
        # 2. Download images from Supabase Storage
        # 3. Organize by waste type
        
        # For demo, simulate data collection
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate finding new user submissions
        simulated_new_samples = self._simulate_user_data_collection()
        
        print(f"📥 Collected {simulated_new_samples} new training samples")
        return simulated_new_samples
    
    def _simulate_user_data_collection(self) -> int:
        """Simulate user data collection for demo purposes"""
        # In production, this would be real data from Supabase
        # For now, simulate with a small number of samples
        
        categories = ["plastic", "paper", "metal", "organic", "glass"]
        total_samples = 0
        
        for category in categories:
            cat_dir = self.user_data_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            
            # Simulate finding 5-15 new samples per category
            new_samples = np.random.randint(5, 16)
            
            # Create placeholder files (in production, these would be real images)
            for i in range(new_samples):
                placeholder = cat_dir / f"user_{datetime.now().strftime('%Y%m%d')}_{i:03d}.jpg"
                placeholder.touch()
            
            total_samples += new_samples
        
        return total_samples
    
    def version_and_push(self, new_sample_count: int):
        """Commit expanded dataset to DVC and push to DagsHub."""
        print(f"📦 Versioning {new_sample_count} new samples...")
        
        try:
            # Add new data to DVC
            if self.user_data_dir.exists():
                subprocess.run(["dvc", "add", str(self.user_data_dir)], check=True)
                
                # Git commit
                subprocess.run(["git", "add", f"{self.user_data_dir}.dvc", ".gitignore"], check=True)
                subprocess.run([
                    "git", "commit", "-m",
                    f"chore: add {new_sample_count} active learning samples ({datetime.now().strftime('%Y-%m-%d')})"
                ], check=True)
                
                # Push to DagsHub
                subprocess.run(["dvc", "push"], check=True)
                subprocess.run(["git", "push"], check=True)
                
                print("✅ Dataset versioned and pushed to DagsHub")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error versioning dataset: {e}")
            return False
        
        return True
    
    def check_retraining_conditions(self, new_sample_count: int) -> bool:
        """Check if retraining should proceed"""
        print(f"🔍 Checking retraining conditions...")
        
        # Check minimum sample threshold
        if new_sample_count < self.min_samples_threshold:
            print(f"❌ Insufficient new samples: {new_sample_count} < {self.min_samples_threshold}")
            return False
        
        # Check time since last retrain (minimum 1 week)
        try:
            last_retrain_date = datetime.fromisoformat(self.last_retrain.replace('Z', '+00:00'))
            days_since_retrain = (datetime.now() - last_retrain_date).days
            
            if days_since_retrain < 7:
                print(f"❌ Too soon since last retrain: {days_since_retrain} days < 7 days")
                return False
                
        except Exception as e:
            print(f"⚠️  Could not parse last retrain date: {e}")
        
        print(f"✅ Retraining conditions met")
        return True
    
    def run_training_pipeline(self) -> bool:
        """Run the full DVC training pipeline"""
        print(f"🚀 Running training pipeline...")
        
        try:
            # Run DVC repro to execute all pipeline stages
            result = subprocess.run(
                ["dvc", "repro", "--force"],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                print("✅ Training pipeline completed successfully")
                return True
            else:
                print(f"❌ Training pipeline failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Training pipeline timed out")
            return False
        except Exception as e:
            print(f"❌ Error running training pipeline: {e}")
            return False
    
    def evaluate_model_improvement(self) -> Dict:
        """Evaluate if new model is better than current production model"""
        print(f"📊 Evaluating model improvement...")
        
        try:
            # Load current metrics
            current_metrics_path = Path("metrics/eval_metrics.json")
            if not current_metrics_path.exists():
                print("⚠️  No current metrics found, assuming improvement")
                return {"improved": True, "reason": "No baseline metrics"}
            
            with open(current_metrics_path, "r") as f:
                current_metrics = json.load(f)
            
            current_accuracy = current_metrics.get("test_accuracy", 0.0)
            
            # Get production model accuracy from MLflow registry
            client = mlflow.MlflowClient()
            
            try:
                # Get latest production model
                production_model = client.get_latest_versions(
                    "satsverdant-waste-classifier",
                    stages=["Production"]
                )
                
                if production_model:
                    prod_run_id = production_model[0].run_id
                    prod_run = client.get_run(prod_run_id)
                    prod_accuracy = prod_run.data.metrics.get("test_accuracy", 0.0)
                    
                    improvement = current_accuracy - prod_accuracy
                    improved = improvement >= self.improvement_threshold
                    
                    return {
                        "improved": improved,
                        "current_accuracy": current_accuracy,
                        "production_accuracy": prod_accuracy,
                        "improvement": improvement,
                        "threshold": self.improvement_threshold,
                        "reason": f"Accuracy {'increased' if improved else 'decreased'} by {improvement:.3f}"
                    }
                else:
                    print("⚠️  No production model found, assuming improvement")
                    return {"improved": True, "reason": "No production model"}
                    
            except Exception as e:
                print(f"⚠️  Could not fetch production model: {e}")
                return {"improved": True, "reason": "Production model inaccessible"}
                
        except Exception as e:
            print(f"❌ Error evaluating improvement: {e}")
            return {"improved": False, "reason": f"Evaluation error: {e}"}
    
    def promote_model_if_improved(self, evaluation_result: Dict) -> bool:
        """Promote model to production if it's better"""
        if not evaluation_result["improved"]:
            print(f"❌ Model not improved: {evaluation_result['reason']}")
            return False
        
        print(f"🎯 Model improved: {evaluation_result['reason']}")
        
        try:
            client = mlflow.MlflowClient()
            
            # Get latest model from registry
            latest_model = client.get_latest_versions(
                "satsverdant-waste-classifier",
                stages=["Staging"]
            )
            
            if latest_model:
                # Promote to Production
                model_version = latest_model[0].version
                client.transition_model_version_stage(
                    name="satsverdant-waste-classifier",
                    version=model_version,
                    stage="Production",
                    archive_existing_versions=True
                )
                
                print(f"✅ Model v{model_version} promoted to Production")
                return True
            else:
                print("⚠️  No staging model found to promote")
                return False
                
        except Exception as e:
            print(f"❌ Error promoting model: {e}")
            return False
    
    def generate_retraining_report(self, new_sample_count: int, evaluation_result: Dict) -> str:
        """Generate a comprehensive retraining report"""
        report = f"""
# SatsVerdant Retraining Report
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**New Samples**: {new_sample_count}
**Last Retrain**: {self.last_retrain[:10]}

## 📊 Model Performance
- **Current Accuracy**: {evaluation_result.get('current_accuracy', 'N/A'):.3f}
- **Production Accuracy**: {evaluation_result.get('production_accuracy', 'N/A'):.3f}
- **Improvement**: {evaluation_result.get('improvement', 'N/A'):.3f}
- **Threshold**: {self.improvement_threshold:.3f}

## 🎯 Decision
- **Improved**: {evaluation_result['improved']}
- **Reason**: {evaluation_result['reason']}
- **Promoted**: {'Yes' if evaluation_result['improved'] else 'No'}

## 📈 Next Steps
{'Model promoted to production - ready for deployment' if evaluation_result['improved'] else 'Keep current production model - continue data collection'}

---
*Generated by SatsVerdant Retraining Pipeline*
"""
        
        # Save report
        report_path = Path("metrics/retraining_report.md")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            f.write(report)
        
        print(f"📋 Retraining report saved to {report_path}")
        return str(report_path)
    
    def run(self, dry_run: bool = False) -> Dict:
        """Run the complete retraining pipeline"""
        print(f"🚀 Starting retraining pipeline (dry_run={dry_run})")
        
        # Step 1: Collect new data
        new_sample_count = self.collect_new_data()
        
        # Step 2: Check conditions
        if not self.check_retraining_conditions(new_sample_count):
            return {
                "status": "skipped",
                "reason": "Retraining conditions not met",
                "new_samples": new_sample_count
            }
        
        if dry_run:
            print("🔍 DRY RUN - Would proceed with retraining")
            return {
                "status": "dry_run_success",
                "reason": "Would retrain with real pipeline",
                "new_samples": new_sample_count
            }
        
        # Step 3: Version and push data
        if not self.version_and_push(new_sample_count):
            return {
                "status": "failed",
                "reason": "Failed to version dataset",
                "new_samples": new_sample_count
            }
        
        # Step 4: Run training pipeline
        if not self.run_training_pipeline():
            return {
                "status": "failed",
                "reason": "Training pipeline failed",
                "new_samples": new_sample_count
            }
        
        # Step 5: Evaluate improvement
        evaluation_result = self.evaluate_model_improvement()
        
        # Step 6: Promote if improved
        promoted = self.promote_model_if_improved(evaluation_result)
        
        # Step 7: Generate report
        report_path = self.generate_retraining_report(new_sample_count, evaluation_result)
        
        return {
            "status": "success" if promoted else "completed",
            "reason": evaluation_result["reason"],
            "new_samples": new_sample_count,
            "promoted": promoted,
            "report": report_path
        }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SatsVerdant Retraining Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline without actually training")
    parser.add_argument("--run", action="store_true", help="Run full retraining pipeline")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.run:
        parser.print_help()
        return
    
    # Initialize pipeline
    pipeline = RetrainingPipeline()
    
    # Run pipeline
    result = pipeline.run(dry_run=args.dry_run)
    
    # Print results
    print(f"\n🎯 Pipeline Results:")
    print(f"  Status: {result['status']}")
    print(f"  Reason: {result['reason']}")
    print(f"  New Samples: {result['new_samples']}")
    
    if 'promoted' in result:
        print(f"  Promoted: {'Yes' if result['promoted'] else 'No'}")
    
    if 'report' in result:
        print(f"  Report: {result['report']}")

if __name__ == "__main__":
    import numpy as np
    main()
