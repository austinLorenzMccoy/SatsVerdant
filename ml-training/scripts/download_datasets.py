#!/usr/bin/env python3
"""
Download all public waste classification datasets.
"""
import os
import subprocess
import sys
from pathlib import Path
import zipfile
import shutil
from tqdm import tqdm
import requests

# Dataset directories
RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_trashnet():
    """Download TrashNet dataset from GitHub."""
    print("\n" + "="*60)
    print("📦 Downloading TrashNet Dataset (2,527 images)")
    print("="*60)
    
    trashnet_dir = RAW_DATA_DIR / "trashnet"
    
    if trashnet_dir.exists():
        print(f"✅ TrashNet already exists at {trashnet_dir}")
        return
    
    try:
        print("Cloning from GitHub...")
        subprocess.run([
            "git", "clone",
            "https://github.com/garythung/trashnet.git",
            str(trashnet_dir)
        ], check=True)
        
        # Count images
        image_count = sum(1 for _ in trashnet_dir.glob("**/*.jpg"))
        print(f"✅ Downloaded {image_count} images")
        
        # Show structure
        print("\nDataset structure:")
        for category in ["glass", "paper", "cardboard", "plastic", "metal", "trash"]:
            cat_dir = trashnet_dir / "data" / category
            if cat_dir.exists():
                count = len(list(cat_dir.glob("*.jpg")))
                print(f"  - {category}: {count} images")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download TrashNet: {e}")
        sys.exit(1)


def download_taco():
    """Download TACO dataset."""
    print("\n" + "="*60)
    print("📦 Downloading TACO Dataset (15,000+ images)")
    print("="*60)
    
    taco_dir = RAW_DATA_DIR / "taco"
    
    if taco_dir.exists() and (taco_dir / "data").exists():
        print(f"✅ TACO already exists at {taco_dir}")
        return
    
    taco_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print("Cloning TACO repository...")
        subprocess.run([
            "git", "clone",
            "https://github.com/pedropro/TACO.git",
            str(taco_dir)
        ], check=True)
        
        print("\nDownloading TACO images (this may take 10-15 minutes)...")
        print("Note: TACO is large (~5GB). You can download a subset if needed.")
        
        # Change to TACO directory and run download script
        original_dir = os.getcwd()
        os.chdir(taco_dir)
        
        # Install TACO package
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        
        # Download dataset (you can modify this to download subset)
        subprocess.run([sys.executable, "download.py"], check=True)
        
        os.chdir(original_dir)
        
        print("✅ TACO dataset downloaded")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download TACO: {e}")
        print("\nNote: TACO download can be slow. You can:")
        print("  1. Download manually from http://tacodataset.org/")
        print("  2. Download a subset by modifying download.py")
        print("  3. Skip TACO for now and use TrashNet + Kaggle only")


def download_kaggle_waste():
    """Download Kaggle Waste Classification dataset."""
    print("\n" + "="*60)
    print("📦 Downloading Kaggle Waste Classification (25,000+ images)")
    print("="*60)
    
    kaggle_dir = RAW_DATA_DIR / "kaggle_waste"
    
    if kaggle_dir.exists() and len(list(kaggle_dir.glob("**/*.jpg"))) > 1000:
        print(f"✅ Kaggle dataset already exists at {kaggle_dir}")
        return
    
    # Check if Kaggle API is configured
    kaggle_config = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_config.exists():
        print("\n⚠️  Kaggle API not configured!")
        print("\nTo download Kaggle datasets:")
        print("1. Go to https://www.kaggle.com/settings")
        print("2. Scroll to 'API' section")
        print("3. Click 'Create New API Token'")
        print("4. Save kaggle.json to ~/.kaggle/")
        print("5. Run: chmod 600 ~/.kaggle/kaggle.json")
        print("\nSkipping Kaggle download for now...")
        return
    
    try:
        kaggle_dir.mkdir(parents=True, exist_ok=True)
        
        print("Downloading from Kaggle...")
        subprocess.run([
            "kaggle", "datasets", "download",
            "-d", "techsash/waste-classification-data",
            "-p", str(kaggle_dir)
        ], check=True)
        
        # Unzip
        print("Extracting files...")
        zip_file = kaggle_dir / "waste-classification-data.zip"
        if zip_file.exists():
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(kaggle_dir)
            zip_file.unlink()  # Remove zip file
        
        # Count images
        image_count = sum(1 for _ in kaggle_dir.glob("**/*.jpg"))
        print(f"✅ Downloaded {image_count} images")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download Kaggle dataset: {e}")
        print("You can download manually from:")
        print("https://www.kaggle.com/datasets/techsash/waste-classification-data")


def download_sample_backgrounds():
    """Download sample background images for synthetic data generation."""
    print("\n" + "="*60)
    print("📦 Downloading Background Images for Synthetic Data")
    print("="*60)
    
    bg_dir = RAW_DATA_DIR / "backgrounds"
    bg_dir.mkdir(parents=True, exist_ok=True)
    
    if len(list(bg_dir.glob("*.jpg"))) > 10:
        print(f"✅ Backgrounds already exist at {bg_dir}")
        return
    
    # Download some free background images from Unsplash
    backgrounds = [
        "https://images.unsplash.com/photo-1557683316-973673baf926",  # Gradient
        "https://images.unsplash.com/photo-1579546929518-9e396f3cc809",  # Abstract
        "https://images.unsplash.com/photo-1557682250-33bd709cbe85",  # Gradient
    ]
    
    print("Downloading sample backgrounds...")
    for idx, url in enumerate(backgrounds):
        try:
            response = requests.get(f"{url}?w=800&h=600", stream=True)
            if response.status_code == 200:
                with open(bg_dir / f"bg_{idx}.jpg", 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Warning: Failed to download background {idx}: {e}")
    
    print(f"✅ Downloaded {len(list(bg_dir.glob('*.jpg')))} background images")


def print_summary():
    """Print download summary."""
    print("\n" + "="*60)
    print("📊 DOWNLOAD SUMMARY")
    print("="*60)
    
    datasets = {
        "TrashNet": RAW_DATA_DIR / "trashnet",
        "TACO": RAW_DATA_DIR / "taco",
        "Kaggle Waste": RAW_DATA_DIR / "kaggle_waste",
        "Backgrounds": RAW_DATA_DIR / "backgrounds"
    }
    
    total_images = 0
    for name, path in datasets.items():
        if path.exists():
            count = sum(1 for _ in path.glob("**/*.jpg"))
            total_images += count
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {name}: {count:,} images")
        else:
            print(f"❌ {name}: Not downloaded")
    
    print(f"\n📈 Total images: {total_images:,}")
    print("\n✅ Dataset download complete!")
    print("\nNext steps:")
    print("  1. Run: python scripts/remap_datasets.py")
    print("  2. Run: python scripts/generate_synthetic.py")
    print("  3. Run: python scripts/train_model.py")


if __name__ == "__main__":
    print("🚀 SatsVerdant Dataset Downloader")
    print("="*60)
    
    # Download all datasets
    download_trashnet()
    download_taco()
    download_kaggle_waste()
    download_sample_backgrounds()
    
    # Print summary
    print_summary()
