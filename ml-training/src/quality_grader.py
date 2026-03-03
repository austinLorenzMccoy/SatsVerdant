#!/usr/bin/env python3
"""
SatsVerdant Image Quality Grader
Analyzes image quality and assigns grades with reward multipliers

Usage:
    python src/quality_grader.py --analyze
    python src/quality_grader.py --grade-image /path/to/image.jpg
"""

import os
import sys
import argparse
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

import cv2
from PIL import Image, ImageStat
import pandas as pd

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_params():
    """Load hyperparameters from params.yaml"""
    with open("params.yaml") as f:
        return yaml.safe_load(f)

class ImageQualityGrader:
    """Grades image quality based on blur, brightness, and contrast metrics"""
    
    def __init__(self, params: Dict):
        self.quality_params = params["quality"]
        self.grades = list(self.quality_params.keys())
        
    def calculate_blur_score(self, image_path: str) -> float:
        """Calculate blur score using Laplacian variance"""
        try:
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                return 0.0
            
            # Laplacian variance - higher = less blurry
            laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
            return laplacian_var
        except Exception:
            return 0.0
    
    def calculate_brightness_score(self, image_path: str) -> float:
        """Calculate average brightness"""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                stat = ImageStat.Stat(img)
                # Mean brightness across RGB channels
                brightness = sum(stat.mean) / len(stat.mean)
                return brightness
        except Exception:
            return 0.0
    
    def calculate_contrast_score(self, image_path: str) -> float:
        """Calculate contrast using standard deviation"""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                stat = ImageStat.Stat(img)
                # Standard deviation across RGB channels
                contrast = sum(stat.stddev) / len(stat.stddev)
                return contrast
        except Exception:
            return 0.0
    
    def grade_image(self, image_path: str) -> Dict:
        """Grade a single image and return quality metrics"""
        blur = self.calculate_blur_score(image_path)
        brightness = self.calculate_brightness_score(image_path)
        contrast = self.calculate_contrast_score(image_path)
        
        # Determine grade based on thresholds
        grade = self._determine_grade(blur, brightness, contrast)
        multiplier = self.quality_params[grade]["reward_multiplier"]
        
        return {
            "image_path": str(image_path),
            "blur_score": blur,
            "brightness_score": brightness,
            "contrast_score": contrast,
            "grade": grade,
            "reward_multiplier": multiplier,
            "thresholds_met": self._check_thresholds(grade, blur, brightness, contrast)
        }
    
    def _determine_grade(self, blur: float, brightness: float, contrast: float) -> str:
        """Determine grade based on quality metrics"""
        # Check from highest grade to lowest
        for grade in ['grade_a', 'grade_b', 'grade_c', 'grade_d']:
            if self._meets_grade_requirements(grade, blur, brightness, contrast):
                return grade
        return 'grade_d'
    
    def _meets_grade_requirements(self, grade: str, blur: float, brightness: float, contrast: float) -> bool:
        """Check if image meets grade requirements"""
        thresholds = self.quality_params[grade]
        return (
            blur >= thresholds["blur_min"] and
            thresholds["brightness_min"] <= brightness <= thresholds["brightness_max"] and
            contrast >= thresholds["contrast_min"]
        )
    
    def _check_thresholds(self, grade: str, blur: float, brightness: float, contrast: float) -> Dict:
        """Check which thresholds are met for debugging"""
        thresholds = self.quality_params[grade]
        return {
            "blur_met": blur >= thresholds["blur_min"],
            "brightness_met": thresholds["brightness_min"] <= brightness <= thresholds["brightness_max"],
            "contrast_met": contrast >= thresholds["contrast_min"]
        }
    
    def analyze_dataset(self, dataset_dir: str) -> Dict:
        """Analyze entire dataset and return quality statistics"""
        dataset_path = Path(dataset_dir)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
        
        results = []
        grade_counts = {grade: 0 for grade in self.grades}
        
        # Process all images in dataset
        for image_file in dataset_path.rglob("*.jpg"):
            try:
                result = self.grade_image(image_file)
                results.append(result)
                grade_counts[result["grade"]] += 1
            except Exception as e:
                print(f"Error processing {image_file}: {e}")
                continue
        
        # Calculate statistics
        total_images = len(results)
        grade_percentages = {
            grade: (count / total_images * 100) if total_images > 0 else 0
            for grade, count in grade_counts.items()
        }
        
        # Calculate average metrics
        avg_metrics = {
            "avg_blur": np.mean([r["blur_score"] for r in results]) if results else 0,
            "avg_brightness": np.mean([r["brightness_score"] for r in results]) if results else 0,
            "avg_contrast": np.mean([r["contrast_score"] for r in results]) if results else 0
        }
        
        return {
            "total_images": total_images,
            "grade_distribution": grade_counts,
            "grade_percentages": grade_percentages,
            "average_metrics": avg_metrics,
            "quality_score": self._calculate_quality_score(grade_percentages),
            "detailed_results": results[:100]  # First 100 for detailed analysis
        }
    
    def _calculate_quality_score(self, grade_percentages: Dict) -> float:
        """Calculate overall quality score (0-100)"""
        weights = {
            "grade_a": 100,
            "grade_b": 75,
            "grade_c": 50,
            "grade_d": 25
        }
        
        weighted_score = sum(
            grade_percentages[grade] * (weight / 100)
            for grade, weight in weights.items()
        )
        
        return min(100, weighted_score)
    
    def save_metrics(self, analysis_results: Dict, output_path: str = "metrics/quality_metrics.json"):
        """Save quality analysis metrics"""
        os.makedirs("metrics", exist_ok=True)
        
        # Prepare metrics for DVC tracking
        metrics = {
            "quality_score": analysis_results["quality_score"],
            "total_images": analysis_results["total_images"],
            "grade_percentages": analysis_results["grade_percentages"],
            "average_metrics": analysis_results["average_metrics"]
        }
        
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"📊 Quality metrics saved to {output_path}")
        
        # Save detailed CSV for analysis
        if analysis_results["detailed_results"]:
            df = pd.DataFrame(analysis_results["detailed_results"])
            csv_path = output_path.replace(".json", ".csv")
            df.to_csv(csv_path, index=False)
            print(f"📋 Detailed results saved to {csv_path}")

