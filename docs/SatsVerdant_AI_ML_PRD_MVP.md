# SatsVerdant AI/ML PRD — MVP v2.1

## 1. Executive Summary

**Project:** SatsVerdant AI/ML System \
**Version:** 2.1 (MVP — MLOps Revised) \
**Timeline:** 8 weeks (Weeks 5–8 of 12-week grant schedule) \
**Goal:** Production-ready waste classification, fraud prevention, and location verification system achieving >80% accuracy, fully integrated into the Supabase backend and Stacks blockchain reward pipeline — with full MLOps traceability via MLflow, DVC, and DagsHub.

### What Changed from v1.0

| Area | v1.0 | v2.0 |
|---|---|---|
| Backend | FastAPI + Redis + Docker | Supabase + Edge Functions |
| Training Platform | TensorFlow Serving / TorchServe | Google Colab Pro (A100) |
| Inference | Self-hosted FastAPI ML service | Groq API (production inference) |
| Location Verification | PostGIS spatial queries | Supabase PostGIS + Radar.io geofencing |
| Anti-Fraud | Perceptual hash only | Perceptual hash + Radar.io + rate limiting |
| Model Export | ONNX + TFLite | TFLite (mobile) + H5 (backend) |
| Weight Estimation | Heuristic model (MVP) | Retained — heuristic MVP, regression post-MVP |
| Accuracy Target | 85% | 80% (grant commitment), target 85%+ |
| Experiment Tracking | W&B only | **MLflow + DagsHub (full MLOps stack)** |
| Dataset Versioning | None | **DVC + DagsHub remote storage** |
| Model Registry | None | **MLflow Model Registry via DagsHub** |

### Core Components
1. **Waste Classification Model** — EfficientNetB0 fine-tuned on 26,000-image dataset
2. **Fraud Detection System** — Perceptual hashing + Radar.io geofencing + rate limiting
3. **Quality Grader** — OpenCV-based image quality scoring
4. **Groq Inference Layer** — Production-speed classification via Groq API
5. **Supabase Edge Functions** — Serverless ML pipeline orchestration
6. **MLOps Stack** — MLflow experiment tracking + DVC data versioning + DagsHub collaboration

---

## 2. System Architecture

```
User submits photo (React Native / Web)
              |
              v
   Supabase Storage (image upload)
              |
              v
   Supabase Edge Function: /classify
   +----------------------------------+
   |  1. Quality Gate (OpenCV)        |
   |  2. Perceptual Hash (fraud)      |
   |  3. Radar.io Geofence check      |
   |  4. Groq API -> Classification   |
   |  5. Fraud Score calculation      |
   |  6. Write result to Supabase DB  |
   +----------------------------------+
              |
              v
   Supabase DB (submissions table)
              |
         +----+----+
         v         v
   Auto-approve  Flag for
   -> mint token  manual review
         |
         v
   Clarity Contract
   -> sBTC reward distribution
```

---

## 3. Technical Stack

### Training
- **Google Colab Pro** — A100 GPU (~$50/month, ~2-4 hours per full training run)
- **TensorFlow 2.15** — Model training framework
- **Albumentations** — Data augmentation
- **scikit-learn** — Evaluation metrics
- **Weights & Biases (free tier)** — Training run tracking

### Inference (Production)
- **Groq API** — Ultra-fast inference via LPU acceleration (~50ms per image)
- **Supabase Edge Functions** — Deno-based serverless orchestration
- **TensorFlow Lite** — On-device inference for React Native mobile app

### Fraud & Location
- **imagehash** — Perceptual hashing for duplicate detection
- **Radar.io** — Geofencing to verify physical presence at recycling locations
- **Supabase PostGIS** (built-in extension) — Spatial queries, no migration needed

### Storage & Database
- **Supabase Storage** — Image uploads with IPFS pinning for permanent records
- **Supabase PostgreSQL + PostGIS** — Submission records and spatial data
- **Supabase Realtime** — Live submission status updates to frontend

---

## 4. Dataset

### 4.1 Sources

| Source | Images | Notes |
|---|---|---|
| TrashNet | 2,527 | 6 classes, clean labels |
| TACO | 15,000 | Real-world context images |
| Kaggle Waste Classification | 5,000 | High quality, balanced |
| Custom collection | 3,473 | Staged + partner recycling centers |
| **Total** | **26,000** | |

### 4.2 Class Distribution

```
Plastic:   8,000 images  (30.8%) - bottles, bags, containers, packaging
Paper:     6,500 images  (25.0%) - cardboard, newspapers, boxes
Metal:     5,000 images  (19.2%) - cans, foil, scrap
Organic:   4,500 images  (17.3%) - food waste, yard waste, compost
Glass:     2,000 images  (7.7%)  - bottles, jars
Total:    26,000 images
```

> **Note:** Electronic waste removed from MVP scope — insufficient data for reliable classification. Added in Phase 4 post-MVP expansion.

### 4.3 Train / Val / Test Split

```
Training:    80%  ->  20,800 images
Validation:  10%  ->   2,600 images
Test:        10%  ->   2,600 images
```

---

## 5. Model: Waste Classifier

### 5.1 Architecture

**Base Model:** EfficientNetB0 (pretrained on ImageNet)

**Why EfficientNetB0 over MobileNetV3:**
- Higher accuracy ceiling (77% vs 75% ImageNet top-1)
- ~20MB model size — fits comfortably in TFLite for mobile
- Sufficient speed for async Supabase Edge Function calls
- Better generalizes to real-world recycling photos with varied backgrounds

### 5.2 Full Training Script (Google Colab Pro)

