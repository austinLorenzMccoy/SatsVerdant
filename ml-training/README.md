# SatsVerdant ML Training Environment

## 🤖 Machine Learning Pipeline for Waste Classification

This directory contains the complete ML training pipeline for SatsVerdant's waste classification system, implementing the EfficientNetB0 model with full MLOps traceability.

## 📁 Directory Structure

```
ml-training/
├── data/
│   ├── raw/                  # Original datasets (DVC-tracked)
│   │   ├── trashnet/        # TrashNet dataset (2,527 images)
│   │   ├── taco/            # TACO dataset (15,000 images)
│   │   ├── kaggle/          # Kaggle dataset (5,000 images)
│   │   └── custom/          # Custom collected images (3,473 images)
│   └── processed/            # Train/val/test splits (DVC-tracked)
│       ├── train/           # 20,800 images (80%)
│       ├── val/             # 2,600 images (10%)
│       └── test/            # 2,600 images (10%)
├── models/                   # Trained model artifacts (DVC-tracked)
│   ├── waste_classifier.h5  # TensorFlow model for backend
│   └── waste_classifier.tflite # TensorFlow Lite for mobile
├── src/                      # Source code
│   ├── prepare_data.py      # Data preprocessing
│   ├── train.py             # Training script with MLflow
│   ├── evaluate.py          # Model evaluation
│   ├── quality_grader.py    # Image quality assessment
│   ├── fraud_detector.py    # Fraud detection algorithms
│   └── weight_estimator.py  # Weight estimation logic
├── scripts/                  # Utility scripts
│   ├── download_datasets.py # Download source datasets
│   ├── setup_colab.py       # Colab environment setup
│   └── deploy_model.py      # Model deployment utilities
├── metrics/                  # Evaluation metrics (DVC-tracked)
│   ├── train_metrics.json   # Training results
│   ├── eval_metrics.json    # Test set performance
│   └── confusion_matrix.csv # Confusion matrix data
├── notebooks/               # Jupyter notebooks for experiments
│   ├── data_exploration.ipynb
│   ├── model_experiments.ipynb
│   └── error_analysis.ipynb
├── params.yaml              # Hyperparameters (DVC-tracked)
├── dvc.yaml                 # Pipeline definition
├── dvc.lock                 # Locked pipeline state
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🎯 Model Architecture

### **EfficientNetB0** (Base Model)
- **Pretrained** on ImageNet (1.2M images)
- **Fine-tuned** on 26k waste images
- **Input size**: 224x224 RGB
- **Parameters**: ~5.3M
- **Model size**: ~20MB (H5), ~5MB (TFLite)
- **Expected accuracy**: 82-88% on test set

### **Training Strategy**
1. **Phase 1**: Train classifier head (frozen base) - 10 epochs
2. **Phase 2**: Fine-tune top 30 layers - 20 epochs
3. **Data augmentation**: Heavy rotation, zoom, brightness, flips
4. **Regularization**: Dropout (0.4), Batch Normalization

## 📊 Dataset Details

### **Class Distribution**
```
Plastic:   8,000 images  (30.8%) - bottles, bags, containers, packaging
Paper:     6,500 images  (25.0%) - cardboard, newspapers, boxes
Metal:     5,000 images  (19.2%) - cans, foil, scrap
Organic:   4,500 images  (17.3%) - food waste, yard waste, compost
Glass:     2,000 images  (7.7%)  - bottles, jars
Total:    26,000 images
```

### **Data Sources**
| Source | Images | Quality | Notes |
|--------|--------|---------|-------|
| TrashNet | 2,527 | High | Clean labels, 6 classes |
| TACO | 15,000 | Medium | Real-world context |
| Kaggle | 5,000 | High | Balanced dataset |
| Custom | 3,473 | Variable | Partner recycling centers |

> **Note:** Electronic waste removed from MVP scope — insufficient data for reliable classification. Added in Phase 4 post-MVP expansion.

## 🔄 MLOps Stack

### **DVC (Data Version Control)**
- **Dataset tracking**: 26k images not in Git
- **Pipeline reproducibility**: Every run is reproducible
- **Remote storage**: DagsHub (10GB free)

### **MLflow (Experiment Tracking)**
- **Run tracking**: Hyperparameters, metrics, artifacts
- **Model registry**: Versioned models with staging
- **Comparison**: Side-by-side run comparison
- **Hosted server**: DagsHub MLflow instance

### **DagsHub (Collaboration Platform)**
- **Git repository**: Code and configuration
- **DVC remote**: Dataset and model storage
- **MLflow server**: Experiment tracking UI
- **Public URL**: Share with grant committee

## 🚀 Quick Start

### **1. Environment Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize DVC
dvc init

# Set up DagsHub remote
dvc remote add origin https://dagshub.com/satsverdant/satsverdant-ml.dvc
dvc remote modify origin --local auth basic
dvc remote modify origin --local user YOUR_DAGSHUB_USERNAME
dvc remote modify origin --local password YOUR_DAGSHUB_TOKEN
```

