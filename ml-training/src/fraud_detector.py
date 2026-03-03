#!/usr/bin/env python3
"""
SatsVerdant Fraud Detection System
Analyzes submissions for fraud patterns using perceptual hashing and rate limiting

Usage:
    python src/fraud_detector.py --analyze
    python src/fraud_detector.py --check-submission /path/to/image.jpg --user-id user123
"""

import os
import sys
import argparse
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set
import numpy as np
from datetime import datetime, timedelta

import cv2
import imagehash
from PIL import Image
import pandas as pd

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_params():
    """Load hyperparameters from params.yaml"""
    with open("params.yaml") as f:
        return yaml.safe_load(f)

class FraudDetector:
    """Detects fraudulent submissions using multiple signals"""
    
    def __init__(self, params: Dict):
        self.fraud_params = params["fraud"]
        self.hash_threshold = self.fraud_params["hash_threshold"]
        self.rate_limit_per_hour = self.fraud_params["rate_limit_per_hour"]
        self.min_confidence = self.fraud_params["min_confidence"]
        self.max_fraud_score = self.fraud_params["max_fraud_score"]
        
        # In-memory storage for demo (in production, use database)
        self.submission_hashes = {}  # user_id -> list of hashes
        self.submission_times = {}   # user_id -> list of timestamps
        self.known_hashes = set()    # global hash database
        
    def calculate_perceptual_hash(self, image_path: str) -> str:
        """Calculate perceptual hash for image similarity detection"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate pHash (perceptual hash)
                phash = imagehash.phash(img)
                return str(phash)
        except Exception as e:
            print(f"Error calculating hash for {image_path}: {e}")
            return ""
    
    def calculate_dhash(self, image_path: str) -> str:
        """Calculate difference hash for additional similarity detection"""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                dhash = imagehash.dhash(img)
                return str(dhash)
        except Exception:
            return ""
    
    def calculate_average_hash(self, image_path: str) -> str:
        """Calculate average hash for robust similarity detection"""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                ahash = imagehash.average_hash(img)
                return str(ahash)
        except Exception:
            return ""
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hashes"""
        if len(hash1) != len(hash2):
            return float('inf')
        
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def check_duplicate_submission(self, image_path: str, user_id: str) -> Dict:
        """Check if image is a duplicate of previous submissions"""
        hashes = {
            'phash': self.calculate_perceptual_hash(image_path),
            'dhash': self.calculate_dhash(image_path),
            'ahash': self.calculate_average_hash(image_path)
        }
        
        if not all(hashes.values()):
            return {"is_duplicate": False, "reason": "Hash calculation failed"}
        
        # Check against user's own submissions
        user_hashes = self.submission_hashes.get(user_id, [])
        duplicate_info = {"is_duplicate": False, "reason": "", "similar_images": []}
        
        for hash_type, current_hash in hashes.items():
            for stored_hash in user_hashes:
                distance = self.hamming_distance(current_hash, stored_hash)
                if distance <= self.hash_threshold:
                    duplicate_info["is_duplicate"] = True
                    duplicate_info["reason"] = f"Duplicate detected via {hash_type} (distance: {distance})"
                    duplicate_info["similar_images"].append({
                        "hash_type": hash_type,
                        "distance": distance,
                        "stored_hash": stored_hash
                    })
                    break
        
        return duplicate_info
    
    def check_rate_limit(self, user_id: str) -> Dict:
        """Check if user is submitting too frequently"""
        current_time = datetime.now()
        user_times = self.submission_times.get(user_id, [])
        
        # Filter submissions from last hour
        recent_submissions = [
            time for time in user_times 
            if current_time - time <= timedelta(hours=1)
        ]
        
        rate_info = {
            "is_rate_limited": len(recent_submissions) >= self.rate_limit_per_hour,
            "recent_count": len(recent_submissions),
            "hourly_limit": self.rate_limit_per_hour,
            "oldest_recent": min(recent_submissions) if recent_submissions else None
        }
        
        if rate_info["is_rate_limited"]:
            rate_info["reason"] = f"Rate limit exceeded: {rate_info['recent_count']}/{rate_info['hourly_limit']} per hour"
        
        return rate_info
    
    def check_image_quality_fraud(self, image_path: str) -> Dict:
        """Check for common fraud patterns in image quality"""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return {"is_suspicious": True, "reason": "Cannot read image"}
            
            # Check for extremely low resolution
            height, width = img.shape[:2]
            if width < 200 or height < 200:
                return {"is_suspicious": True, "reason": f"Very low resolution: {width}x{height}"}
            
            # Check for completely black/white images
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            unique_pixels = len(np.unique(gray))
            if unique_pixels < 10:
                return {"is_suspicious": True, "reason": f"Low color variety: {unique_pixels} unique pixels"}
            
            # Check for extreme brightness (overexposed/underexposed)
            mean_brightness = np.mean(gray)
            if mean_brightness < 20 or mean_brightness > 235:
                return {"is_suspicious": True, "reason": f"Extreme brightness: {mean_brightness:.1f}"}
            
            return {"is_suspicious": False, "reason": "Quality checks passed"}
            
        except Exception as e:
            return {"is_suspicious": True, "reason": f"Quality check error: {e}"}
    
    def calculate_fraud_score(self, image_path: str, user_id: str, ai_confidence: float = 0.0) -> Dict:
        """Calculate overall fraud score (0-1, higher = more suspicious)"""
        fraud_signals = []
        
        # Signal 1: Duplicate detection
        duplicate_check = self.check_duplicate_submission(image_path, user_id)
        if duplicate_check["is_duplicate"]:
            fraud_signals.append(0.8)  # High suspicion for duplicates
        else:
            fraud_signals.append(0.1)  # Low suspicion for unique images
        
        # Signal 2: Rate limiting
        rate_check = self.check_rate_limit(user_id)
        if rate_check["is_rate_limited"]:
            fraud_signals.append(0.6)  # Medium-high suspicion for rate limiting
        else:
            # Scale suspicion based on submission frequency
            frequency_score = rate_check["recent_count"] / rate_check["hourly_limit"]
            fraud_signals.append(frequency_score * 0.3)
        
        # Signal 3: Image quality
        quality_check = self.check_image_quality_fraud(image_path)
        if quality_check["is_suspicious"]:
            fraud_signals.append(0.4)  # Medium suspicion for quality issues
        else:
            fraud_signals.append(0.1)  # Low suspicion for good quality
        
        # Signal 4: AI confidence (if provided)
        if ai_confidence < self.min_confidence:
            fraud_signals.append(0.3)  # Medium suspicion for low confidence
        else:
            fraud_signals.append(0.05)  # Very low suspicion for high confidence
        
        # Calculate weighted average
        weights = [0.4, 0.3, 0.2, 0.1]  # Duplicate, rate, quality, confidence
        fraud_score = sum(signal * weight for signal, weight in zip(fraud_signals, weights))
        
        return {
            "fraud_score": min(1.0, fraud_score),
            "is_fraudulent": fraud_score > self.max_fraud_score,
            "signals": {
                "duplicate": duplicate_check,
                "rate_limit": rate_check,
                "quality": quality_check,
                "confidence_check": {
                    "confidence": ai_confidence,
                    "threshold": self.min_confidence,
                    "suspicious": ai_confidence < self.min_confidence
                }
            },
            "recommendation": self._get_recommendation(fraud_score)
        }
    
    def _get_recommendation(self, fraud_score: float) -> str:
        """Get recommendation based on fraud score"""
        if fraud_score > 0.7:
            return "REJECT - High fraud probability"
        elif fraud_score > 0.4:
            return "MANUAL_REVIEW - Medium fraud probability"
        elif fraud_score > 0.2:
            return "QUEUE - Low fraud probability"
        else:
            return "ACCEPT - Very low fraud probability"
    
    def record_submission(self, image_path: str, user_id: str):
        """Record submission for future fraud detection"""
        current_time = datetime.now()
        
        # Store hashes
        hashes = {
            'phash': self.calculate_perceptual_hash(image_path),
            'dhash': self.calculate_dhash(image_path),
            'ahash': self.calculate_average_hash(image_path)
        }
        
        if user_id not in self.submission_hashes:
            self.submission_hashes[user_id] = []
        
        # Add all hashes to user's hash list
        for hash_value in hashes.values():
            if hash_value:  # Only add non-empty hashes
                self.submission_hashes[user_id].append(hash_value)
                self.known_hashes.add(hash_value)
        
        # Store timestamp
        if user_id not in self.submission_times:
            self.submission_times[user_id] = []
        
        self.submission_times[user_id].append(current_time)
        
        # Keep only last 24 hours of timestamps
        cutoff_time = current_time - timedelta(hours=24)
        self.submission_times[user_id] = [
            time for time in self.submission_times[user_id] 
            if time > cutoff_time
        ]
    
    def analyze_dataset(self, dataset_dir: str) -> Dict:
        """Analyze dataset for fraud patterns"""
        dataset_path = Path(dataset_dir)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
        
        results = []
        fraud_scores = []
        duplicate_count = 0
        rate_limited_count = 0
        quality_suspicious_count = 0
        
        # Simulate different users for analysis
        user_ids = [f"user_{i}" for i in range(1, 21)]  # 20 simulated users
        
        for i, image_file in enumerate(dataset_path.rglob("*.jpg"))[:200]:  # Analyze first 200
            try:
                user_id = user_ids[i % len(user_ids)]
                
                # Record submission first
                self.record_submission(image_file, user_id)
                
                # Then check for fraud
                fraud_result = self.calculate_fraud_score(image_file, user_id)
                
                result = {
                    "image_path": str(image_file),
                    "user_id": user_id,
                    "fraud_score": fraud_result["fraud_score"],
                    "is_fraudulent": fraud_result["is_fraudulent"],
                    "recommendation": fraud_result["recommendation"]
                }
                
                results.append(result)
                fraud_scores.append(fraud_result["fraud_score"])
                
                # Count fraud signals
                if fraud_result["signals"]["duplicate"]["is_duplicate"]:
                    duplicate_count += 1
                if fraud_result["signals"]["rate_limit"]["is_rate_limited"]:
                    rate_limited_count += 1
                if fraud_result["signals"]["quality"]["is_suspicious"]:
                    quality_suspicious_count += 1
                    
            except Exception as e:
                print(f"Error processing {image_file}: {e}")
                continue
        
        # Calculate statistics
        total_images = len(results)
        fraudulent_count = sum(1 for r in results if r["is_fraudulent"])
        
        return {
            "total_images": total_images,
            "fraudulent_images": fraudulent_count,
            "fraud_rate": (fraudulent_count / total_images * 100) if total_images > 0 else 0,
            "average_fraud_score": np.mean(fraud_scores) if fraud_scores else 0,
            "fraud_signals": {
                "duplicates": duplicate_count,
                "rate_limited": rate_limited_count,
                "quality_suspicious": quality_suspicious_count
            },
            "recommendation_distribution": {
                rec: sum(1 for r in results if r["recommendation"] == rec)
                for rec in set(r["recommendation"] for r in results)
            },
            "detailed_results": results[:50]  # First 50 for detailed analysis
        }
    
    def save_metrics(self, analysis_results: Dict, output_path: str = "metrics/fraud_metrics.json"):
        """Save fraud analysis metrics"""
        os.makedirs("metrics", exist_ok=True)
        
        # Prepare metrics for DVC tracking
        metrics = {
            "total_images": analysis_results["total_images"],
            "fraudulent_images": analysis_results["fraudulent_images"],
            "fraud_rate": analysis_results["fraud_rate"],
            "average_fraud_score": analysis_results["average_fraud_score"],
            "fraud_signals": analysis_results["fraud_signals"],
            "recommendation_distribution": analysis_results["recommendation_distribution"]
        }
        
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"🔍 Fraud metrics saved to {output_path}")
        
        # Save detailed CSV for analysis
        if analysis_results["detailed_results"]:
            df = pd.DataFrame(analysis_results["detailed_results"])
            csv_path = output_path.replace(".json", ".csv")
            df.to_csv(csv_path, index=False)
            print(f"📋 Detailed results saved to {csv_path}")