```python
# Install
!pip install tensorflow albumentations scikit-learn mlflow dagshub dvc imagehash

import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import mlflow
import mlflow.tensorflow

# MLflow + DagsHub setup
import dagshub
dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)
# This sets mlflow.set_tracking_uri() to your DagsHub MLflow server automatically

mlflow.set_experiment("waste-classifier-efficientnetb0")

# Config
IMG_SIZE     = 224
BATCH_SIZE   = 32
EPOCHS_P1    = 10    # frozen base
EPOCHS_P2    = 20    # fine-tuning
NUM_CLASSES  = 5
DATASET_DIR  = "/content/drive/MyDrive/satsverdant/dataset"
MODEL_SAVE   = "/content/drive/MyDrive/satsverdant/waste_classifier.h5"
TFLITE_SAVE  = "/content/drive/MyDrive/satsverdant/waste_classifier.tflite"
RUN_NAME     = f"efficientnetb0-b{BATCH_SIZE}-ep{EPOCHS_P1}p1-ep{EPOCHS_P2}p2"

# Data Augmentation
# Critical: real recycling photos vary hugely in angle, lighting, background
train_datagen = ImageDataGenerator(
    rescale=1./255, rotation_range=40,
    width_shift_range=0.2, height_shift_range=0.2,
    shear_range=0.2, zoom_range=0.3,
    horizontal_flip=True, vertical_flip=True,
    brightness_range=[0.7, 1.3], channel_shift_range=30.0, fill_mode='nearest'
)
val_datagen = ImageDataGenerator(rescale=1./255)

train_gen = train_datagen.flow_from_directory(
    f"{DATASET_DIR}/train", target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE, class_mode='categorical'
)
val_gen = val_datagen.flow_from_directory(
    f"{DATASET_DIR}/val", target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE, class_mode='categorical'
)

# Model Architecture
base_model = EfficientNetB0(weights='imagenet', include_top=False,
                             input_shape=(IMG_SIZE, IMG_SIZE, 3))
base_model.trainable = False

inputs  = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x       = base_model(inputs, training=False)
x       = layers.GlobalAveragePooling2D()(x)
x       = layers.BatchNormalization()(x)
x       = layers.Dense(256, activation='relu')(x)
x       = layers.Dropout(0.4)(x)
outputs = layers.Dense(NUM_CLASSES, activation='softmax')(x)
model   = models.Model(inputs, outputs, name='satsverdant_waste_classifier')

# Phase 1: Train classifier head only (frozen base)
model.compile(optimizer=optimizers.Adam(learning_rate=1e-3),
              loss='categorical_crossentropy', metrics=['accuracy'])

callbacks_p1 = [
    EarlyStopping(patience=4, restore_best_weights=True),
    ReduceLROnPlateau(factor=0.5, patience=2, min_lr=1e-7),
    ModelCheckpoint(MODEL_SAVE, save_best_only=True, monitor='val_accuracy'),
    WandbCallback()
]

print("Phase 1: Frozen base training")
model.fit(train_gen, epochs=EPOCHS_P1, validation_data=val_gen, callbacks=callbacks_p1)

# Phase 2: Fine-tune top 30 layers
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(optimizer=optimizers.Adam(learning_rate=1e-5),
              loss='categorical_crossentropy', metrics=['accuracy'])

callbacks_p2 = [
    EarlyStopping(patience=6, restore_best_weights=True),
    ReduceLROnPlateau(factor=0.3, patience=3, min_lr=1e-8),
    ModelCheckpoint(MODEL_SAVE, save_best_only=True, monitor='val_accuracy'),
    WandbCallback()
]

print("Phase 2: Fine-tuning top 30 layers")
model.fit(train_gen, epochs=EPOCHS_P2, validation_data=val_gen, callbacks=callbacks_p2)

# Evaluate
val_loss, val_acc = model.evaluate(val_gen)
print(f"\nFinal Validation Accuracy: {val_acc:.2%}")
print("TARGET MET (>80%)!" if val_acc >= 0.80 else "Below 80% - iterate")
wandb.log({"final_val_accuracy": val_acc})

# Export: H5 (backend) + TFLite (mobile)
model.save(MODEL_SAVE)
print(f"H5 model saved -> {MODEL_SAVE}")

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]
tflite_model = converter.convert()

with open(TFLITE_SAVE, 'wb') as f:
    f.write(tflite_model)
print(f"TFLite model saved -> {TFLITE_SAVE}")
```

### 5.3 Expected Training Results

| Metric | Phase 1 (frozen) | Phase 2 (fine-tuned) |
|---|---|---|
| Training time (A100) | ~45 min | ~90 min |
| Val accuracy | 72-78% | **82-88%** |
| Model size (.h5) | ~20MB | ~20MB |
| TFLite size | — | ~5MB |
| Groq inference speed | — | ~50ms/image |

### 5.4 If Accuracy Falls Below 80%

Try these in order before a full retraining run:

1. Increase augmentation — raise `rotation_range` to 45, add `CoarseDropout`
2. Unfreeze more layers — change `[:-30]` to `[:-50]` in Phase 2
3. Lower learning rate — try `5e-6` for Phase 2
4. Add class weights for Glass (fewest images) via `class_weight` in `model.fit()`
5. Upgrade to EfficientNetB3 — higher accuracy ceiling, ~2x training time

---

## 6. Groq Inference Integration

Groq is used for **production inference only — not training**. Once your `.h5` model is trained, Groq's LPU delivers ~10x faster inference than a standard CPU server at near-zero cost for MVP scale.

### 6.1 Why Groq for Inference

| Option | Latency | Cost at 1K inferences/day | Notes |
|---|---|---|---|
| Self-hosted FastAPI (CPU) | ~800ms | Server cost | Complex infra |
| Hugging Face Inference API | ~300ms | Free tier limited | Good fallback |
| **Groq API** | **~50ms** | **~$0.01/day** | Best for MVP |
| AWS SageMaker | ~200ms | $$$ | Overkill for MVP |

### 6.2 Supabase Edge Function: `/classify`

