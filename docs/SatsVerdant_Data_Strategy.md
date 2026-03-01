# SatsVerdant Data Acquisition Strategy - MVP Cold Start

## Problem Statement

**Challenge:** We need 15,000+ labeled waste images to train our classifier, but we have zero data and zero users.

**Solution:** Multi-phase approach starting with public datasets + synthetic data, then bootstrapping with real user data.

---

## Phase 1: Cold Start with Public Data (Week 1-2)

### **1.1 Public Datasets Available NOW**

#### **TrashNet Dataset**
- **Source:** https://github.com/garythung/trashnet
- **Size:** 2,527 images
- **Classes:** Glass, paper, cardboard, plastic, metal, trash
- **Format:** 512x384 images
- **License:** MIT (free to use)
- **Download:**
```bash
git clone https://github.com/garythung/trashnet.git
cd trashnet/data
# Images in: glass/, paper/, cardboard/, plastic/, metal/, trash/
```

**Pros:** Ready to use, good quality, diverse items  
**Cons:** Only 2.5K images, includes "glass" (we don't have), missing "organic"

#### **TACO (Trash Annotations in Context)**
- **Source:** http://tacodataset.org/
- **Size:** 15,000+ images with 60 categories
- **Classes:** Includes plastic, paper, metal, organic waste
- **Format:** COCO format annotations
- **License:** CC BY 4.0
- **Download:**
```bash
# Install TACO toolkit
pip install taco

# Download dataset
python download.py
```

**Pros:** Large dataset, real-world images, detailed annotations  
**Cons:** Need to remap 60 categories to our 5 categories

#### **Waste Classification Data (Kaggle)**
- **Source:** https://www.kaggle.com/datasets/techsash/waste-classification-data
- **Size:** 25,000+ images
- **Classes:** Organic, recyclable (mapped to our categories)
- **Format:** Pre-organized folders
- **License:** CC0 (public domain)
- **Download:**
```bash
kaggle datasets download -d techsash/waste-classification-data
unzip waste-classification-data.zip
```

**Pros:** Large dataset, free to use, organized  
**Cons:** Only 2 main categories (need subdivision)

#### **OpenImages Subset**
- **Source:** https://storage.googleapis.com/openimages/web/index.html
- **Size:** 9M images total, ~50K waste-related
- **Classes:** Search for specific items
- **Download Tool:** https://github.com/openimages/dataset
```bash
# Download specific classes
python downloader.py --classes "Plastic bottle,Cardboard,Aluminum can" \
  --type_csv train --limit 5000
```

**Pros:** Huge dataset, diverse, high quality  
**Cons:** Need to search and filter, time-consuming

### **1.2 Dataset Remapping Strategy**

**Map public datasets to our 5 categories:**

```python
# dataset_mapper.py
import shutil
import os
from pathlib import Path

class DatasetRemapper:
    def __init__(self):
        # Mapping rules for different datasets
        self.trashnet_mapping = {
            'plastic': 'plastic',
            'metal': 'metal',
            'paper': 'paper',
            'cardboard': 'paper',  # Combine with paper
            'glass': None,  # Skip - not in our taxonomy
            'trash': None   # Skip - mixed waste
        }
        
        self.taco_mapping = {
            # Map TACO's 60 categories to our 5
            'Plastic bottle': 'plastic',
            'Plastic bag & wrapper': 'plastic',
            'Plastic container': 'plastic',
            'Plastic straw': 'plastic',
            'Plastic utensils': 'plastic',
            'Styrofoam piece': 'plastic',
            
            'Cardboard': 'paper',
            'Paper': 'paper',
            'Paper bag': 'paper',
            'Magazine paper': 'paper',
            'Paperboard': 'paper',
            
            'Aluminium foil': 'metal',
            'Aluminium blister pack': 'metal',
            'Metal bottle cap': 'metal',
            'Metal lid': 'metal',
            'Can': 'metal',
            'Pop tab': 'metal',
            
            'Food waste': 'organic',
            'Leaves': 'organic',
            'Food Can': 'metal',
            
            'Battery': 'electronic',
            'Cigarette': None  # Skip
            # ... (add more mappings)
        }
    
    def remap_trashnet(self, source_dir, output_dir):
        """Remap TrashNet to our category structure"""
        for old_category, new_category in self.trashnet_mapping.items():
            if new_category is None:
                continue
            
            source_path = Path(source_dir) / old_category
            dest_path = Path(output_dir) / new_category
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Copy images
            for img in source_path.glob('*.jpg'):
                shutil.copy(img, dest_path / f"trashnet_{old_category}_{img.name}")
            
            print(f"Mapped {old_category} -> {new_category}: {len(list(source_path.glob('*.jpg')))} images")
    
    def remap_taco(self, annotations_file, images_dir, output_dir):
        """Remap TACO dataset"""
        import json
        
        with open(annotations_file) as f:
            data = json.load(f)
        
        # Map category IDs to names
        category_map = {cat['id']: cat['name'] for cat in data['categories']}
        
        for annotation in data['annotations']:
            category_name = category_map.get(annotation['category_id'])
            new_category = self.taco_mapping.get(category_name)
            
            if new_category is None:
                continue
            
            image_id = annotation['image_id']
            # Find image file and copy
            # ... (implementation details)
    
    def create_unified_dataset(self, output_dir='data/unified'):
        """Create unified dataset from all sources"""
        print("Creating unified dataset...")
        
        # 1. Remap TrashNet
        self.remap_trashnet('data/trashnet', output_dir)
        
        # 2. Remap TACO
        self.remap_taco('data/taco/annotations.json', 'data/taco/images', output_dir)
        
        # 3. Copy Kaggle dataset
        # ... (implementation)
        
        # Count final dataset
        for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
            cat_path = Path(output_dir) / category
            count = len(list(cat_path.glob('*.jpg')))
            print(f"{category}: {count} images")

# Usage
mapper = DatasetRemapper()
mapper.create_unified_dataset('data/unified')
```

**Expected Results After Remapping:**
```
plastic:     ~8,000 images (from TrashNet, TACO, Kaggle, OpenImages)
paper:       ~6,000 images (TrashNet cardboard, TACO paper, Kaggle)
metal:       ~4,000 images (TACO cans, OpenImages)
organic:     ~3,000 images (Kaggle organic, TACO food waste)
electronic:  ~500 images (TACO batteries, need augmentation)

TOTAL:       ~21,500 images ✅ (exceeds 15K minimum!)
```

---

## Phase 2: Synthetic Data Generation (Week 2)

Since **electronic waste** data is sparse, generate synthetic images:

### **2.1 Background Replacement**

```python
from PIL import Image
import numpy as np
import cv2

class SyntheticDataGenerator:
    def __init__(self, background_dir='backgrounds/'):
        self.backgrounds = list(Path(background_dir).glob('*.jpg'))
    
    def remove_background(self, image):
        """Remove background using GrabCut or U2-Net"""
        # Simple version: use rembg library
        from rembg import remove
        return remove(image)
    
    def composite_on_background(self, foreground, background):
        """Place foreground object on new background"""
        # Resize foreground
        fg = Image.open(foreground).convert('RGBA')
        bg = Image.open(background).convert('RGBA')
        
        # Remove background from foreground
        fg_no_bg = self.remove_background(fg)
        
        # Random placement
        x = np.random.randint(0, bg.width - fg.width)
        y = np.random.randint(0, bg.height - fg.height)
        
        # Composite
        bg.paste(fg_no_bg, (x, y), fg_no_bg)
        return bg.convert('RGB')
    
    def generate_variants(self, image_path, num_variants=10):
        """Generate multiple synthetic variants"""
        variants = []
        for i in range(num_variants):
            bg = np.random.choice(self.backgrounds)
            variant = self.composite_on_background(image_path, bg)
            variants.append(variant)
        return variants

# Usage: Expand 500 electronic images → 5,000 images
generator = SyntheticDataGenerator()
for img in Path('data/unified/electronic').glob('*.jpg'):
    variants = generator.generate_variants(img, num_variants=9)
    for idx, variant in enumerate(variants):
        variant.save(f'data/unified/electronic/{img.stem}_syn_{idx}.jpg')
```

### **2.2 3D Rendering (Advanced - Optional)**

Use Blender Python API to render 3D models:
```python
# Generate synthetic electronic waste using free 3D models
# Source: https://www.thingiverse.com/ or https://free3d.com/
```

---

## Phase 3: MVP Launch with Transfer Learning (Week 3)

### **3.1 Train Initial Model**

**Strategy:** Use combined public dataset (~21K images) to train initial model

```python
# Use the unified dataset
model = create_waste_classifier()

# Train on public data
model.fit(
    public_dataset_train,  # ~21K images
    validation_data=public_dataset_val,
    epochs=20
)

# Evaluate
test_accuracy = model.evaluate(public_dataset_test)
print(f"Test Accuracy: {test_accuracy:.2%}")
# Expected: 75-80% (good enough for MVP with high threshold)
```

**MVP Deployment Strategy:**
```python
# Start conservative
CONFIDENCE_THRESHOLD = 0.8  # Only accept high-confidence predictions
MANUAL_REVIEW_THRESHOLD = 0.7  # Human validation for medium confidence

if confidence >= 0.8:
    status = "approved_auto"
elif confidence >= 0.7:
    status = "pending_manual_review"
else:
    status = "rejected_low_confidence"
```

---

## Phase 4: Bootstrap with Real User Data (Week 4+)

### **4.1 Controlled Beta Launch**

**Invite 20-30 beta testers:**
- Friends & family
- Recycling enthusiasts
- Environmental organizations
- Crypto community members

**Beta Tester Instructions:**
```markdown
# SatsVerdant Beta Testing

Welcome! Help us improve our AI by submitting diverse waste photos:

**What to photograph:**
✅ Clear, well-lit images
✅ Single waste items or small groups
✅ Various angles and backgrounds
✅ Different lighting conditions

**What NOT to photograph:**
❌ Blurry images
❌ Poor lighting
❌ Mixed waste piles
❌ Non-waste items

**Goal:** 10 submissions per tester × 30 testers = 300 real-world images!
```

### **4.2 Active Learning Pipeline**

```python
class ActiveLearningCollector:
    def __init__(self, model):
        self.model = model
    
    def identify_valuable_samples(self, submissions):
        """Find submissions most valuable for retraining"""
        valuable = []
        
        for sub in submissions:
            prediction = self.model.predict(sub.image)
            confidence = np.max(prediction)
            
            # High value samples:
            # 1. Low confidence (uncertain)
            # 2. Close top-2 predictions (ambiguous)
            # 3. Rare categories (electronic)
            
            if confidence < 0.75:
                valuable.append({
                    'submission': sub,
                    'reason': 'low_confidence',
                    'priority': 1 - confidence
                })
            
            top_2 = np.sort(prediction)[-2:]
            if top_2[1] - top_2[0] < 0.15:  # Close call
                valuable.append({
                    'submission': sub,
                    'reason': 'ambiguous',
                    'priority': 0.15 - (top_2[1] - top_2[0])
                })
        
        # Sort by priority
        return sorted(valuable, key=lambda x: x['priority'], reverse=True)
    
    def request_human_labels(self, valuable_samples, num_samples=50):
        """Send to human validators for labeling"""
        # Send top N uncertain samples to validator queue
        # Validators label these while doing normal validation
        pass

# Weekly active learning
collector = ActiveLearningCollector(model)
uncertain = collector.identify_valuable_samples(last_week_submissions)
collector.request_human_labels(uncertain[:50])
```

### **4.3 Validator as Labelers**

**Dual Purpose:** Validators not only approve/reject, but also provide training data

```python
# When validator reviews submission
class ValidatorReview:
    def __init__(self, submission, validator):
        self.submission = submission
        self.validator = validator
    
    def review(self, decision, corrected_label=None):
        # 1. Update submission status
        self.submission.status = decision
        
        # 2. Collect as training data
        if corrected_label:
            # AI was wrong - valuable training sample!
            training_data.add({
                'image': self.submission.image,
                'true_label': corrected_label,
                'ai_predicted': self.submission.ai_waste_type,
                'confidence': self.submission.ai_confidence,
                'source': 'validator_correction'
            })
```

**Expected Growth:**
```
Month 1: 300 beta images + 2,500 public = 2,800 images (retrain weekly)
Month 2: 1,000 user images + 2,500 public = 3,500 images
Month 3: 3,000 user images + 2,500 public = 5,500 images
Month 6: 10,000+ user images (can reduce reliance on public data)
```

---

## Phase 5: Continuous Improvement (Ongoing)

### **5.1 Monthly Retraining Schedule**

```python
# retrain_pipeline.py
class RetrainingPipeline:
    def __init__(self):
        self.base_model_path = 'models/waste_classifier_v1.h5'
        self.public_data_dir = 'data/unified'
        self.user_data_dir = 'data/user_validated'
    
    def collect_new_data(self):
        """Collect validated user submissions from last month"""
        new_data = db.query("""
            SELECT image_ipfs_cid, ai_waste_type, validator_id
            FROM submissions
            WHERE status = 'approved'
              AND created_at > NOW() - INTERVAL '30 days'
              AND validation_notes IS NOT NULL
        """)
        
        # Download from IPFS and save locally
        for data in new_data:
            download_from_ipfs(data.image_ipfs_cid, self.user_data_dir)
        
        return len(new_data)
    
    def retrain_model(self):
        """Retrain with combined dataset"""
        # Combine public + user data
        combined_dataset = create_dataset([
            self.public_data_dir,
            self.user_data_dir
        ])
        
        # Load current model
        model = load_model(self.base_model_path)
        
        # Continue training (fine-tuning)
        model.fit(
            combined_dataset,
            epochs=5,  # Fewer epochs since starting from good checkpoint
            callbacks=[EarlyStopping(patience=2)]
        )
        
        # Evaluate
        test_acc = model.evaluate(test_dataset)
        
        # Deploy if improved
        if test_acc > current_prod_accuracy + 0.02:  # 2% improvement threshold
            model.save(f'models/waste_classifier_v{version}.h5')
            deploy_to_production()
            print(f"Deployed v{version} with {test_acc:.2%} accuracy")
        else:
            print(f"No improvement. Keeping current model.")

# Run monthly
pipeline = RetrainingPipeline()
new_samples = pipeline.collect_new_data()
print(f"Collected {new_samples} new samples")
pipeline.retrain_model()
```

### **5.2 Dataset Quality Monitoring**

```python
class DatasetQualityMonitor:
    def check_class_balance(self, dataset_dir):
        """Ensure classes are balanced"""
        counts = {}
        for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
            counts[category] = len(list(Path(dataset_dir, category).glob('*.jpg')))
        
        # Check if any class < 20% of largest class
        max_count = max(counts.values())
        for cat, count in counts.items():
            if count < max_count * 0.2:
                print(f"WARNING: {cat} underrepresented ({count} vs {max_count})")
                # Trigger: collect more data for this category
    
    def check_label_quality(self):
        """Check inter-validator agreement"""
        # For samples reviewed by multiple validators
        multi_reviewed = db.query("""
            SELECT submission_id, COUNT(DISTINCT validator_decision) as disagreements
            FROM validation_reviews
            GROUP BY submission_id
            HAVING COUNT(*) > 1
        """)
        
        disagreement_rate = multi_reviewed.count() / total_samples
        if disagreement_rate > 0.1:
            print(f"WARNING: High disagreement rate ({disagreement_rate:.1%})")
            # Trigger: validator training needed
```

---

## Phase 6: Long-Term Data Strategy

### **6.1 Partner with Recycling Centers**

**Approach:**
1. Identify local recycling centers
2. Offer free digital waste tracking dashboard
3. In exchange: photograph incoming waste for dataset

**Expected:** 1,000 images/week with professional labeling

### **6.2 Gamification for Data Collection**

**"Data Bounty" Program:**
```
Users earn BONUS tokens for:
- First photo of rare waste type: +50 tokens
- High-quality photo (Grade A): +10 tokens
- Photo that improves model (uncertain sample): +20 tokens
```

### **6.3 Crowdsourced Labeling**

**Amazon Mechanical Turk / Label Studio:**
- Pay $0.01 per image label
- 3 labelers per image (majority vote)
- Cost: $0.03 × 10,000 images = $300

---

## Summary: Realistic MVP Data Plan

### **Week 1-2: Initial Dataset (No users needed)**
```
✅ Download TrashNet (2,500 images) - FREE
✅ Download TACO (15,000 images) - FREE  
✅ Download Kaggle (25,000 images) - FREE
✅ Remap & combine → ~21,000 images
✅ Generate synthetic for electronic → +5,000 images
✅ TOTAL: 26,000 images for MVP training
```

### **Week 3-4: MVP Launch**
```
✅ Train initial model (75-80% accuracy on public data)
✅ Deploy with high confidence threshold (0.8)
✅ Manual review for medium confidence (0.7-0.8)
✅ Beta test with 30 users → +300 real images
```

### **Month 2-3: Bootstrap Phase**
```
✅ Active learning from user submissions
✅ Validator corrections as training data
✅ Weekly model updates
✅ Accuracy improves to 85%+
```

### **Month 4+: Self-Sustaining**
```
✅ 10,000+ validated user images
✅ Monthly retraining with new data
✅ Continuous improvement loop
✅ Can reduce reliance on public datasets
```

---

## Cost Breakdown

```
Public Datasets:           $0 (all free/open-source)
Compute for Training:      $50 (Google Colab Pro or AWS)
Crowdsourced Labeling:     $300 (optional, for validation)
Storage (S3/IPFS):         $20/month
Total MVP Cost:            $70-370 (one-time)

Post-MVP Monthly:          $50-100 (compute + storage)
```

---

## Key Takeaway

**You DON'T need existing users to start!**

1. ✅ Use public datasets (26K+ images available NOW)
2. ✅ Train initial model (good enough for MVP)
3. ✅ Launch with high threshold + manual review
4. ✅ Bootstrap with real data via active learning
5. ✅ Continuous improvement as users grow

**This is a proven strategy used by successful ML startups.**
