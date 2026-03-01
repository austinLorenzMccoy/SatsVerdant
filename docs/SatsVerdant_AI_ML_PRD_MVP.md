# SatsVerdant AI/ML PRD - MVP

## 1. Executive Summary

**Project:** SatsVerdant AI/ML System  
**Version:** 1.0 (MVP)  
**Timeline:** 8 weeks (parallel with backend development)  
**Goal:** Production-ready AI classification and fraud detection system for waste verification with >85% accuracy and <30 second inference time.

**Core Components:**
1. **Waste Classification Model** - Computer vision for waste type identification
2. **Weight Estimation Model** - Regression for weight prediction
3. **Fraud Detection System** - Multi-signal anomaly detection
4. **Quality Grading Model** - Image quality assessment

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI/ML Pipeline                            │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────────┐
                │             │                 │
         ┌──────▼──────┐ ┌───▼────────┐ ┌─────▼──────┐
         │Waste        │ │Weight      │ │Quality     │
         │Classifier   │ │Estimator   │ │Grader      │
         └──────┬──────┘ └───┬────────┘ └─────┬──────┘
                │            │                 │
                └────────────┼─────────────────┘
                             │
                      ┌──────▼──────┐
                      │Fraud        │
                      │Detection    │
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │Submission   │
                      │Score        │
                      └─────────────┘
```

---

## 3. Technical Stack

### **3.1 Frameworks & Libraries**

**Deep Learning:**
- **TensorFlow 2.15** or **PyTorch 2.1** (choose one for consistency)
- **TensorFlow Lite** for mobile deployment
- **ONNX** for model portability

**Computer Vision:**
- **OpenCV 4.8** - Image preprocessing
- **Pillow 10.0** - Image manipulation
- **imgaug 0.4** - Data augmentation

**ML Utilities:**
- **scikit-learn 1.3** - Classical ML algorithms, metrics
- **NumPy 1.24** - Numerical operations
- **Pandas 2.1** - Data manipulation
- **matplotlib/seaborn** - Visualization

**Model Serving:**
- **TensorFlow Serving** or **TorchServe**
- **FastAPI** - REST API wrapper
- **Redis** - Model result caching

**Experiment Tracking:**
- **MLflow** - Experiment tracking, model registry
- **Weights & Biases** - Training monitoring (optional)
- **TensorBoard** - Training visualization

**Data Management:**
- **DVC (Data Version Control)** - Dataset versioning
- **Label Studio** - Data annotation
- **Augly** - Data augmentation

---

## 4. Model 1: Waste Classification

### **4.1 Objective**
Classify waste images into 5 categories: plastic, paper, metal, organic, electronic with >85% accuracy and <30 second inference time.

### **4.2 Model Architecture**

**Base Model:** Transfer Learning with MobileNetV3-Large or EfficientNet-B0

**Choice Rationale:**
- **MobileNetV3-Large**: Fast inference (40ms), good accuracy (75% ImageNet top-1)
- **EfficientNet-B0**: Better accuracy (77% ImageNet top-1), slightly slower (60ms)

**Recommendation for MVP:** MobileNetV3-Large for speed, upgrade to EfficientNet post-MVP if accuracy insufficient.

```python
# TensorFlow Implementation
import tensorflow as tf
from tensorflow.keras import layers, models

def create_waste_classifier(
    num_classes=5,
    input_shape=(224, 224, 3),
    base_model_name='MobileNetV3Large'
):
    # Load pre-trained base model
    if base_model_name == 'MobileNetV3Large':
        base_model = tf.keras.applications.MobileNetV3Large(
            input_shape=input_shape,
            include_top=False,
            weights='imagenet'
        )
    elif base_model_name == 'EfficientNetB0':
        base_model = tf.keras.applications.EfficientNetB0(
            input_shape=input_shape,
            include_top=False,
            weights='imagenet'
        )
    
    # Freeze base model initially
    base_model.trainable = False
    
    # Build classification head
    inputs = layers.Input(shape=input_shape, name='image_input')
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D(name='global_avg_pool')(x)
    x = layers.Dropout(0.3, name='dropout_1')(x)
    x = layers.Dense(256, activation='relu', name='dense_1')(x)
    x = layers.BatchNormalization(name='batch_norm_1')(x)
    x = layers.Dropout(0.2, name='dropout_2')(x)
    
    # Output layer with softmax
    outputs = layers.Dense(num_classes, activation='softmax', name='predictions')(x)
    
    model = models.Model(inputs, outputs, name='waste_classifier')
    
    return model, base_model

# Create model
model, base_model = create_waste_classifier()

# Compile
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss='categorical_crossentropy',
    metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=2, name='top_2_accuracy')]
)

model.summary()
```

**Model Summary:**
```
Total params: 5,483,032
Trainable params: 1,326,088
Non-trainable params: 4,156,944
```

### **4.3 Dataset Requirements**

**Minimum Dataset Size (MVP):**
```
Plastic:     5,000 images (bottles, bags, containers, packaging)
Paper:       4,000 images (cardboard, newspapers, documents, boxes)
Metal:       3,000 images (cans, foil, scrap metal)
Organic:     2,000 images (food waste, yard waste, compost)
Electronic:  1,000 images (phones, cables, batteries) [optional for MVP]