def main():
    parser = argparse.ArgumentParser(description="SatsVerdant Image Quality Grader")
    parser.add_argument("--analyze", action="store_true", help="Analyze entire dataset")
    parser.add_argument("--grade-image", type=str, help="Grade a single image")
    parser.add_argument("--dataset", type=str, default="data/processed/test", 
                       help="Dataset directory to analyze")
    parser.add_argument("--output", type=str, default="metrics/quality_metrics.json",
                       help="Output metrics file")
    
    args = parser.parse_args()
    
    # Load parameters
    params = load_params()
    
    # Initialize grader
    grader = ImageQualityGrader(params)
    
    if args.grade_image:
        # Grade single image
        if not Path(args.grade_image).exists():
            print(f"❌ Image not found: {args.grade_image}")
            return
        
        result = grader.grade_image(args.grade_image)
        print(f"📸 Image Quality Analysis:")
        print(f"  Image: {result['image_path']}")
        print(f"  Grade: {result['grade']}")
        print(f"  Reward Multiplier: {result['reward_multiplier']}x")
        print(f"  Blur Score: {result['blur_score']:.1f}")
        print(f"  Brightness: {result['brightness_score']:.1f}")
        print(f"  Contrast: {result['contrast_score']:.1f}")
        print(f"  Thresholds Met: {result['thresholds_met']}")
        
    elif args.analyze:
        # Analyze dataset
        print(f"🔍 Analyzing dataset: {args.dataset}")
        
        try:
            results = grader.analyze_dataset(args.dataset)
            
            print(f"\n📊 Dataset Quality Analysis:")
            print(f"  Total Images: {results['total_images']}")
            print(f"  Quality Score: {results['quality_score']:.1f}/100")
            print(f"\n📈 Grade Distribution:")
            
            for grade in ['grade_a', 'grade_b', 'grade_c', 'grade_d']:
                count = results['grade_distribution'][grade]
                percentage = results['grade_percentages'][grade]
                multiplier = params["quality"][grade]["reward_multiplier"]
                print(f"  {grade.upper()}: {count} images ({percentage:.1f}%) - {multiplier}x reward")
            
            print(f"\n📏 Average Metrics:")
            print(f"  Blur: {results['average_metrics']['avg_blur']:.1f}")
            print(f"  Brightness: {results['average_metrics']['avg_brightness']:.1f}")
            print(f"  Contrast: {results['average_metrics']['avg_contrast']:.1f}")
            
            # Save metrics
            grader.save_metrics(results, args.output)
            
        except Exception as e:
            print(f"❌ Error analyzing dataset: {e}")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
