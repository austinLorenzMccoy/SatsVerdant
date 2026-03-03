# SatsVerdant ML Training - Google Colab Notebook

This notebook provides a complete environment for training the SatsVerdant waste classification model in Google Colab with A100 GPU.

## 🚀 Quick Start

1. **Open this notebook in Google Colab**
2. **Run the setup cell** to install dependencies
3. **Set your DagsHub credentials**
4. **Start training!**

## 📋 Setup Instructions

```python
# 1. Install dependencies
!python scripts/setup_colab.py

# 2. Set DagsHub credentials
import os
os.environ['DAGSHUB_USERNAME'] = 'your_dagshub_username'
os.environ['DAGSHUB_TOKEN'] = 'your_dagshub_token'

# 3. Initialize DagsHub
import dagshub
dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)

# 4. Prepare dataset
!python src/prepare_data.py

# 5. Start training
!python src/train.py
```

## 📊 Expected Results

- **Training Time**: ~2.5 hours on A100 GPU
- **Test Accuracy**: 82-88%
- **Model Size**: ~20MB (H5), ~5MB (TFLite)
- **Inference Time**: ~50ms via Groq API

## 📈 Monitoring

- **MLflow Dashboard**: https://dagshub.com/satsverdant/satsverdant-ml/mlflow
- **Real-time Training**: Watch metrics in Colab
- **Model Registry**: Automatic versioning and staging

## 🔧 Advanced Usage

### Custom Hyperparameters
Edit `params.yaml` to modify training parameters:
- Batch size
- Learning rates
- Augmentation settings
- Model architecture

### Resume Training
```bash
!python src/train.py --resume
```

### Export Only
```bash
!python src/train.py --export-only
```

## 📚 Documentation

- **[README.md](../README.md)**: Full pipeline documentation
- **[AI/ML PRD](../../docs/SatsVerdant_AI_ML_PRD_MVP.md)**: Technical specifications
- **[Backend PRD](../../docs/SatsVerdant_Backend_PRD_MVP.md)**: Integration details