def main():
    parser = argparse.ArgumentParser(description="SatsVerdant Fraud Detection")
    parser.add_argument("--analyze", action="store_true", help="Analyze dataset for fraud patterns")
    parser.add_argument("--check-submission", type=str, help="Check single submission for fraud")
    parser.add_argument("--user-id", type=str, help="User ID for submission check")
    parser.add_argument("--dataset", type=str, default="data/processed/test",
                       help="Dataset directory to analyze")
    parser.add_argument("--output", type=str, default="metrics/fraud_metrics.json",
                       help="Output metrics file")
    parser.add_argument("--confidence", type=float, default=0.8,
                       help="AI confidence for fraud calculation")
    
    args = parser.parse_args()
    
    # Load parameters
    params = load_params()
    
    # Initialize fraud detector
    detector = FraudDetector(params)
    
    if args.check_submission and args.user_id:
        # Check single submission
        if not Path(args.check_submission).exists():
            print(f"❌ Image not found: {args.check_submission}")
            return
        
        fraud_result = detector.calculate_fraud_score(
            args.check_submission, 
            args.user_id, 
            args.confidence
        )
        
        print(f"🔍 Fraud Analysis for {args.check_submission}:")
        print(f"  User ID: {args.user_id}")
        print(f"  Fraud Score: {fraud_result['fraud_score']:.3f}")
        print(f"  Is Fraudulent: {fraud_result['is_fraudulent']}")
        print(f"  Recommendation: {fraud_result['recommendation']}")
        
        print(f"\n📊 Fraud Signals:")
        signals = fraud_result["signals"]
        print(f"  Duplicate: {signals['duplicate']['is_duplicate']} - {signals['duplicate'].get('reason', 'None')}")
        print(f"  Rate Limited: {signals['rate_limit']['is_rate_limited']} - {signals['rate_limit'].get('reason', 'None')}")
        print(f"  Quality Issue: {signals['quality']['is_suspicious']} - {signals['quality'].get('reason', 'None')}")
        print(f"  Low Confidence: {signals['confidence_check']['suspicious']} (confidence: {args.confidence:.2f})")
        
    elif args.analyze:
        # Analyze dataset
        print(f"🔍 Analyzing dataset: {args.dataset}")
        
        try:
            results = detector.analyze_dataset(args.dataset)
            
            print(f"\n📊 Fraud Analysis Results:")
            print(f"  Total Images: {results['total_images']}")
            print(f"  Fraudulent Images: {results['fraudulent_images']}")
            print(f"  Fraud Rate: {results['fraud_rate']:.2f}%")
            print(f"  Average Fraud Score: {results['average_fraud_score']:.3f}")
            
            print(f"\n🚨 Fraud Signals Detected:")
            signals = results["fraud_signals"]
            print(f"  Duplicates: {signals['duplicates']} images")
            print(f"  Rate Limited: {signals['rate_limited']} submissions")
            print(f"  Quality Suspicious: {signals['quality_suspicious']} images")
            
            print(f"\n📋 Recommendation Distribution:")
            for rec, count in results["recommendation_distribution"].items():
                percentage = (count / results['total_images'] * 100) if results['total_images'] > 0 else 0
                print(f"  {rec}: {count} ({percentage:.1f}%)")
            
            # Save metrics
            detector.save_metrics(results, args.output)
            
        except Exception as e:
            print(f"❌ Error analyzing dataset: {e}")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
