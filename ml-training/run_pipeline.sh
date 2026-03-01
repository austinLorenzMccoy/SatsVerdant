#!/bin/bash
# SatsVerdant ML Training Pipeline - Complete Automation

set -e  # Exit on error

echo "🚀 SatsVerdant ML Training Pipeline"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}✅ Activating virtual environment${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "===================================="
echo "Step 1: Download Datasets"
echo "===================================="
python scripts/download_datasets.py

echo ""
echo "===================================="
echo "Step 2: Remap Datasets to 5 Categories"
echo "===================================="
python scripts/remap_datasets.py

echo ""
echo "===================================="
echo "Step 3: Generate Synthetic Data"
echo "===================================="
python scripts/generate_synthetic.py

echo ""
echo "===================================="
echo "Step 4: Train Model with MLflow"
echo "===================================="
python scripts/train_model.py

echo ""
echo -e "${GREEN}===================================="
echo "✅ PIPELINE COMPLETE!"
echo "====================================${NC}"
echo ""
echo "📊 View training results:"
echo "  mlflow ui"
echo "  Open: http://localhost:5000"
echo ""
echo "📦 Model saved to:"
echo "  - ml-training/models/waste_classifier_*.h5"
echo "  - backend/models/waste_classifier.h5"
echo ""
echo "🚀 Next steps:"
echo "  1. Test model: python scripts/test_model.py"
echo "  2. Deploy to backend"
echo "  3. Start collecting real user data"
echo ""