Total:      15,000 images minimum
```

**Ideal Dataset Size (Post-MVP):**
```
Each category: 10,000+ images
Total:        50,000+ images
```

**Data Sources:**
1. **Public Datasets:**
   - TrashNet (2,527 images, 6 classes)
   - TACO (Trash Annotations in Context) - 15,000 images
   - Waste Classification Data (Kaggle)
   - OpenImages subset (search: "plastic bottle", "cardboard", etc.)

2. **Custom Collection:**
   - Beta users submissions
   - Staged photo collection (controlled environment)
   - Partner with recycling centers

3. **Synthetic Data:**
   - 3D rendering of waste items
   - Background augmentation
   - Cutout/paste augmentation

**Data Split:**
```
Training:    70% (10,500 images)
Validation:  15% (2,250 images)
Test:        15% (2,250 images)
```

### **4.4 Data Preprocessing Pipeline**

```python
import cv2
import numpy as np
from PIL import Image
import albumentations as A

class WasteImagePreprocessor:
    def __init__(self, target_size=(224, 224)):
        self.target_size = target_size
        
        # Training augmentation pipeline
        self.train_transform = A.Compose([
            A.Resize(target_size[0], target_size[1]),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.2),
            A.Rotate(limit=30, p=0.5),
            A.RandomBrightnessContrast(p=0.3),
            A.GaussianBlur(blur_limit=(3, 7), p=0.2),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.2),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.2, rotate_limit=15, p=0.5),
            A.CoarseDropout(max_holes=8, max_height=32, max_width=32, p=0.3),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        # Validation/Test augmentation (minimal)
        self.val_transform = A.Compose([
            A.Resize(target_size[0], target_size[1]),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    
    def preprocess_image(self, image_path_or_bytes, mode='train'):
        # Load image
        if isinstance(image_path_or_bytes, str):
            image = cv2.imread(image_path_or_bytes)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image = cv2.imdecode(
                np.frombuffer(image_path_or_bytes, np.uint8),
                cv2.IMREAD_COLOR
            )
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply transformations
        if mode == 'train':
            transformed = self.train_transform(image=image)
        else:
            transformed = self.val_transform(image=image)
        
        return transformed['image']
    
    def preprocess_batch(self, image_paths, mode='train'):
        images = []
        for path in image_paths:
            img = self.preprocess_image(path, mode)
            images.append(img)
        return np.array(images)

# Usage
preprocessor = WasteImagePreprocessor(target_size=(224, 224))
processed_image = preprocessor.preprocess_image('waste_photo.jpg', mode='inference')
```

### **4.5 Training Strategy**

**Phase 1: Transfer Learning (Frozen Base)**
```python
# Freeze base model, train only classification head
base_model.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

history_phase1 = model.fit(
    train_dataset,
    epochs=10,
    validation_data=val_dataset,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=2),
        tf.keras.callbacks.ModelCheckpoint('models/waste_classifier_phase1.h5', save_best_only=True)
    ]
)
```

**Phase 2: Fine-Tuning (Unfreeze Top Layers)**
```python
# Unfreeze top 20% of base model layers
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),  # Lower LR for fine-tuning
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

history_phase2 = model.fit(
    train_dataset,
    epochs=15,
    validation_data=val_dataset,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=3),
        tf.keras.callbacks.ModelCheckpoint('models/waste_classifier_final.h5', save_best_only=True)
    ]
)
```

**Training Hyperparameters:**
```python
HYPERPARAMETERS = {
    'batch_size': 32,
    'initial_lr': 1e-3,
    'fine_tune_lr': 1e-4,
    'phase1_epochs': 10,
    'phase2_epochs': 15,
    'dropout_rate': 0.3,
    'dense_units': 256,
    'weight_decay': 1e-4
}
```

### **4.6 Evaluation Metrics**

```python
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report
)
import seaborn as sns
import matplotlib.pyplot as plt

class WasteClassifierEvaluator:
    def __init__(self, model, test_dataset, class_names):
        self.model = model
        self.test_dataset = test_dataset
        self.class_names = class_names
    
    def evaluate(self):
        # Predictions
        y_true = []
        y_pred = []
        y_pred_proba = []
        
        for images, labels in self.test_dataset:
            predictions = self.model.predict(images, verbose=0)
            y_pred_proba.extend(predictions)
            y_pred.extend(np.argmax(predictions, axis=1))
            y_true.extend(np.argmax(labels, axis=1))
        
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        y_pred_proba = np.array(y_pred_proba)
        
        # Metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average='weighted'
        )
        
        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred)
        
        # Per-class metrics
        report = classification_report(
            y_true, y_pred,
            target_names=self.class_names,
            output_dict=True
        )
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm,
            'classification_report': report,
            'predictions': y_pred,
            'probabilities': y_pred_proba,
            'true_labels': y_true
        }
    
    def plot_confusion_matrix(self, cm):
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=self.class_names,
            yticklabels=self.class_names
        )
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png')
        plt.close()
    
    def plot_per_class_metrics(self, report):
        classes = list(report.keys())[:-3]  # Exclude avg metrics
        precisions = [report[c]['precision'] for c in classes]
        recalls = [report[c]['recall'] for c in classes]
        f1_scores = [report[c]['f1-score'] for c in classes]
        
        x = np.arange(len(classes))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(x - width, precisions, width, label='Precision')
        ax.bar(x, recalls, width, label='Recall')
        ax.bar(x + width, f1_scores, width, label='F1-Score')
        
        ax.set_xlabel('Waste Type')
        ax.set_ylabel('Score')
        ax.set_title('Per-Class Performance Metrics')
        ax.set_xticks(x)
        ax.set_xticklabels(classes)
        ax.legend()
        plt.tight_layout()
        plt.savefig('per_class_metrics.png')
        plt.close()