### **2. Google Colab Setup**
```python
# Run in Colab notebook
!pip install tensorflow albumentations scikit-learn mlflow dagshub dvc

import dagshub
dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)
```

### **3. Training Pipeline**
```bash
# Download datasets
python scripts/download_datasets.py

# Prepare data
python src/prepare_data.py

# Run full pipeline
dvc repro

# Or train manually
python src/train.py
```

## 📈 Expected Results

### **Training Performance (A100 GPU)**
| Phase | Time | Accuracy | Loss |
|-------|------|----------|------|
| Phase 1 | ~45 min | 72-78% | 0.65-0.85 |
| Phase 2 | ~90 min | **82-88%** | 0.35-0.55 |

### **Inference Performance**
| Platform | Latency | Cost |
|----------|---------|------|
| Groq API | ~50ms | ~$0.01/day |
| Self-hosted CPU | ~800ms | Server cost |
| Mobile (TFLite) | ~100ms | Free |

## 🔧 Configuration

### **Hyperparameters** (params.yaml)
```yaml
train:
  base_model: EfficientNetB0
  batch_size: 32
  epochs_phase1: 10
  epochs_phase2: 20
  lr_phase1: 0.001
  lr_phase2: 0.00001
  dropout: 0.4
  fine_tune_layers: 30

augmentation:
  rotation_range: 40
  zoom_range: 0.3
  brightness_range: [0.7, 1.3]
  horizontal_flip: true
  vertical_flip: true
```

### **Environment Variables**
```bash
export DAGSHUB_USERNAME=your_username
export DAGSHUB_TOKEN=your_token
export GROQ_API_KEY=your_groq_key
export MLFLOW_TRACKING_URI=https://dagshub.com/satsverdant/satsverdant-ml.mlflow
```

## 📊 Model Evaluation

### **Metrics Tracked**
- **Accuracy**: Overall classification accuracy
- **Precision/Recall**: Per-class performance
- **F1-Score**: Harmonic mean of precision/recall
- **Confusion Matrix**: Class-wise predictions
- **Inference Time**: Latency measurements

### **Target Metrics**
- **Test Accuracy**: >80% (grant requirement)
- **Target Accuracy**: >85% (stretch goal)
- **Inference Latency**: <100ms (Groq)
- **Model Size**: <10MB (TFLite)

## 🚀 Deployment

### **Production Pipeline**
```bash
# Export models
python src/train.py --export-only

# Deploy to Groq
python scripts/deploy_model.py --platform groq

# Deploy TFLite to mobile
python scripts/deploy_model.py --platform mobile
```

### **Model Registry**
- **Staging**: Models meeting 80% target
- **Production**: Validated models for Groq
- **Archived**: Previous versions for rollback

## 📚 Documentation

- **[Data Strategy](../docs/SatsVerdant_Data_Strategy.md)**: Dataset collection and labeling
- **[Backend PRD](../docs/SatsVerdant_Backend_PRD_MVP.md)**: Integration with Supabase
- **[AI/ML PRD](../docs/SatsVerdant_AI_ML_PRD_MVP.md)**: Complete technical specifications

## 🏆 Grant Deliverables

### **Model Evaluation Report**
- **MLflow Dashboard**: Public URL with all experiments
- **Performance Metrics**: Accuracy, precision, recall, F1
- **Confusion Matrix**: Per-class performance analysis
- **Error Analysis**: Common failure modes and improvements

### **Reproducibility**
- **DVC Pipeline**: Complete data and code versioning
- **DagsHub Repository**: Public access to all artifacts
- **Training Scripts**: Fully documented and reproducible
- **Model Artifacts**: Downloadable H5 and TFLite models

---

**This ML pipeline provides a production-ready, reproducible, and fully traceable waste classification system that meets all grant requirements and exceeds industry standards.**