```typescript
// supabase/functions/classify/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GROQ_API_KEY  = Deno.env.get("GROQ_API_KEY")!;
const RADAR_API_KEY = Deno.env.get("RADAR_API_KEY")!;
const SUPABASE_URL  = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_KEY  = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

serve(async (req) => {
  try {
    const { imageBase64, userId, latitude, longitude, deviceInfo } = await req.json();

    // Step 1: Quality Gate
    const quality = await checkImageQuality(imageBase64);
    if (quality.grade === "D") {
      return json({ success: false, reason: "Image quality too low. Please retake in better lighting." }, 400);
    }

    // Step 2: Duplicate Detection
    const imageHash   = await computeHash(imageBase64);
    const isDuplicate = await checkDuplicate(userId, imageHash);
    if (isDuplicate) {
      return json({ success: false, reason: "Duplicate submission detected." }, 409);
    }

    // Step 3: Radar.io Geofence Check
    if (latitude && longitude) {
      const geo = await verifyLocation(latitude, longitude);
      if (!geo.isAtRecyclingPoint) {
        return json({
          success: false,
          reason: "Must be at a registered recycling location.",
          nearestLocation: geo.nearestLocation
        }, 403);
      }
    }

    // Step 4: Groq Classification
    const classification = await classifyWithGroq(imageBase64);

    // Step 5: Fraud Score
    const fraudScore = await getFraudScore(userId, classification.confidence);

    // Step 6: Persist to Supabase
    const { data: submission } = await supabase
      .from("submissions")
      .insert({
        user_id: userId, waste_type: classification.wasteType,
        ai_confidence: classification.confidence, quality_grade: quality.grade,
        image_hash: imageHash, latitude, longitude,
        fraud_score: fraudScore,
        status: fraudScore > 0.5 ? "flagged" : "approved",
        device_info: deviceInfo
      })
      .select().single();

    // Step 7: Trigger reward if approved
    if (submission.status === "approved" && classification.confidence >= 0.7) {
      await supabase.from("reward_queue").insert({
        user_id: userId, waste_type: classification.wasteType,
        submission_id: submission.id, status: "pending"
      });
    }

    return json({
      success: true, submissionId: submission.id,
      wasteType: classification.wasteType, confidence: classification.confidence,
      qualityGrade: quality.grade, status: submission.status,
      rewardTriggered: submission.status === "approved"
    });

  } catch (err) {
    return json({ success: false, error: err.message }, 500);
  }
});

// Groq: Vision classification
async function classifyWithGroq(imageBase64: string) {
  const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { "Authorization": `Bearer ${GROQ_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "llama-3.2-11b-vision-preview",
      messages: [{
        role: "user",
        content: [
          { type: "image_url", image_url: { url: `data:image/jpeg;base64,${imageBase64}` } },
          { type: "text", text: `Classify this waste image. Respond ONLY with valid JSON:
{
  "wasteType": "<plastic|paper|metal|organic|glass>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence>"
}` }
        ]
      }],
      max_tokens: 150, temperature: 0.1
    })
  });
  const data = await res.json();
  const text = data.choices[0].message.content.replace(/```json|```/g, "").trim();
  return JSON.parse(text);
}

// Radar.io: Geofence verification
async function verifyLocation(lat: number, lng: number) {
  const res   = await fetch(
    `https://api.radar.io/v1/geofences/nearby?coordinates=${lat},${lng}&radius=100`,
    { headers: { "Authorization": RADAR_API_KEY } }
  );
  const data  = await res.json();
  const fences = (data.geofences ?? []).filter((f: any) => f.tag === "recycling_point");
  return { isAtRecyclingPoint: fences.length > 0, nearestLocation: fences[0]?.description ?? null };
}

// Hash: Duplicate detection
async function computeHash(imageBase64: string): Promise<string> {
  const bytes = Uint8Array.from(atob(imageBase64), c => c.charCodeAt(0));
  const hash  = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
}

async function checkDuplicate(userId: string, hash: string): Promise<boolean> {
  const { data } = await supabase
    .from("submissions").select("id").eq("user_id", userId).eq("image_hash", hash)
    .gte("created_at", new Date(Date.now() - 30*24*60*60*1000).toISOString()).limit(1);
  return (data?.length ?? 0) > 0;
}

// Fraud Score
async function getFraudScore(userId: string, confidence: number): Promise<number> {
  const { count } = await supabase
    .from("submissions").select("*", { count: "exact", head: true }).eq("user_id", userId)
    .gte("created_at", new Date(Date.now() - 60*60*1000).toISOString());
  let score = 0;
  if ((count ?? 0) >= 5) score += 0.4;
  if (confidence < 0.6)  score += 0.3;
  return Math.min(score, 1.0);
}

function json(data: object, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
}
```

---

## 7. Location Verification: Supabase PostGIS + Radar.io

### 7.1 Why Both

| Tool | Role |
|---|---|
| **Supabase PostGIS** | Store recycling point coordinates, spatial queries, "find nearest" feature |
| **Radar.io Geofencing** | Real-time verify user is physically present at a recycling point at submission time |

PostGIS manages your data layer. Radar.io handles live event verification. They are complementary, not redundant.

### 7.2 Supabase PostGIS Setup

```sql
-- Enable PostGIS (natively supported in Supabase)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Recycling locations table
CREATE TABLE recycling_locations (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT NOT NULL,
  address        TEXT,
  coordinates    GEOGRAPHY(POINT, 4326) NOT NULL,
  waste_types    TEXT[] DEFAULT '{}',
  radar_fence_id TEXT,
  is_active      BOOLEAN DEFAULT true,
  created_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_recycling_locations_geo
  ON recycling_locations USING GIST(coordinates);

-- Find recycling points within 100m of user
CREATE OR REPLACE FUNCTION nearby_recycling_points(
  user_lat FLOAT, user_lng FLOAT, radius_m INT DEFAULT 100
)
RETURNS TABLE(id UUID, name TEXT, distance_meters FLOAT) AS $$
  SELECT id, name,
    ST_Distance(coordinates, ST_MakePoint(user_lng, user_lat)::GEOGRAPHY) AS distance_meters
  FROM recycling_locations
  WHERE ST_DWithin(coordinates, ST_MakePoint(user_lng, user_lat)::GEOGRAPHY, radius_m)
    AND is_active = true
  ORDER BY distance_meters;
$$ LANGUAGE SQL;
```

### 7.3 Radar.io Geofence Registration

Each verified recycling partner is registered as a Radar.io geofence with tag `recycling_point`. The Edge Function checks at submission time that the user is inside a registered fence — your third anti-fraud layer alongside AI confidence and perceptual hashing. This is a strong differentiator for the grant committee.

---

## 8. Image Quality Grader

Runs first in the pipeline as a fast gate before any Groq API call. Saves cost on unusable images and adjusts reward multipliers for borderline submissions.

```python
# quality_grader.py
import cv2
import numpy as np

class QualityGrader:
    REWARD_MULTIPLIERS = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.0}

    def grade(self, image_bytes: bytes) -> dict:
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        gray  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness = float(np.mean(gray))
        contrast   = float(np.std(gray))

        if   blur_score >= 100 and 50 <= brightness <= 200 and contrast >= 40: grade = "A"
        elif blur_score >= 50  and 30 <= brightness <= 220 and contrast >= 25: grade = "B"
        elif blur_score >= 20  and 20 <= brightness <= 240 and contrast >= 15: grade = "C"
        else: grade = "D"

        return {
            "grade":             grade,
            "reward_multiplier": self.REWARD_MULTIPLIERS[grade],
            "blur_score":        round(blur_score, 2),
            "brightness":        round(brightness, 2),
            "contrast":          round(contrast, 2),
            "is_blurry":         blur_score < 50,
            "is_too_dark":       brightness < 30,
            "is_overexposed":    brightness > 220,
        }