# Usage
evaluator = WasteClassifierEvaluator(
    model=model,
    test_dataset=test_dataset,
    class_names=['plastic', 'paper', 'metal', 'organic', 'electronic']
)
results = evaluator.evaluate()
evaluator.plot_confusion_matrix(results['confusion_matrix'])
evaluator.plot_per_class_metrics(results['classification_report'])
```

**Target Metrics (MVP):**
```
Overall Accuracy:    ≥ 85%
Per-Class Precision: ≥ 80%
Per-Class Recall:    ≥ 80%
Inference Time:      < 1 second (CPU)
                     < 100ms (GPU)
```

### **4.7 Inference Pipeline**

```python
class WasteClassificationInference:
    def __init__(self, model_path, threshold=0.7):
        self.model = tf.keras.models.load_model(model_path)
        self.preprocessor = WasteImagePreprocessor()
        self.threshold = threshold
        self.class_names = ['plastic', 'paper', 'metal', 'organic', 'electronic']
    
    def classify(self, image_bytes):
        # Preprocess
        processed_image = self.preprocessor.preprocess_image(
            image_bytes, mode='inference'
        )
        processed_image = np.expand_dims(processed_image, axis=0)
        
        # Predict
        predictions = self.model.predict(processed_image, verbose=0)[0]
        
        # Get top prediction
        class_idx = np.argmax(predictions)
        confidence = float(predictions[class_idx])
        waste_type = self.class_names[class_idx]
        
        # Get top-2 for ambiguity detection
        top_2_indices = np.argsort(predictions)[-2:][::-1]
        top_2_probs = predictions[top_2_indices]
        
        # Check if confident
        is_confident = confidence >= self.threshold
        is_ambiguous = (top_2_probs[0] - top_2_probs[1]) < 0.15  # Close call
        
        return {
            'waste_type': waste_type,
            'confidence': confidence,
            'all_probabilities': {
                self.class_names[i]: float(predictions[i])
                for i in range(len(self.class_names))
            },
            'is_confident': is_confident,
            'is_ambiguous': is_ambiguous,
            'top_2_classes': [self.class_names[i] for i in top_2_indices],
            'top_2_probabilities': [float(p) for p in top_2_probs]
        }

# Usage
classifier = WasteClassificationInference(
    model_path='models/waste_classifier_final.h5',
    threshold=0.7
)

with open('waste_image.jpg', 'rb') as f:
    image_bytes = f.read()

result = classifier.classify(image_bytes)
print(f"Type: {result['waste_type']}, Confidence: {result['confidence']:.2%}")
```

---

## 5. Model 2: Weight Estimation

### **5.1 Objective**
Estimate weight of waste in kilograms from image with ±20% accuracy (RMSE < 0.2 kg for items 0.5-2kg).

### **5.2 Approach**

**MVP Approach:** Heuristic-based estimation (rule-based)
**Post-MVP:** Regression model trained on labeled data

**Heuristic Model (MVP):**
```python
class WeightEstimator:
    def __init__(self):
        # Base weights by waste type (in kg)
        self.base_weights = {
            'plastic': 0.5,    # Typical: plastic bottle
            'paper': 1.0,      # Typical: stack of cardboard
            'metal': 0.8,      # Typical: aluminum cans
            'organic': 1.5,    # Typical: food waste bag
            'electronic': 0.3  # Typical: phone/cable
        }
        
        # Object count multipliers (if detected)
        self.count_multipliers = {
            1: 1.0,
            2: 1.8,   # Slight efficiency
            3: 2.5,
            4: 3.2,
            5: 4.0
        }
    
    def estimate_weight(self, waste_type, image_metadata=None):
        base_weight = self.base_weights.get(waste_type, 1.0)
        
        # Add random variance ±20%
        variance = np.random.uniform(0.8, 1.2)
        estimated_weight = base_weight * variance
        
        # If object count available (from object detection)
        if image_metadata and 'object_count' in image_metadata:
            count = min(image_metadata['object_count'], 5)
            multiplier = self.count_multipliers.get(count, 1.0)
            estimated_weight *= multiplier
        
        # Round to 1 decimal place
        return round(estimated_weight, 1)

# Usage
estimator = WeightEstimator()
weight_kg = estimator.estimate_weight('plastic', {'object_count': 3})
print(f"Estimated weight: {weight_kg} kg")
```

**Regression Model (Post-MVP):**
```python
import tensorflow as tf

