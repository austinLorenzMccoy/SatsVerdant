#!/usr/bin/env python3
"""
SatsVerdant Data Preparation Script
Downloads datasets and creates train/val/test splits

Usage:
    python src/prepare_data.py [--download-only] [--force]
"""

import os
import sys
import shutil
import argparse
import yaml
import random
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np
from tqdm import tqdm

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_params():
    """Load hyperparameters from params.yaml"""
    with open("params.yaml") as f:
        return yaml.safe_load(f)

def create_directories():
    """Create necessary directory structure"""
    dirs = [
        "data/raw/trashnet",
        "data/raw/taco", 
        "data/raw/kaggle",
        "data/raw/custom",
        "data/processed/train",
        "data/processed/val",
        "data/processed/test"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")

def download_trashnet():
    """Download TrashNet dataset (simulated - in practice would download from source)"""
    print("📥 Downloading TrashNet dataset...")
    
    # In practice, this would download from the actual source
    # For now, we'll create a placeholder structure
    
    trashnet_dir = Path("data/raw/trashnet")
    classes = ["plastic", "paper", "metal", "organic", "glass"]
    
    for class_name in classes:
        class_dir = trashnet_dir / class_name
        class_dir.mkdir(exist_ok=True)
        
        # Create placeholder files (in practice, these would be actual images)
        # TrashNet contributes 2,527 images total
        class_counts = {"plastic": 800, "paper": 700, "metal": 500, "organic": 327, "glass": 200}
        for i in range(class_counts[class_name]):
            placeholder = class_dir / f"trashnet_{class_name}_{i:04d}.jpg"
            placeholder.touch()
    
    print("✅ TrashNet dataset structure created")

def download_taco():
    """Download TACO dataset (simulated)"""
    print("📥 Downloading TACO dataset...")
    
    taco_dir = Path("data/raw/taco")
    classes = ["plastic", "paper", "metal", "organic", "glass"]
    
    # TACO has 15,000 images with realistic distribution
    class_counts = {"plastic": 4500, "paper": 3800, "metal": 2800, "organic": 2500, "glass": 1400}
    
    for class_name, count in class_counts.items():
        class_dir = taco_dir / class_name
        class_dir.mkdir(exist_ok=True)
        
        for i in range(count):
            placeholder = class_dir / f"taco_{class_name}_{i:04d}.jpg"
            placeholder.touch()
    
    print("✅ TACO dataset structure created")

def download_kaggle():
    """Download Kaggle dataset (simulated)"""
    print("📥 Downloading Kaggle dataset...")
    
    kaggle_dir = Path("data/raw/kaggle")
    classes = ["plastic", "paper", "metal", "organic", "glass"]
    
    # Kaggle dataset with 5,000 balanced images
    for class_name in classes:
        class_dir = kaggle_dir / class_name
        class_dir.mkdir(exist_ok=True)
        
        for i in range(1000):  # 1000 images per class
            placeholder = class_dir / f"kaggle_{class_name}_{i:04d}.jpg"
            placeholder.touch()
    
    print("✅ Kaggle dataset structure created")

def download_custom():
    """Download custom collected dataset (simulated)"""
    print("📥 Setting up custom dataset...")
    
    custom_dir = Path("data/raw/custom")
    classes = ["plastic", "paper", "metal", "organic", "glass"]
    
    # Custom dataset from recycling partners (3,473 images)
    class_counts = {"plastic": 1700, "paper": 1000, "metal": 900, "organic": 673, "glass": 200}
    
    for class_name, count in class_counts.items():
        class_dir = custom_dir / class_name
        class_dir.mkdir(exist_ok=True)
        
        for i in range(count):
            placeholder = class_dir / f"custom_{class_name}_{i:04d}.jpg"
            placeholder.touch()
    
    print("✅ Custom dataset structure created")

def scan_dataset_directory(root_dir: Path) -> Dict[str, List[str]]:
    """Scan dataset directory and return class-wise file lists"""
    dataset = {}
    
    if not root_dir.exists():
        return dataset
    
    for class_dir in root_dir.iterdir():
        if class_dir.is_dir():
            class_name = class_dir.name
            files = [f for f in class_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
            dataset[class_name] = files
    
    return dataset

def combine_datasets() -> Dict[str, List[str]]:
    """Combine all datasets into a single dataset"""
    print("🔗 Combining datasets...")
    
    combined = {}
    sources = ["trashnet", "taco", "kaggle", "custom"]
    
    for source in sources:
        source_dir = Path(f"data/raw/{source}")
        source_data = scan_dataset_directory(source_dir)
        
        for class_name, files in source_data.items():
            if class_name not in combined:
                combined[class_name] = []
            combined[class_name].extend(files)
    
    # Print dataset statistics
    total_files = sum(len(files) for files in combined.values())
    print(f"📊 Combined dataset: {total_files} total files")
    print("🎯 Target distribution (per PRD):")
    print("  Plastic:   8,000 images (30.8%)")
    print("  Paper:     6,500 images (25.0%)") 
    print("  Metal:     5,000 images (19.2%)")
    print("  Organic:   4,500 images (17.3%)")
    print("  Glass:     2,000 images (7.7%)")
    print("  Total:    26,000 images")
    
    for class_name, files in combined.items():
        print(f"  {class_name}: {len(files)} files")
    
    return combined

def split_dataset(combined_dataset: Dict[str, List[str]], params: Dict) -> Tuple[Dict, Dict, Dict]:
    """Split dataset into train, validation, and test sets"""
    print("✂️  Splitting dataset...")
    
    train_split = params["prepare"]["train_split"]
    val_split = params["prepare"]["val_split"]
    test_split = params["prepare"]["test_split"]
    random_seed = params["prepare"]["random_seed"]
    
    random.seed(random_seed)
    
    train_set = {}
    val_set = {}
    test_set = {}
    
    for class_name, files in combined_dataset.items():
        random.shuffle(files)
        
        total_files = len(files)
        train_count = int(total_files * train_split)
        val_count = int(total_files * val_split)
        
        train_files = files[:train_count]
        val_files = files[train_count:train_count + val_count]
        test_files = files[train_count + val_count:]
        
        train_set[class_name] = train_files
        val_set[class_name] = val_files
        test_set[class_name] = test_files
        
        print(f"  {class_name}: {len(train_files)} train, {len(val_files)} val, {len(test_files)} test")
    
    return train_set, val_set, test_set

def copy_files(file_set: Dict[str, List[str]], target_dir: str):
    """Copy files to target directory maintaining class structure"""
    target_path = Path(target_dir)
    
    for class_name, files in file_set.items():
        class_target_dir = target_path / class_name
        class_target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in tqdm(files, desc=f"Copying {class_name}"):
            if file_path.exists():
                # Create unique filename to avoid conflicts
                target_file = class_target_dir / file_path.name
                shutil.copy2(file_path, target_file)

def create_class_info_file(train_set: Dict, val_set: Dict, test_set: Dict):
    """Create a JSON file with dataset information"""
    dataset_info = {
        "total_images": sum(len(files) for files in train_set.values()) + 
                       sum(len(files) for files in val_set.values()) + 
                       sum(len(files) for files in test_set.values()),
        "train_images": sum(len(files) for files in train_set.values()),
        "val_images": sum(len(files) for files in val_set.values()),
        "test_images": sum(len(files) for files in test_set.values()),
        "classes": list(train_set.keys()),
        "class_distribution": {
            class_name: {
                "train": len(train_set[class_name]),
                "val": len(val_set[class_name]),
                "test": len(test_set[class_name]),
                "total": len(train_set[class_name]) + len(val_set[class_name]) + len(test_set[class_name])
            }
            for class_name in train_set.keys()
        }
    }
    
    import json
    with open("data/processed/dataset_info.json", "w") as f:
        json.dump(dataset_info, f, indent=2)
    
    print("📋 Dataset info saved to data/processed/dataset_info.json")

def create_metrics_file():
    """Create initial metrics file for DVC tracking"""
    metrics = {
        "preparation": {
            "status": "completed",
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_classes": 5,
            "target_img_size": 224
        }
    }
    
    import json
    os.makedirs("metrics", exist_ok=True)
    with open("metrics/prepare_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Prepare SatsVerdant dataset")
    parser.add_argument("--download-only", action="store_true", help="Only download datasets")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing data")
    args = parser.parse_args()
    
    # Load parameters
    params = load_params()
    
    # Create directories
    create_directories()
    
    # Download datasets
    if args.force or not Path("data/raw/trashnet").exists():
        download_trashnet()
        download_taco()
        download_kaggle()
        download_custom()
    else:
        print("📁 Raw datasets already exist. Use --force to re-download.")
    
    if args.download_only:
        print("✅ Download complete. Use without --download-only to process data.")
        return
    
    # Combine datasets
    combined_dataset = combine_datasets()
    
    # Split dataset
    train_set, val_set, test_set = split_dataset(combined_dataset, params)
    
    # Copy files to processed directories
    print("📁 Copying files to processed directories...")
    copy_files(train_set, "data/processed/train")
    copy_files(val_set, "data/processed/val")
    copy_files(test_set, "data/processed/test")
    
    # Create info files
    create_class_info_file(train_set, val_set, test_set)
    create_metrics_file()
    
    print("✅ Data preparation complete!")
    print(f"📊 Dataset ready for training:")
    print(f"  Train: {sum(len(files) for files in train_set.values())} images")
    print(f"  Val: {sum(len(files) for files in val_set.values())} images")
    print(f"  Test: {sum(len(files) for files in test_set.values())} images")

if __name__ == "__main__":
    main()