```

**Grade to reward mapping:**
- Grade A (sharp, well-lit) — 1.0x token reward
- Grade B (slightly blurry) — 0.8x token reward
- Grade C (poor quality) — 0.6x token reward
- Grade D (unusable) — Rejected before ML inference runs

---

## 9. Fraud Detection System

Three independent signals. All must pass for auto-approval.

### 9.1 Signal Summary

| Signal | Method | Score Weight | Trigger |
|---|---|---|---|
| Duplicate image | Perceptual hash (64-bit) | 0.5 | Same hash within 30 days |
| Rapid submissions | Rate counter in Supabase | 0.4 | 5 or more per hour |
| Low AI confidence | Confidence score | 0.3 | Below 0.6 confidence |
| Location spoofing | Radar.io geofence | Hard block | Not inside registered fence |

### 9.2 Score to Action

```
0.0 - 0.29  ->  auto_approve    Mint token immediately
0.3 - 0.49  ->  warning         Approve, flag user for monitoring
0.5 - 0.79  ->  manual_review   Hold for validator decision
0.8 - 1.0   ->  auto_reject     No reward, user notified
```

### 9.3 Python Fraud Detector

```python
# fraud_detector.py
import imagehash
from PIL import Image
import io

class FraudDetector:
    def __init__(self, db, hash_threshold=10, rate_limit=5):
        self.db             = db
        self.hash_threshold = hash_threshold
        self.rate_limit     = rate_limit

    def perceptual_hash(self, image_bytes: bytes) -> dict:
        img = Image.open(io.BytesIO(image_bytes))
        return {
            "phash": str(imagehash.phash(img)),
            "dhash": str(imagehash.dhash(img)),
            "whash": str(imagehash.whash(img)),
        }

    def is_duplicate(self, user_id: str, hashes: dict) -> bool:
        recent = self.db.query("""
            SELECT image_hash_phash, image_hash_dhash, image_hash_whash
            FROM submissions
            WHERE user_id = %s AND created_at > NOW() - INTERVAL '30 days'
        """, (user_id,))

        for row in recent:
            distances = [
                imagehash.hex_to_hash(hashes["phash"]) - imagehash.hex_to_hash(row["image_hash_phash"]),
                imagehash.hex_to_hash(hashes["dhash"]) - imagehash.hex_to_hash(row["image_hash_dhash"]),
                imagehash.hex_to_hash(hashes["whash"]) - imagehash.hex_to_hash(row["image_hash_whash"]),
            ]
            if sum(distances) / 3 < self.hash_threshold:
                return True
        return False

    def is_rapid_submitter(self, user_id: str) -> bool:
        count = self.db.query("""
            SELECT COUNT(*) as cnt FROM submissions
            WHERE user_id = %s AND created_at > NOW() - INTERVAL '1 hour'
        """, (user_id,)).fetchone()["cnt"]
        return count >= self.rate_limit

    def score(self, user_id: str, image_bytes: bytes, confidence: float) -> dict:
        flags = []
        total = 0.0

        hashes = self.perceptual_hash(image_bytes)
        if self.is_duplicate(user_id, hashes):
            total += 0.5
            flags.append({"type": "duplicate_image", "severity": "high"})

        if self.is_rapid_submitter(user_id):
            total += 0.4
            flags.append({"type": "rapid_submission", "severity": "high"})

        if confidence < 0.6:
            total += 0.3
            flags.append({"type": "low_confidence", "severity": "medium"})

        total = min(total, 1.0)

        if   total >= 0.8: action = "auto_reject"
        elif total >= 0.5: action = "manual_review"
        elif total >= 0.3: action = "warning"
        else:              action = "auto_approve"

        return {
            "fraud_score": round(total, 3), "flags": flags,
            "recommended_action": action, "image_hashes": hashes
        }
```

---

## 10. Weight Estimation

**MVP:** Heuristic model — ships immediately, no training required.
**Post-MVP:** Regression model trained on labeled weight data from recycling partners.

```python
# weight_estimator.py
class WeightEstimator:
    BASE_WEIGHTS_KG  = {"plastic": 0.5, "paper": 1.0, "metal": 0.8, "organic": 1.5, "glass": 0.7}
    QUALITY_FACTORS  = {"A": 1.0, "B": 0.9, "C": 0.8, "D": 0.0}

    def estimate(self, waste_type: str, quality_grade: str) -> float:
        import random
        base     = self.BASE_WEIGHTS_KG.get(waste_type, 1.0)
        quality  = self.QUALITY_FACTORS[quality_grade]
        variance = random.uniform(0.85, 1.15)
        return round(base * variance * quality, 2)
```

---

## 11. TFLite On-Device Inference (React Native)

The exported TFLite model runs on the user's device for instant feedback before the Edge Function confirms the result server-side. Reduces perceived latency to near-zero.

```javascript
// WasteClassifier.ts
import * as tf from '@tensorflow/tfjs';
import '@tensorflow/tfjs-react-native';
import { bundleResourceIO } from '@tensorflow/tfjs-react-native';

const CLASS_NAMES = ['plastic', 'paper', 'metal', 'organic', 'glass'];

export class WasteClassifier {
  private model: tf.GraphModel | null = null;

  async load() {
    await tf.ready();
    const modelJSON    = require('../assets/model/model.json');
    const modelWeights = require('../assets/model/group1-shard1of1.bin');
    this.model = await tf.loadGraphModel(bundleResourceIO(modelJSON, modelWeights));
  }

  async classify(imageUri: string): Promise<{ wasteType: string; confidence: number }> {
    if (!this.model) throw new Error('Model not loaded');
    const tensor      = await this.uriToTensor(imageUri);
    const predictions = this.model.predict(tensor) as tf.Tensor;
    const probs       = await predictions.data();
    const maxIdx      = Array.from(probs).indexOf(Math.max(...Array.from(probs)));
    tf.dispose([tensor, predictions]);
    return { wasteType: CLASS_NAMES[maxIdx], confidence: probs[maxIdx] };
  }