def create_weight_regression_model(base_model_name='MobileNetV3Small'):
    # Smaller base model for faster inference
    base_model = tf.keras.applications.MobileNetV3Small(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False
    
    inputs = layers.Input(shape=(224, 224, 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(64, activation='relu')(x)
    
    # Single output: weight in kg
    outputs = layers.Dense(1, activation='linear', name='weight_output')(x)
    
    model = models.Model(inputs, outputs, name='weight_estimator')
    
    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['mae', 'mape']  # Mean Absolute Error, Mean Absolute Percentage Error
    )
    
    return model

# Training
weight_model = create_weight_regression_model()
# Note: Requires labeled dataset with actual weights
```

---

## 6. Model 3: Quality Grading

### **6.1 Objective**
Assign quality grade (A, B, C, D) based on image clarity, lighting, and waste condition.

### **6.2 Implementation**

```python
import cv2

class QualityGrader:
    def __init__(self):
        self.grade_thresholds = {
            'A': {'blur_variance': 100, 'brightness': (50, 200), 'contrast': 40},
            'B': {'blur_variance': 50, 'brightness': (30, 220), 'contrast': 25},
            'C': {'blur_variance': 20, 'brightness': (20, 240), 'contrast': 15},
            'D': {'blur_variance': 0, 'brightness': (0, 255), 'contrast': 0}
        }
    
    def calculate_blur(self, image):
        # Laplacian variance for blur detection
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var
    
    def calculate_brightness(self, image):
        # Average brightness
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return np.mean(gray)
    
    def calculate_contrast(self, image):
        # Standard deviation as contrast measure
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return np.std(gray)
    
    def grade_image(self, image_bytes):
        # Load image
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Calculate metrics
        blur_score = self.calculate_blur(image)
        brightness = self.calculate_brightness(image)
        contrast = self.calculate_contrast(image)
        
        # Determine grade
        if (blur_score >= 100 and 
            50 <= brightness <= 200 and 
            contrast >= 40):
            grade = 'A'
        elif (blur_score >= 50 and 
              30 <= brightness <= 220 and 
              contrast >= 25):
            grade = 'B'
        elif (blur_score >= 20 and 
              20 <= brightness <= 240 and 
              contrast >= 15):
            grade = 'C'
        else:
            grade = 'D'
        
        return {
            'grade': grade,
            'blur_score': float(blur_score),
            'brightness': float(brightness),
            'contrast': float(contrast),
            'quality_details': {
                'is_blurry': blur_score < 50,
                'is_too_dark': brightness < 30,
                'is_too_bright': brightness > 220,
                'is_low_contrast': contrast < 25
            }
        }

# Usage
grader = QualityGrader()
with open('waste_image.jpg', 'rb') as f:
    image_bytes = f.read()

quality = grader.grade_image(image_bytes)
print(f"Quality Grade: {quality['grade']}")
```

**Quality Grading Criteria:**
```
Grade A (1.0x multiplier):
  - Sharp image (blur variance > 100)
  - Good lighting (brightness 50-200)
  - High contrast (std > 40)
  - Clear waste item visible

Grade B (0.8x multiplier):
  - Slightly blurry (blur variance 50-100)
  - Acceptable lighting
  - Medium contrast
  
Grade C (0.6x multiplier):
  - Blurry (blur variance 20-50)
  - Poor lighting
  - Low contrast
  
Grade D (0.4x multiplier):
  - Very blurry or unclear
  - Cannot verify waste properly
```

---

## 7. Fraud Detection System

### **7.1 Objective**
Detect fraudulent submissions (duplicates, location spoofing, rapid submissions) with >90% precision to minimize false positives.

### **7.2 Multi-Signal Detection**

```python
import imagehash
from PIL import Image
import hashlib
from datetime import datetime, timedelta

class FraudDetectionSystem:
    def __init__(self, db_connection):
        self.db = db_connection
        
        # Thresholds
        self.duplicate_hash_threshold = 5
        self.location_radius_meters = 50
        self.rapid_submission_threshold = 5  # submissions per hour
        self.low_confidence_threshold = 0.7
        
    # === 1. Image Duplicate Detection ===
    def calculate_perceptual_hash(self, image_bytes):
        """Calculate perceptual hash for near-duplicate detection"""
        image = Image.open(io.BytesIO(image_bytes))
        
        # Multiple hash types for robustness
        phash = imagehash.phash(image)
        dhash = imagehash.dhash(image)
        whash = imagehash.whash(image)
        
        return {
            'phash': str(phash),
            'dhash': str(dhash),
            'whash': str(whash)
        }
    
    def check_duplicate_image(self, user_id, image_hashes):
        """Check if image is duplicate of previous submission"""
        # Query recent submissions from same user
        recent_submissions = self.db.query("""
            SELECT id, image_phash, image_dhash, image_whash
            FROM submissions
            WHERE user_id = %s
              AND created_at > NOW() - INTERVAL '30 days'
              AND image_phash IS NOT NULL
        """, (user_id,))
        
        for sub in recent_submissions:
            # Calculate hash distances
            phash_dist = imagehash.hex_to_hash(image_hashes['phash']) - \
                        imagehash.hex_to_hash(sub['image_phash'])
            dhash_dist = imagehash.hex_to_hash(image_hashes['dhash']) - \
                        imagehash.hex_to_hash(sub['image_dhash'])
            whash_dist = imagehash.hex_to_hash(image_hashes['whash']) - \
                        imagehash.hex_to_hash(sub['image_whash'])
            
            # Average distance
            avg_distance = (phash_dist + dhash_dist + whash_dist) / 3
            
            if avg_distance < self.duplicate_hash_threshold:
                return {
                    'is_duplicate': True,
                    'duplicate_of': sub['id'],
                    'similarity_score': 1 - (avg_distance / 64),  # Normalize to 0-1
                    'hash_distance': float(avg_distance)
                }
        
        return {'is_duplicate': False}
    
    # === 2. Location Clustering Detection ===
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS coordinates in meters"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        return c * r
    
    def check_location_clustering(self, user_id, latitude, longitude):
        """Detect if too many submissions from same location"""
        recent_locations = self.db.query("""
            SELECT latitude, longitude, created_at
            FROM submissions
            WHERE user_id = %s
              AND latitude IS NOT NULL
              AND created_at > NOW() - INTERVAL '7 days'
        """, (user_id,))
        
        same_location_count = 0
        for loc in recent_locations:
            distance = self.haversine_distance(
                latitude, longitude,
                loc['latitude'], loc['longitude']
            )
            
            if distance < self.location_radius_meters:
                same_location_count += 1
        
        if same_location_count > 5:
            return {
                'flag': 'location_clustering',
                'severity': 'medium',
                'same_location_submissions': same_location_count,
                'description': f'{same_location_count} submissions within 50m in past 7 days'
            }
        
        return None
    
    # === 3. Rapid Submission Detection ===
    def check_rapid_submissions(self, user_id):
        """Detect suspiciously rapid submissions"""
        recent_count = self.db.query("""
            SELECT COUNT(*) as count
            FROM submissions
            WHERE user_id = %s
              AND created_at > NOW() - INTERVAL '1 hour'
        """, (user_id,)).fetchone()
        
        if recent_count['count'] >= self.rapid_submission_threshold:
            return {
                'flag': 'rapid_submission',
                'severity': 'high',
                'submissions_last_hour': recent_count['count'],
                'description': f'{recent_count["count"]} submissions in past hour (threshold: {self.rapid_submission_threshold})'
            }
        
        return None
    
    # === 4. Low Confidence Pattern Detection ===
    def check_low_confidence_pattern(self, user_id, current_confidence):
        """Detect pattern of low-confidence submissions"""
        low_conf_count = self.db.query("""
            SELECT COUNT(*) as count
            FROM submissions
            WHERE user_id = %s
              AND ai_confidence < %s
              AND created_at > NOW() - INTERVAL '7 days'
        """, (user_id, self.low_confidence_threshold)).fetchone()
        
        if low_conf_count['count'] >= 3 and current_confidence < self.low_confidence_threshold:
            return {
                'flag': 'low_confidence_pattern',
                'severity': 'low',
                'low_confidence_count': low_conf_count['count'],
                'description': f'{low_conf_count["count"]} low-confidence submissions in 7 days'
            }
        
        return None
    
    # === 5. Device Fingerprinting ===
    def check_device_fingerprint(self, user_id, device_info):
        """Check if device fingerprint matches multiple accounts"""
        device_hash = hashlib.sha256(
            f"{device_info.get('model', '')}{device_info.get('os', '')}".encode()
        ).hexdigest()
        
        account_count = self.db.query("""
            SELECT COUNT(DISTINCT user_id) as count
            FROM submissions
            WHERE device_info->>'fingerprint' = %s
              AND created_at > NOW() - INTERVAL '30 days'
        """, (device_hash,)).fetchone()
        
        if account_count['count'] > 3:
            return {
                'flag': 'multiple_accounts',
                'severity': 'critical',
                'account_count': account_count['count'],
                'description': f'Device fingerprint linked to {account_count["count"]} accounts'
            }
        
        return None
    
    # === 6. Composite Fraud Score ===
    def calculate_fraud_score(self, submission_data):
        """Calculate overall fraud score (0-1)"""
        flags = []
        score = 0.0
        
        # Check all signals
        user_id = submission_data['user_id']
        
        # 1. Duplicate image (weight: 0.5)
        image_hashes = self.calculate_perceptual_hash(submission_data['image_bytes'])
        duplicate_check = self.check_duplicate_image(user_id, image_hashes)
        if duplicate_check['is_duplicate']:
            score += 0.5 * duplicate_check['similarity_score']
            flags.append({
                'type': 'duplicate_image',
                'severity': 'high',
                'details': duplicate_check
            })
        
        # 2. Location clustering (weight: 0.2)
        if submission_data.get('latitude') and submission_data.get('longitude'):
            location_flag = self.check_location_clustering(
                user_id,
                submission_data['latitude'],
                submission_data['longitude']
            )
            if location_flag:
                score += 0.2
                flags.append(location_flag)
        
        # 3. Rapid submissions (weight: 0.3)
        rapid_flag = self.check_rapid_submissions(user_id)
        if rapid_flag:
            score += 0.3
            flags.append(rapid_flag)
        
        # 4. Low confidence pattern (weight: 0.1)
        if 'ai_confidence' in submission_data:
            conf_flag = self.check_low_confidence_pattern(
                user_id,
                submission_data['ai_confidence']
            )
            if conf_flag:
                score += 0.1
                flags.append(conf_flag)
        
        # 5. Device fingerprint (weight: 0.4 - can exceed 1.0 for critical)
        if submission_data.get('device_info'):
            device_flag = self.check_device_fingerprint(
                user_id,
                submission_data['device_info']
            )
            if device_flag:
                score += 0.4
                flags.append(device_flag)
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        # Determine action
        if score >= 0.8:
            action = 'auto_reject'
        elif score >= 0.5:
            action = 'flag_for_manual_review'
        elif score >= 0.3:
            action = 'warning'
        else:
            action = 'approve'
        
        return {
            'fraud_score': round(score, 3),
            'flags': flags,
            'recommended_action': action,
            'image_hashes': image_hashes
        }

# Usage
fraud_detector = FraudDetectionSystem(db_connection)

submission_data = {
    'user_id': 'user_123',
    'image_bytes': image_bytes,
    'latitude': 52.3676,
    'longitude': 4.9041,
    'ai_confidence': 0.65,
    'device_info': {'model': 'iPhone 14', 'os': 'iOS 17'}
}

fraud_result = fraud_detector.calculate_fraud_score(submission_data)
print(f"Fraud Score: {fraud_result['fraud_score']}")
print(f"Action: {fraud_result['recommended_action']}")
```

### **7.3 Fraud Detection Metrics**

**Target Performance:**
```
Precision:     ≥ 90% (minimize false positives)
Recall:        ≥ 70% (catch most fraud)
False Positive Rate: < 5%
```

**Monitoring:**
```python
class FraudDetectionMonitor:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def calculate_metrics(self, time_period_days=30):
        # Get flagged submissions and their outcomes
        data = self.db.query("""
            SELECT 
                fraud_score,
                status,
                fraud_flags,
                validator_decision
            FROM submissions
            WHERE created_at > NOW() - INTERVAL '%s days'
              AND fraud_score > 0
        """, (time_period_days,))
        
        # Calculate TP, FP, TN, FN
        tp = fp = tn = fn = 0
        
        for row in data:
            is_fraud_flagged = row['fraud_score'] >= 0.5
            is_actually_fraud = row['validator_decision'] == 'rejected'
            
            if is_fraud_flagged and is_actually_fraud:
                tp += 1
            elif is_fraud_flagged and not is_actually_fraud:
                fp += 1
            elif not is_fraud_flagged and is_actually_fraud:
                fn += 1
            else:
                tn += 1
        
        # Metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'false_positive_rate': fpr,
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn
        }
```

---

## 8. Complete Inference Pipeline

### **8.1 Unified Classification Service**

```python
import time
from typing import Dict, Any

class SatsVerdantMLService:
    """Unified ML service for waste classification, weight estimation, quality grading, and fraud detection"""
    
    def __init__(
        self,
        classifier_model_path: str,
        db_connection,
        confidence_threshold: float = 0.7
    ):
        # Load models
        self.classifier = WasteClassificationInference(
            classifier_model_path,
            threshold=confidence_threshold
        )
        self.weight_estimator = WeightEstimator()
        self.quality_grader = QualityGrader()
        self.fraud_detector = FraudDetectionSystem(db_connection)
        
        # Performance tracking
        self.inference_times = []
    
    def process_submission(
        self,
        image_bytes: bytes,
        user_id: str,
        latitude: float = None,
        longitude: float = None,
        device_info: Dict = None
    ) -> Dict[str, Any]:
        """
        Complete ML pipeline for waste submission processing
        
        Returns:
            Complete classification result with fraud analysis
        """
        start_time = time.time()
        
        try:
            # 1. Image Quality Grading
            quality_start = time.time()
            quality_result = self.quality_grader.grade_image(image_bytes)
            quality_time = time.time() - quality_start
            
            # 2. Waste Classification
            classification_start = time.time()
            classification_result = self.classifier.classify(image_bytes)
            classification_time = time.time() - classification_start
            
            # 3. Weight Estimation
            weight_start = time.time()
            estimated_weight = self.weight_estimator.estimate_weight(
                classification_result['waste_type']
            )
            weight_time = time.time() - weight_start
            
            # 4. Fraud Detection
            fraud_start = time.time()
            fraud_result = self.fraud_detector.calculate_fraud_score({
                'user_id': user_id,
                'image_bytes': image_bytes,
                'latitude': latitude,
                'longitude': longitude,
                'ai_confidence': classification_result['confidence'],
                'device_info': device_info
            })
            fraud_time = time.time() - fraud_start
            
            # Total inference time
            total_time = time.time() - start_time
            self.inference_times.append(total_time)
            
            # Combine results
            result = {
                'classification': {
                    'waste_type': classification_result['waste_type'],
                    'confidence': classification_result['confidence'],
                    'is_confident': classification_result['is_confident'],
                    'is_ambiguous': classification_result['is_ambiguous'],
                    'all_probabilities': classification_result['all_probabilities']
                },
                'weight_estimation': {
                    'estimated_weight_kg': estimated_weight
                },
                'quality': {
                    'grade': quality_result['grade'],
                    'blur_score': quality_result['blur_score'],
                    'brightness': quality_result['brightness'],
                    'contrast': quality_result['contrast'],
                    'quality_details': quality_result['quality_details']
                },
                'fraud_analysis': {
                    'fraud_score': fraud_result['fraud_score'],
                    'flags': fraud_result['flags'],
                    'recommended_action': fraud_result['recommended_action']
                },
                'metadata': {
                    'total_inference_time_seconds': round(total_time, 3),
                    'classification_time_seconds': round(classification_time, 3),
                    'quality_grading_time_seconds': round(quality_time, 3),
                    'weight_estimation_time_seconds': round(weight_time, 3),
                    'fraud_detection_time_seconds': round(fraud_time, 3),
                    'model_version': '1.0.0',
                    'timestamp': time.time()
                },
                'image_hashes': fraud_result['image_hashes']
            }
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def get_performance_stats(self):
        """Get inference performance statistics"""
        if not self.inference_times:
            return None
        
        return {
            'mean_inference_time': np.mean(self.inference_times),
            'median_inference_time': np.median(self.inference_times),
            'p95_inference_time': np.percentile(self.inference_times, 95),
            'p99_inference_time': np.percentile(self.inference_times, 99),
            'min_inference_time': np.min(self.inference_times),
            'max_inference_time': np.max(self.inference_times),
            'total_inferences': len(self.inference_times)
        }

# Usage
ml_service = SatsVerdantMLService(
    classifier_model_path='models/waste_classifier_final.h5',
    db_connection=db_conn,
    confidence_threshold=0.7
)

# Process submission
result = ml_service.process_submission(
    image_bytes=image_bytes,
    user_id='user_123',
    latitude=52.3676,
    longitude=4.9041,
    device_info={'model': 'iPhone 14', 'os': 'iOS 17'}
)

if result['success']:
    print(f"Classification: {result['data']['classification']['waste_type']}")
    print(f"Confidence: {result['data']['classification']['confidence']:.2%}")
    print(f"Weight: {result['data']['weight_estimation']['estimated_weight_kg']} kg")
    print(f"Quality: {result['data']['quality']['grade']}")
    print(f"Fraud Score: {result['data']['fraud_analysis']['fraud_score']:.3f}")
    print(f"Inference Time: {result['data']['metadata']['total_inference_time_seconds']:.3f}s")
```

---

## 9. Model Deployment

### **9.1 Model Serving Architecture**

```python
# FastAPI serving endpoint
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="SatsVerdant ML API", version="1.0.0")

