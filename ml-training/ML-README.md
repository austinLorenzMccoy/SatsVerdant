# SatsVerdant ML Training Pipeline

Complete machine learning training pipeline for waste classification models.

## Quick Start

### 1. Install Dependencies

```bash
cd ml-training
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Kaggle API (Optional)

To download Kaggle datasets:

```bash
# Get API credentials from https://www.kaggle.com/settings
mkdir -p ~/.kaggle
# Save kaggle.json to ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### 3. Download Datasets

```bash
python scripts/download_datasets.py
```

This downloads:
- ✅ **TrashNet** (2,527 images) - Free, MIT license
- ✅ **TACO** (15,000+ images) - Free, CC BY 4.0
- ✅ **Kaggle Waste** (25,000+ images) - Free, CC0 (requires API key)

**Expected:** ~26,000+ images total

### 4. Remap to 5 Categories

```bash
python scripts/remap_datasets.py
```

Maps all datasets to SatsVerdant's 5 categories:
- `plastic`
- `paper`
- `metal`
- `organic`
- `electronic`

### 5. Generate Synthetic Data

```bash
python scripts/generate_synthetic.py
```

Generates synthetic variants for underrepresented categories (especially electronic waste).

### 6. Train Model

```bash
python scripts/train_model.py
```

Trains MobileNetV3-Large classifier with:
- Transfer learning from ImageNet
- Data augmentation
- MLflow experiment tracking
- Early stopping & learning rate scheduling

**Expected accuracy:** 75-80% on validation set

## Dataset Statistics

After running all scripts, you should have:

```
plastic:     ~8,000 images
paper:       ~6,000 images
metal:       ~4,000 images
organic:     ~3,000 images
electronic:  ~5,000 images (mostly synthetic)

TOTAL:       ~26,000 images
```

## Directory Structure

```
ml-training/
├── data/
│   ├── raw/              # Downloaded datasets
│   │   ├── trashnet/
│   │   ├── taco/
│   │   ├── kaggle_waste/
│   │   └── backgrounds/
│   ├── unified/          # Remapped to 5 categories
│   ├── synthetic/        # Generated synthetic data
│   └── combined/         # Final training dataset
├── models/               # Trained models
├── mlruns/              # MLflow tracking data
├── notebooks/           # Jupyter notebooks
├── scripts/             # Training scripts
│   ├── download_datasets.py
│   ├── remap_datasets.py
│   ├── generate_synthetic.py
│   └── train_model.py
└── requirements.txt
```

## Model Architecture

**Base:** MobileNetV3-Large (pre-trained on ImageNet)

**Modifications:**
- Global Average Pooling
- Dropout (0.3)
- Dense layer (256 units, ReLU)
- Dropout (0.3)
- Output layer (5 classes, Softmax)

**Total parameters:** ~4.2M (2.5M trainable)

## MLflow Tracking

View training experiments:

```bash
mlflow ui
# Open http://localhost:5000
```

Tracked metrics:
- Training/validation accuracy
- Training/validation loss
- Top-2 accuracy
- Per-epoch metrics
- Model artifacts

## Deployment

After training, the model is automatically saved to:

```
../backend/models/waste_classifier.h5
```

The backend will load this model for inference.

## Configuration

Edit `.env` file (copy from `.env.example`):

```env
MODEL_ARCHITECTURE=MobileNetV3-Large
INPUT_SIZE=224
BATCH_SIZE=32
EPOCHS=20
LEARNING_RATE=0.001
```

## Troubleshooting

### TACO Download Fails
TACO is large (~5GB). If download fails:
- Download manually from http://tacodataset.org/
- Or skip TACO and use TrashNet + Kaggle only

### Kaggle API Not Configured
- Get API key from https://www.kaggle.com/settings
- Save to `~/.kaggle/kaggle.json`
- Or download dataset manually

### Out of Memory During Training
- Reduce `BATCH_SIZE` in `.env`
- Use smaller input size (e.g., 192 instead of 224)
- Train on GPU if available

### Low Accuracy (<70%)
- Increase `EPOCHS`
- Add more data augmentation
- Fine-tune more layers of base model
- Collect more real-world data

## Next Steps

1. **Evaluate model** on test set
2. **Deploy to backend** (already done automatically)
3. **Test with real images** via API
4. **Collect user data** for retraining
5. **Retrain monthly** with new data

## Continuous Improvement

### Active Learning Pipeline

```python
# Identify uncertain predictions
uncertain = model.predict(new_images)
low_confidence = uncertain[np.max(uncertain, axis=1) < 0.75]

# Send to validators for labeling
# Add to training set
# Retrain model
```

### Monthly Retraining

```bash
# Collect validated user submissions
python scripts/collect_user_data.py

# Retrain with combined dataset
python scripts/train_model.py --include-user-data

# Deploy if accuracy improves
```

## Resources

- **TrashNet:** https://github.com/garythung/trashnet
- **TACO:** http://tacodataset.org/
- **Kaggle:** https://www.kaggle.com/datasets/techsash/waste-classification-data
- **MLflow:** https://mlflow.org/docs/latest/index.html
- **TensorFlow:** https://www.tensorflow.org/tutorials

## License

Training scripts: MIT
Datasets: See individual dataset licenses