  private async uriToTensor(uri: string): Promise<tf.Tensor4D> {
    const b64 = await fetch(uri).then(r => r.blob()).then(b =>
      new Promise<string>((res) => {
        const reader = new FileReader();
        reader.onload = () => res((reader.result as string).split(',')[1]);
        reader.readAsDataURL(b);
      })
    );
    const raw    = tf.tensor(Uint8Array.from(atob(b64), c => c.charCodeAt(0)));
    const decoded = tf.image.decodeJpeg(raw as tf.Tensor1D);
    const resized = tf.image.resizeBilinear(decoded, [224, 224]);
    const norm    = resized.div(255.0).expandDims(0) as tf.Tensor4D;
    tf.dispose([raw, decoded, resized]);
    return norm;
  }
}
```

---

## 12. Supabase Database Schema

```sql
CREATE TABLE submissions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES auth.users(id),
  waste_type      TEXT NOT NULL CHECK (waste_type IN ('plastic','paper','metal','organic','glass')),
  ai_confidence   FLOAT NOT NULL,
  quality_grade   CHAR(1) NOT NULL CHECK (quality_grade IN ('A','B','C','D')),
  estimated_kg    FLOAT,
  image_hash      TEXT,
  latitude        FLOAT,
  longitude       FLOAT,
  fraud_score     FLOAT DEFAULT 0,
  status          TEXT DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','flagged','rejected')),
  reward_amount   FLOAT,
  reward_tx_id    TEXT,
  device_info     JSONB,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE reward_queue (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES auth.users(id),
  submission_id UUID REFERENCES submissions(id),
  waste_type    TEXT NOT NULL,
  status        TEXT DEFAULT 'pending'
                  CHECK (status IN ('pending','processing','completed','failed')),
  stacks_tx_id  TEXT,
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE recycling_locations (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           TEXT NOT NULL,
  address        TEXT,
  coordinates    GEOGRAPHY(POINT, 4326) NOT NULL,
  waste_types    TEXT[] DEFAULT '{}',
  radar_fence_id TEXT,
  is_active      BOOLEAN DEFAULT true
);

CREATE INDEX idx_submissions_user   ON submissions(user_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_hash   ON submissions(image_hash);
CREATE INDEX idx_recycling_geo      ON recycling_locations USING GIST(coordinates);
```

---

## 13. Budget Allocation — AI/ML ($2,000 of $10,000 total)

| Item | Cost | Timing |
|---|---|---|
| Google Colab Pro (3 months) | $150 | Months 1-3 |
| Dataset labeling / Label Studio | $400 | Month 1 |
| MLflow + DagsHub (free tier) | $0 | Ongoing |
| Groq API — production inference | $200 | Post-launch |
| Radar.io Starter plan | $150 | Month 2 onward |
| Hugging Face Pro (model backup) | $100 | Month 2 |
| Retraining buffer (GPU compute) | $300 | Months 2-3 |
| Contingency | $700 | As needed |
| **Total** | **$2,000** | |


---

## 17. MLOps Stack: MLflow + DVC + DagsHub

### 17.1 Why This Combination

| Tool | Role | Why SatsVerdant Needs It |
|---|---|---|
| **DVC** | Dataset & pipeline versioning | 26,000 images can't live in Git. DVC tracks dataset versions so every model run is reproducible with the exact data that produced it |
| **MLflow** | Experiment tracking + model registry | Compare every training run side by side — hyperparameters, accuracy, loss curves. Promotes winning models to production |
| **DagsHub** | Remote storage + hosted MLflow server + team UI | Free hosting for both DVC remote storage and MLflow tracking server. The grant committee can view your experiment history as a public URL |

**Grant application value:** This stack gives the Stacks Endowment committee a live, public URL showing every training run, dataset version, and model artifact — stronger evidence than a screenshot.

---

### 17.2 DagsHub Project Setup

```bash
# 1. Create free account at https://dagshub.com
# 2. Create new repo: satsverdant/satsverdant-ml
# 3. Install tools
pip install dagshub dvc mlflow dvc-s3

# 4. Clone your DagsHub repo
git clone https://dagshub.com/satsverdant/satsverdant-ml.git
cd satsverdant-ml

# 5. Initialize DVC
dvc init

# 6. Set DagsHub as DVC remote (free 10GB storage)
dvc remote add origin https://dagshub.com/satsverdant/satsverdant-ml.dvc
dvc remote modify origin --local auth basic
dvc remote modify origin --local user YOUR_DAGSHUB_USERNAME
dvc remote modify origin --local password YOUR_DAGSHUB_TOKEN
dvc remote default origin

# 7. Configure MLflow to use DagsHub tracking server
# (dagshub.init() does this automatically in Colab -- see training script)
```

---

### 17.3 DVC: Dataset Versioning

DVC tracks your 26,000-image dataset like Git tracks code. Every training run references an exact dataset commit — making results fully reproducible.

#### Directory Structure

```
satsverdant-ml/
├── data/
│   ├── raw/                  <- Original downloaded images (DVC-tracked)
│   │   ├── trashnet/
│   │   ├── taco/
│   │   ├── kaggle/
│   │   └── custom/
│   └── processed/            <- Train/val/test splits (DVC-tracked)
│       ├── train/
│       │   ├── plastic/
│       │   ├── paper/
│       │   ├── metal/
│       │   ├── organic/
│       │   └── glass/
│       ├── val/
│       └── test/
├── models/                   <- Trained model artifacts (DVC-tracked)
│   ├── waste_classifier.h5
│   └── waste_classifier.tflite
├── src/
│   ├── prepare_data.py
│   ├── train.py
│   └── evaluate.py
├── dvc.yaml                  <- Pipeline definition
├── dvc.lock                  <- Locked pipeline state (commit this)
├── params.yaml               <- Hyperparameters (tracked by DVC)
└── .dvc/
    └── config                <- Remote storage config
```

#### params.yaml — All Hyperparameters in One File

```yaml
# params.yaml -- tracked by DVC, referenced by MLflow
prepare:
  img_size: 224
  train_split: 0.80
  val_split: 0.10
  test_split: 0.10
  random_seed: 42

train:
  base_model: EfficientNetB0
  batch_size: 32
  epochs_phase1: 10
  epochs_phase2: 20
  lr_phase1: 0.001
  lr_phase2: 0.00001
  dropout: 0.4
  fine_tune_layers: 30
  num_classes: 5
  confidence_threshold: 0.70

augmentation:
  rotation_range: 40
  zoom_range: 0.3
  brightness_min: 0.7
  brightness_max: 1.3
  horizontal_flip: true
  vertical_flip: true

fraud:
  hash_threshold: 10
  rate_limit_per_hour: 5
  min_confidence: 0.6
```

#### dvc.yaml — Reproducible Pipeline

```yaml
# dvc.yaml -- defines the full ML pipeline as reproducible stages
stages:

  prepare:
    cmd: python src/prepare_data.py
    deps:
      - src/prepare_data.py
      - data/raw/
    params:
      - prepare
    outs:
      - data/processed/

  train:
    cmd: python src/train.py
    deps:
      - src/train.py
      - data/processed/
    params:
      - train
      - augmentation
    outs:
      - models/waste_classifier.h5
      - models/waste_classifier.tflite
    metrics:
      - metrics/train_metrics.json:
          cache: false

  evaluate:
    cmd: python src/evaluate.py
    deps:
      - src/evaluate.py
      - models/waste_classifier.h5
      - data/processed/test/
    metrics:
      - metrics/eval_metrics.json:
          cache: false
    plots:
      - metrics/confusion_matrix.csv:
          cache: false
      - metrics/per_class_metrics.csv:
          cache: false
```

#### Core DVC Commands

```bash
# Add dataset to DVC tracking (removes from Git, tracks with DVC)
dvc add data/raw/
git add data/raw/.gitignore data/raw.dvc
git commit -m "Add raw dataset v1 (26k images)"
dvc push  # Uploads to DagsHub remote storage

# Run full pipeline reproducibly
dvc repro

# Check what has changed since last run
dvc status

# Compare metrics between runs
dvc metrics diff HEAD~1

# Switch to a previous dataset version
git checkout v1.0
dvc checkout  # Restores the exact dataset for that commit

# View pipeline DAG
dvc dag
```

---

### 17.4 MLflow: Experiment Tracking & Model Registry

#### Complete Training Script with MLflow (Colab-ready)

```python
# src/train.py -- Full MLflow + DagsHub integration
import os
import yaml
import json
import subprocess
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix
import mlflow
import mlflow.tensorflow
import dagshub

# ── DagsHub + MLflow Init ────────────────────────────────────────────
dagshub.init(
    repo_owner="satsverdant",
    repo_name="satsverdant-ml",
    mlflow=True  # Sets mlflow tracking URI to DagsHub server automatically
)

# ── Load params from DVC params.yaml ────────────────────────────────
with open("params.yaml") as f:
    params = yaml.safe_load(f)

TRAIN_P  = params["train"]
AUG_P    = params["augmentation"]
PREP_P   = params["prepare"]

IMG_SIZE    = PREP_P["img_size"]
BATCH_SIZE  = TRAIN_P["batch_size"]
NUM_CLASSES = TRAIN_P["num_classes"]
DATASET_DIR = "data/processed"
MODEL_H5    = "models/waste_classifier.h5"
MODEL_TFLITE= "models/waste_classifier.tflite"
CLASS_NAMES = ["plastic", "paper", "metal", "organic", "glass"]

os.makedirs("models", exist_ok=True)
os.makedirs("metrics", exist_ok=True)

mlflow.set_experiment("waste-classifier-efficientnetb0")

with mlflow.start_run(run_name=f"effnetb0-bs{BATCH_SIZE}-p1ep{TRAIN_P['epochs_phase1']}") as run:

    # ── Log all params from params.yaml ─────────────────────────────
    mlflow.log_params({
        "base_model":         TRAIN_P["base_model"],
        "img_size":           IMG_SIZE,
        "batch_size":         BATCH_SIZE,
        "epochs_phase1":      TRAIN_P["epochs_phase1"],
        "epochs_phase2":      TRAIN_P["epochs_phase2"],
        "lr_phase1":          TRAIN_P["lr_phase1"],
        "lr_phase2":          TRAIN_P["lr_phase2"],
        "dropout":            TRAIN_P["dropout"],
        "fine_tune_layers":   TRAIN_P["fine_tune_layers"],
        "dataset_size":       26000,
        "dataset_version":    _get_dvc_hash(),
    })

    # ── Data Generators ──────────────────────────────────────────────
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=AUG_P["rotation_range"],
        zoom_range=AUG_P["zoom_range"],
        brightness_range=[AUG_P["brightness_min"], AUG_P["brightness_max"]],
        horizontal_flip=AUG_P["horizontal_flip"],
        vertical_flip=AUG_P["vertical_flip"],
        fill_mode="nearest"
    )
    val_datagen = ImageDataGenerator(rescale=1./255)

    train_gen = train_datagen.flow_from_directory(
        f"{DATASET_DIR}/train",
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE, class_mode="categorical"
    )
    val_gen = val_datagen.flow_from_directory(
        f"{DATASET_DIR}/val",
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE, class_mode="categorical"
    )
    test_gen = val_datagen.flow_from_directory(
        f"{DATASET_DIR}/test",
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE, class_mode="categorical",
        shuffle=False
    )

    # ── Model ────────────────────────────────────────────────────────
    base   = EfficientNetB0(weights="imagenet", include_top=False,
                            input_shape=(IMG_SIZE, IMG_SIZE, 3))
    base.trainable = False
    x      = layers.GlobalAveragePooling2D()(base.output)
    x      = layers.BatchNormalization()(x)
    x      = layers.Dense(256, activation="relu")(x)
    x      = layers.Dropout(TRAIN_P["dropout"])(x)
    out    = layers.Dense(NUM_CLASSES, activation="softmax")(x)
    model  = models.Model(base.input, out)

    # ── Phase 1: Train head ──────────────────────────────────────────
    model.compile(optimizer=optimizers.Adam(TRAIN_P["lr_phase1"]),
                  loss="categorical_crossentropy", metrics=["accuracy"])

    h1 = model.fit(train_gen, epochs=TRAIN_P["epochs_phase1"],
                   validation_data=val_gen,
                   callbacks=[
                       EarlyStopping(patience=4, restore_best_weights=True),
                       ReduceLROnPlateau(factor=0.5, patience=2),
                       ModelCheckpoint(MODEL_H5, save_best_only=True, monitor="val_accuracy"),
                   ])

    # Log Phase 1 metrics per epoch
    for i, (tl, ta, vl, va) in enumerate(zip(
        h1.history["loss"], h1.history["accuracy"],
        h1.history["val_loss"], h1.history["val_accuracy"]
    )):
        mlflow.log_metrics(
            {"p1_loss": tl, "p1_acc": ta, "p1_val_loss": vl, "p1_val_acc": va},
            step=i
        )

    # ── Phase 2: Fine-tune ───────────────────────────────────────────
    base.trainable = True
    for layer in base.layers[:-TRAIN_P["fine_tune_layers"]]:
        layer.trainable = False

    model.compile(optimizer=optimizers.Adam(TRAIN_P["lr_phase2"]),
                  loss="categorical_crossentropy", metrics=["accuracy"])

    h2 = model.fit(train_gen, epochs=TRAIN_P["epochs_phase2"],
                   validation_data=val_gen,
                   callbacks=[
                       EarlyStopping(patience=6, restore_best_weights=True),
                       ReduceLROnPlateau(factor=0.3, patience=3),
                       ModelCheckpoint(MODEL_H5, save_best_only=True, monitor="val_accuracy"),
                   ])

    for i, (tl, ta, vl, va) in enumerate(zip(
        h2.history["loss"], h2.history["accuracy"],
        h2.history["val_loss"], h2.history["val_accuracy"]
    )):
        mlflow.log_metrics(
            {"p2_loss": tl, "p2_acc": ta, "p2_val_loss": vl, "p2_val_acc": va},
            step=i
        )

    # ── Evaluate on test set ─────────────────────────────────────────
    model.load_weights(MODEL_H5)
    test_loss, test_acc = model.evaluate(test_gen)

    y_true = test_gen.classes
    y_pred = np.argmax(model.predict(test_gen), axis=1)

    report = classification_report(y_true, y_pred,
                                   target_names=CLASS_NAMES,
                                   output_dict=True)
    cm = confusion_matrix(y_true, y_pred).tolist()

    # Log final metrics
    mlflow.log_metrics({
        "test_accuracy":   test_acc,
        "test_loss":       test_loss,
        "test_precision":  report["weighted avg"]["precision"],
        "test_recall":     report["weighted avg"]["recall"],
        "test_f1":         report["weighted avg"]["f1-score"],
        "target_met":      int(test_acc >= 0.80),
    })

    # Log per-class metrics
    for cls in CLASS_NAMES:
        mlflow.log_metrics({
            f"{cls}_precision": report[cls]["precision"],
            f"{cls}_recall":    report[cls]["recall"],
            f"{cls}_f1":        report[cls]["f1-score"],
        })

    # Save metrics for DVC tracking
    metrics_out = {
        "test_accuracy": test_acc, "test_loss": test_loss,
        "test_f1": report["weighted avg"]["f1-score"],
        "target_met": test_acc >= 0.80
    }
    with open("metrics/train_metrics.json", "w") as f:
        json.dump(metrics_out, f, indent=2)

    # Save confusion matrix for DVC plots
    import csv
    with open("metrics/confusion_matrix.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["actual", "predicted", "count"])
        for i, row in enumerate(cm):
            for j, count in enumerate(row):
                writer.writerow([CLASS_NAMES[i], CLASS_NAMES[j], count])

    # ── Export models ────────────────────────────────────────────────
    model.save(MODEL_H5)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    with open(MODEL_TFLITE, "wb") as f:
        f.write(converter.convert())

    # ── Log artifacts to MLflow / DagsHub ───────────────────────────
    mlflow.log_artifact(MODEL_H5,     artifact_path="models")
    mlflow.log_artifact(MODEL_TFLITE, artifact_path="models")
    mlflow.log_artifact("params.yaml")
    mlflow.log_artifact("metrics/confusion_matrix.csv", artifact_path="plots")

    # ── Register in MLflow Model Registry ───────────────────────────
    model_uri = f"runs:/{run.info.run_id}/models/waste_classifier.h5"
    mv = mlflow.register_model(model_uri, "satsverdant-waste-classifier")

    # Promote to Staging if target accuracy met
    if test_acc >= 0.80:
        client = mlflow.MlflowClient()
        client.transition_model_version_stage(
            name="satsverdant-waste-classifier",
            version=mv.version,
            stage="Staging"
        )
        print(f"Model v{mv.version} promoted to Staging")

    print(f"\n=== Final Results ===")
    print(f"Test Accuracy: {test_acc:.2%}")
    print(f"Target Met:    {'YES' if test_acc >= 0.80 else 'NO -- iterate'}")
    print(f"MLflow Run:    {run.info.run_id}")
    print(f"DagsHub URL:   https://dagshub.com/satsverdant/satsverdant-ml/mlflow")


def _get_dvc_hash() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True)
        return r.stdout.strip()
    except Exception:
        return "unknown"
```

---

### 17.5 MLflow Model Registry Workflow

Once models are registered on DagsHub, the promotion workflow is:

```
Training Run
    |
    v
MLflow Run (logged on DagsHub)
    |
    v
Model Registry: satsverdant-waste-classifier
    |
    +-- Version 1 (None stage) -- first run
    |
    +-- Version 2 (Staging)    -- meets 80% target
    |
    +-- Version 3 (Production) -- validated by team, deployed to Groq
```

#### Querying the Registry Programmatically

```python
import mlflow
import dagshub

dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)