# Initialize ML service
ml_service = SatsVerdantMLService(
    classifier_model_path='/models/waste_classifier_final.h5',
    db_connection=get_db_connection()
)

class SubmissionRequest(BaseModel):
    user_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_info: Optional[dict] = None

@app.post("/classify")
async def classify_waste(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None)
):
    """Classify waste submission"""
    
    # Validate file type
    if file.content_type not in ['image/jpeg', 'image/png', 'image/heic']:
        raise HTTPException(400, "Invalid image format")
    
    # Read image
    image_bytes = await file.read()
    
    # Validate file size (max 10MB)
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image too large (max 10MB)")
    
    # Process
    result = ml_service.process_submission(
        image_bytes=image_bytes,
        user_id=user_id,
        latitude=latitude,
        longitude=longitude
    )
    
    if not result['success']:
        raise HTTPException(500, f"Classification failed: {result['error']}")
    
    return result['data']

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": ml_service.classifier.model is not None,
        "version": "1.0.0"
    }

@app.get("/metrics")
async def get_metrics():
    """Get inference performance metrics"""
    return ml_service.get_performance_stats()

# Run with: uvicorn ml_api:app --host 0.0.0.0 --port 8001
```

### **9.2 Docker Deployment**

```dockerfile
# Dockerfile.ml
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt

