#!/usr/bin/env python3
"""
Google Colab Setup Script for SatsVerdant ML Training
Automates environment setup in Google Colab

Usage:
    # In Colab notebook:
    !python scripts/setup_colab.py
"""

import os
import sys
import subprocess
from pathlib import Path

def install_packages():
    """Install required packages"""
    print("📦 Installing packages...")
    
    packages = [
        "tensorflow==2.15.0",
        "tensorflow-addons==0.23.0", 
        "albumentations==1.4.0",
        "scikit-learn==1.3.2",
        "mlflow==2.8.1",
        "dagshub==0.3.5",
        "dvc==3.48.4",
        "opencv-python==4.8.1.78",
        "imagehash==4.3.1",
        "Pillow==10.1.0",
        "numpy==1.24.4",
        "pandas==2.1.4",
        "matplotlib==3.8.2",
        "seaborn==0.13.0",
        "tqdm==4.66.1",
        "pyyaml==6.0.1",
        "requests==2.31.0"
    ]
    
    for package in packages:
        print(f"  Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
    
    print("✅ All packages installed!")

def setup_dagshub():
    """Setup DagsHub integration"""
    print("🔗 Setting up DagsHub...")
    
    # Check if DagsHub credentials are set
    if not os.getenv("DAGSHUB_USERNAME") or not os.getenv("DAGSHUB_TOKEN"):
        print("⚠️  Please set DagsHub credentials:")
        print("  import os")
        print("  os.environ['DAGSHUB_USERNAME'] = 'your_username'")
        print("  os.environ['DAGSHUB_TOKEN'] = 'your_token'")
        return False
    
    # Initialize DagsHub
    try:
        import dagshub
        dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)
        print("✅ DagsHub initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ DagsHub setup failed: {e}")
        return False

def setup_dvc():
    """Setup DVC for data versioning"""
    print("📁 Setting up DVC...")
    
    # Initialize DVC if not already done
    if not Path(".dvc").exists():
        subprocess.run(["dvc", "init"], check=True)
        print("✅ DVC initialized")
    
    # Set up DagsHub remote
    try:
        subprocess.run(["dvc", "remote", "add", "origin", 
                      "https://dagshub.com/satsverdant/satsverdant-ml.dvc"], check=True)
        
        # Configure authentication
        subprocess.run(["dvc", "remote", "modify", "origin", "--local", "auth", "basic"], check=True)
        subprocess.run(["dvc", "remote", "modify", "origin", "--local", "user", 
                      os.getenv("DAGSHUB_USERNAME", "")], check=False)
        subprocess.run(["dvc", "remote", "modify", "origin", "--local", "password", 
                      os.getenv("DAGSHUB_TOKEN", "")], check=False)
        
        print("✅ DVC remote configured")
        return True
    except Exception as e:
        print(f"❌ DVC setup failed: {e}")
        return False

def setup_colab_environment():
    """Setup Google Colab specific configurations"""
    print("🔧 Setting up Colab environment...")
    
    # Mount Google Drive
    try:
        from google.colab import drive
        drive.mount('/content/drive')
        print("✅ Google Drive mounted")
        
        # Create working directory in Drive
        work_dir = "/content/drive/MyDrive/satsverdant"
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        
        # Change to working directory
        os.chdir(work_dir)
        print(f"✅ Working directory: {work_dir}")
        
        return True
    except ImportError:
        print("⚠️  Not in Colab environment")
        return False
    except Exception as e:
        print(f"❌ Colab setup failed: {e}")
        return False

def verify_setup():
    """Verify that everything is set up correctly"""
    print("🔍 Verifying setup...")
    
    checks = []
    
    # Check Python packages
    try:
        import tensorflow as tf
        import mlflow
        import dagshub
        import dvc
        import cv2
        checks.append("✅ Python packages installed")
    except ImportError as e:
        checks.append(f"❌ Missing package: {e}")
    
    # Check DagsHub connection
    try:
        import dagshub
        dagshub.get_repo("satsverdant", "satsverdant-ml")
        checks.append("✅ DagsHub connection working")
    except:
        checks.append("❌ DagsHub connection failed")
    
    # Check DVC
    try:
        result = subprocess.run(["dvc", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            checks.append("✅ DVC working")
        else:
            checks.append("❌ DVC not working")
    except:
        checks.append("❌ DVC not installed")
    
    # Check directories
    required_dirs = ["src", "data", "models", "metrics"]
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            checks.append(f"✅ {dir_name}/ directory exists")
        else:
            checks.append(f"❌ {dir_name}/ directory missing")
    
    print("\n📋 Setup Verification:")
    for check in checks:
        print(f"  {check}")
    
    return all("✅" in check for check in checks)

def main():
    print("🚀 SatsVerdant ML Training - Colab Setup")
    print("=" * 50)
    
    # Setup Colab environment
    setup_colab_environment()
    
    # Install packages
    install_packages()
    
    # Setup DagsHub
    dagshub_ok = setup_dagshub()
    
    # Setup DVC
    dvc_ok = setup_dvc()
    
    # Verify setup
    setup_ok = verify_setup()
    
    print("\n" + "=" * 50)
    if setup_ok:
        print("🎉 Setup complete! Ready to start training.")
        print("\n📝 Next steps:")
        print("1. Set your DagsHub credentials:")
        print("   os.environ['DAGSHUB_USERNAME'] = 'your_username'")
        print("   os.environ['DAGSHUB_TOKEN'] = 'your_token'")
        print("2. Prepare data:")
        print("   !python src/prepare_data.py")
        print("3. Start training:")
        print("   !python src/train.py")
    else:
        print("❌ Setup incomplete. Please check the errors above.")
    
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()