client = mlflow.MlflowClient()

# Get current Production model
prod_versions = client.get_latest_versions(
    "satsverdant-waste-classifier", stages=["Production"]
)
if prod_versions:
    prod = prod_versions[0]
    print(f"Production model: v{prod.version}")
    print(f"Run ID: {prod.run_id}")
    print(f"Accuracy: {client.get_run(prod.run_id).data.metrics['test_accuracy']:.2%}")

# Compare all runs in experiment
experiment = mlflow.get_experiment_by_name("waste-classifier-efficientnetb0")
runs = mlflow.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.test_accuracy DESC"]
)
print(runs[["run_id", "metrics.test_accuracy", "params.epochs_phase2", "params.lr_phase2"]].head())
```

---

### 17.6 DagsHub Dashboard

Everything is visible at:
`https://dagshub.com/satsverdant/satsverdant-ml`

| Tab | What You See |
|---|---|
| **Experiments** | Every MLflow run — hyperparams, accuracy, loss curves side by side |
| **Models** | MLflow Model Registry — versions, stages (None/Staging/Production) |
| **Data** | DVC-tracked dataset versions — what data each model was trained on |
| **Files** | Code, params.yaml, metrics JSON, confusion matrix plots |
| **Compare** | Side-by-side diff of any two runs — instantly see if a change helped |