# Copy models and code
COPY models/ ./models/
COPY ml/ ./ml/

# Expose port
EXPOSE 8001

# Run
CMD ["uvicorn", "ml.api:app", "--host", "0.0.0.0", "--port", "8001"]
```

```yaml
# docker-compose.ml.yml
version: '3.8'

services:
  ml-service:
    build:
      context: .
      dockerfile: Dockerfile.ml
    ports:
      - "8001:8001"
    environment:
      - MODEL_PATH=/app/models/waste_classifier_final.h5
      - DB_URL=postgresql://user:pass@db:5432/satsverdant
    volumes:
      - ./models:/app/models:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]  # Optional: for GPU acceleration
```

### **9.3 Model Optimization**

**TensorFlow Lite Conversion (for mobile):**
```python
import tensorflow as tf

def convert_to_tflite(model_path, output_path):
    # Load model
    model = tf.keras.models.load_model(model_path)
    
    # Convert to TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Optimization
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]  # Use FP16
    
    # Convert
    tflite_model = converter.convert()
    
    # Save
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    print(f"Model converted to TFLite: {output_path}")
    print(f"Size reduction: {os.path.getsize(model_path) / os.path.getsize(output_path):.2f}x")

# Convert
convert_to_tflite(
    'models/waste_classifier_final.h5',
    'models/waste_classifier_mobile.tflite'
)
```

**ONNX Conversion (for cross-platform):**
```python
import tf2onnx
import onnx