This URL is shareable with the Stacks Endowment grant committee as direct evidence of your Model Evaluation Report deliverable.

---

### 17.7 DVC + MLflow Integration: Full Reproducibility

Any team member (or grant reviewer) can reproduce any training run exactly:

```bash
# Clone the repo
git clone https://dagshub.com/satsverdant/satsverdant-ml.git
cd satsverdant-ml

# Restore the exact dataset used for a specific run
git checkout <commit-sha>
dvc pull  # Downloads exact dataset version from DagsHub storage

# Re-run the exact pipeline
dvc repro

# Compare with the original MLflow run
mlflow ui  # Or view on DagsHub
```

---

### 17.8 Updated Install for Colab

```python
# Cell 1: Install all dependencies
!pip install tensorflow albumentations scikit-learn \
            mlflow dagshub dvc imagehash \
            pyyaml

# Cell 2: Authenticate DagsHub
import dagshub
dagshub.auth.add_app_token(token="YOUR_DAGSHUB_TOKEN")
# Or set env var: os.environ["DAGSHUB_TOKEN"] = "..."

# Cell 3: Pull dataset from DagsHub DVC remote
!dvc pull data/processed/  # Downloads 26k images to Colab
```

---

### 17.9 Week 5 DVC Setup Checklist

Runs in parallel with dataset preparation:

- [ ] Create DagsHub account and repo (`satsverdant/satsverdant-ml`)
- [ ] Initialize DVC in the repo (`dvc init`)
- [ ] Configure DagsHub as DVC remote storage
- [ ] Add raw dataset folders to DVC (`dvc add data/raw/`)
- [ ] Create `params.yaml` with all hyperparameters
- [ ] Create `dvc.yaml` pipeline stages (prepare, train, evaluate)
- [ ] First `dvc push` — uploads dataset to DagsHub storage
- [ ] Verify MLflow tracking works with `dagshub.init()`
- [ ] Make DagsHub repo public (grant committee access)

---

## 14. Success Criteria

### Model Performance
- [ ] Waste classification accuracy >= 80% on holdout test set
- [ ] Per-class precision/recall >= 75%
- [ ] Groq inference latency < 200ms per image
- [ ] TFLite on-device inference < 100ms

### Fraud Detection
- [ ] Duplicate detection accuracy >= 95%
- [ ] False positive rate < 5%
- [ ] Radar.io geofence live with >= 3 registered recycling partners

### System Performance
- [ ] Edge Function p95 response time < 2 seconds end-to-end
- [ ] Supports 1,000 inferences/day at MVP scale
- [ ] Zero critical security incidents in first 30 days

### Data Quality
- [ ] 26,000 images with verified labels
- [ ] Class balance within +/-30%
- [ ] Inter-annotator agreement >= 85%

### MLOps
- [ ] DagsHub repo live and public (grant committee can view)
- [ ] All training runs logged to MLflow on DagsHub
- [ ] Dataset versioned with DVC and pushed to DagsHub remote
- [ ] Winning model registered in MLflow Model Registry at Staging or Production stage
- [ ] `dvc repro` reproduces training pipeline from scratch
- [ ] params.yaml captures all hyperparameters used in grant deliverable

---

## 15. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Accuracy below 80% after training | Grant deliverable miss | 3 training runs budgeted; fallback to EfficientNetB3 |
| Groq API rate limits at scale | Inference bottleneck | Hugging Face Inference API as hot fallback |
| Radar.io geofence false rejections | User frustration | 100m radius (generous), manual appeal flow |
| Supabase Edge Function cold starts | Latency spikes | Keep-warm pings every 5 minutes via cron |
| Real-world photos differ from training data | Accuracy drops post-launch | Active learning: validator-confirmed submissions feed back into monthly retraining |
| DVC remote storage full (10GB free tier) | Dataset push fails | Compress images to JPEG 85% quality before DVC add; 26k images ~8GB compressed |

---

## 16. 8-Week Delivery Timeline

### Week 5 — Data Pipeline & MLOps Setup
- [ ] Create DagsHub repo (satsverdant/satsverdant-ml), make it public
- [ ] Initialize DVC, configure DagsHub as remote storage
- [ ] Download and organize all 26,000 images into train/val/test splits
- [ ] Run quality review pass in Label Studio
- [ ] Add dataset to DVC (`dvc add data/processed/`) and push to DagsHub
- [ ] Create params.yaml with all hyperparameters
- [ ] Create dvc.yaml pipeline (prepare, train, evaluate stages)
- [ ] Enable PostGIS on Supabase, create full schema
- [ ] Verify MLflow tracking works via `dagshub.init()`

### Week 6 — Model Training
- [ ] Run `dvc repro` to execute full pipeline on Colab A100
- [ ] Phase 1 (frozen) + Phase 2 (fine-tune) — all metrics auto-logged to MLflow
- [ ] Evaluate — confirm >=80% accuracy on test set
- [ ] Export H5 (backend) + TFLite (mobile) models
- [ ] Register model in MLflow Model Registry, promote to Staging if target met
- [ ] Log confusion matrix + per-class metrics as DVC plots
- [ ] Share DagsHub experiment URL as grant evidence

### Week 7 — Integration
- [ ] Deploy Supabase Edge Function /classify
- [ ] Integrate Groq API for inference
- [ ] Integrate Radar.io geofencing (register first 3 recycling partners)
- [ ] Connect fraud detection pipeline end-to-end
- [ ] Wire reward_queue to Clarity contract worker

### Week 8 — Testing & Documentation
- [ ] Full end-to-end tests: photo -> classification -> reward trigger
- [ ] Model Evaluation Report (grant deliverable evidence) — use DagsHub experiment URL
- [ ] Verify `dvc repro` reproduces training from scratch (reproducibility proof)
- [ ] Promote winning model to Production stage in MLflow Model Registry
- [ ] Load test: 100 concurrent submissions
- [ ] Publish reproducible Colab notebook to GitHub
- [ ] Document Groq + Radar.io integration for grant committee review
- [ ] Share DagsHub public repo link as Model Evaluation Report evidence

---

*SatsVerdant AI/ML PRD v2.1 — March 2026. Adds MLflow + DVC + DagsHub MLOps stack. Supersedes v2.0.*