def convert_to_onnx(model_path, output_path):
    model = tf.keras.models.load_model(model_path)
    
    # Convert
    onnx_model, _ = tf2onnx.convert.from_keras(
        model,
        input_signature=[tf.TensorSpec(shape=[None, 224, 224, 3], dtype=tf.float32)],
        opset=13
    )
    
    # Save
    onnx.save(onnx_model, output_path)
    print(f"Model converted to ONNX: {output_path}")

convert_to_onnx(
    'models/waste_classifier_final.h5',
    'models/waste_classifier.onnx'
)
```

---

## 10. Monitoring & Maintenance

### **10.1 Model Performance Monitoring**

```python
import mlflow

class ModelMonitor:
    def __init__(self, mlflow_tracking_uri):
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        self.experiment_name = "satsverdant-production"
        mlflow.set_experiment(self.experiment_name)
    
    def log_inference(self, result, ground_truth=None):
        """Log inference result for monitoring"""
        with mlflow.start_run(run_name=f"inference_{int(time.time())}"):
            # Log predictions
            mlflow.log_param("waste_type", result['classification']['waste_type'])
            mlflow.log_metric("confidence", result['classification']['confidence'])
            mlflow.log_metric("fraud_score", result['fraud_analysis']['fraud_score'])
            mlflow.log_metric("inference_time", result['metadata']['total_inference_time_seconds'])
            
            # Log quality metrics
            mlflow.log_param("quality_grade", result['quality']['grade'])
            mlflow.log_metric("blur_score", result['quality']['blur_score'])
            
            # If ground truth available (from validator feedback)
            if ground_truth:
                is_correct = result['classification']['waste_type'] == ground_truth['waste_type']
                mlflow.log_metric("is_correct", int(is_correct))
    
    def log_daily_metrics(self, metrics):
        """Log aggregated daily metrics"""
        with mlflow.start_run(run_name=f"daily_metrics_{datetime.now().strftime('%Y-%m-%d')}"):
            mlflow.log_metrics(metrics)
    
    def detect_model_drift(self):
        """Detect if model performance is degrading"""
        # Get last 7 days of accuracy
        recent_accuracy = self.get_recent_accuracy(days=7)
        baseline_accuracy = 0.85
        
        if recent_accuracy < baseline_accuracy * 0.9:  # 10% degradation
            self.send_alert(
                f"Model accuracy degraded to {recent_accuracy:.2%} "
                f"(baseline: {baseline_accuracy:.2%})"
            )
    
    def send_alert(self, message):
        """Send alert to team"""
        # Integration with Slack, PagerDuty, etc.
        print(f"ALERT: {message}")
```

### **10.2 A/B Testing Framework**

```python
class ModelABTesting:
    def __init__(self):
        self.models = {
            'model_a': WasteClassificationInference('models/waste_classifier_v1.h5'),
            'model_b': WasteClassificationInference('models/waste_classifier_v2.h5')
        }
        self.traffic_split = 0.1  # 10% to model_b
    
    def classify_with_ab(self, image_bytes, user_id):
        # Deterministic assignment based on user_id
        user_hash = hash(user_id) % 100
        
        if user_hash < self.traffic_split * 100:
            model_name = 'model_b'
        else:
            model_name = 'model_a'
        
        result = self.models[model_name].classify(image_bytes)
        result['model_variant'] = model_name
        
        return result
```

---

## 11. Continuous Improvement

### **11.1 Active Learning Pipeline**

```python
class ActiveLearningPipeline:
    def __init__(self, db_connection, model):
        self.db = db_connection
        self.model = model
        self.uncertainty_threshold = 0.3  # Top-2 prob difference
    
    def identify_uncertain_samples(self, days=7):
        """Find submissions where model was uncertain"""
        uncertain_submissions = self.db.query("""
            SELECT id, image_ipfs_cid, ai_confidence, ai_waste_type
            FROM submissions
            WHERE created_at > NOW() - INTERVAL '%s days'
              AND ai_confidence < 0.8
              AND status IN ('approved', 'rejected')
            ORDER BY ai_confidence ASC
            LIMIT 100
        """, (days,))
        
        return uncertain_submissions
    
    def prioritize_for_labeling(self, submissions):
        """Prioritize samples for human labeling"""
        priorities = []
        
        for sub in submissions:
            # Calculate information value
            priority_score = (1 - sub['ai_confidence']) * 100
            
            priorities.append({
                'submission_id': sub['id'],
                'priority_score': priority_score,
                'current_label': sub['ai_waste_type'],
                'confidence': sub['ai_confidence']
            })
        
        return sorted(priorities, key=lambda x: x['priority_score'], reverse=True)
    
    def retrain_with_new_data(self, new_labeled_data):
        """Retrain model with newly labeled data"""
        # Load existing training data
        # Add new labeled samples
        # Retrain model
        # Evaluate on validation set
        # Deploy if improvement > 2%
        pass
```

### **11.2 Model Retraining Schedule**

```
Weekly:  Monitor performance metrics, identify drift
Monthly: Retrain with validated submissions (active learning)
Quarterly: Full model retraining with expanded dataset
```

---

## 12. Success Criteria

### **✅ Model Performance**
- [ ] Waste classification accuracy ≥ 85%
- [ ] Per-class precision/recall ≥ 80%
- [ ] Inference time < 1 second (CPU)
- [ ] Inference time < 100ms (GPU)
- [ ] Model size < 50MB (mobile)

### **✅ Fraud Detection**
- [ ] Fraud detection precision ≥ 90%
- [ ] Fraud detection recall ≥ 70%
- [ ] False positive rate < 5%
- [ ] Duplicate detection accuracy ≥ 95%

### **✅ System Performance**
- [ ] API response time < 2 seconds (p95)
- [ ] Support 1000 inferences/day (MVP)
- [ ] Scale to 10,000 inferences/day (post-MVP)

### **✅ Data Quality**
- [ ] Dataset size ≥ 15,000 images
- [ ] Balanced class distribution (±20%)
- [ ] High-quality labels (inter-annotator agreement ≥ 90%)

### **✅ Monitoring**
- [ ] Real-time performance tracking
- [ ] Model drift detection
- [ ] Alerting on degradation
- [ ] A/B testing framework

---

## 13. Risks & Mitigation

### **13.1 Technical Risks**

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Low initial accuracy** | User trust, rewards accuracy | Start with high confidence threshold (0.7), manual review for uncertain |
| **Dataset bias** | Poor performance on edge cases | Diverse data collection, stratified sampling |
| **Model overfitting** | Poor generalization | Strong augmentation, regularization, cross-validation |
| **Inference latency** | Poor UX | Model optimization, caching, async processing |
| **Fraud evolution** | Attackers adapt | Continuous monitoring, model updates, multi-signal detection |

### **13.2 Data Risks**

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Insufficient training data** | Low accuracy | Synthetic data, transfer learning, data partnerships |
| **Label quality issues** | Model learns wrong patterns | Multiple annotators, quality checks, validator feedback |
| **Distribution shift** | Model fails on new waste types | Regular retraining, active learning, model monitoring |

---

## 14. Timeline & Milestones

### **Week 1-2: Data Collection & Preparation**
- [ ] Collect/download 15,000+ images
- [ ] Set up annotation pipeline (Label Studio)
- [ ] Create train/val/test splits
- [ ] Build preprocessing pipeline

### **Week 3-4: Model Development**
- [ ] Implement classification model
- [ ] Train initial model
- [ ] Evaluate and iterate
- [ ] Implement weight estimator

### **Week 5-6: Fraud Detection**
- [ ] Implement perceptual hashing
- [ ] Build fraud detection pipeline
- [ ] Test on simulated fraud cases
- [ ] Tune thresholds

### **Week 7: Integration & Testing**
- [ ] Build unified ML service
- [ ] API development
- [ ] Integration testing with backend
- [ ] Performance optimization

### **Week 8: Deployment & Monitoring**
- [ ] Deploy to staging
- [ ] Load testing
- [ ] Set up monitoring
- [ ] Deploy to production

---

This AI/ML PRD provides everything needed to build, train, deploy, and maintain the SatsVerdant machine learning system!
