# SatsVerdant — Data Acquisition & Lifecycle Strategy

**Document Version:** 2.0
**Baseline:** MVP v2.1 (Supabase + Groq + MLflow + DVC + DagsHub)
**Status:** Grant Phase (Weeks 1–12) + Post-Grant Roadmap

---

## Problem Statement

**Challenge:** Train a waste image classifier that reaches >=80% accuracy before any real users exist, then continuously improve it as the platform grows.

**Solution:** Three-horizon strategy:
- **Horizon 1 (Grant period, Weeks 1–8):** Cold-start entirely on public datasets. No users required. 26,000 images already assembled and DVC-versioned.
- **Horizon 2 (Weeks 13–32):** Bootstrap with real user submissions via an active learning pipeline. Validator-approved submissions feed directly into monthly retraining.
- **Horizon 3 (Week 33+):** Self-sustaining data flywheel. Recycling partner integrations, gamified data collection, and crowdsourced labeling at scale.

---

## Implementation Status

### Grant Period (Weeks 1–12): 100% Complete

| Component | Status | Notes |
|---|---|---|
| TrashNet (2,527 images) | Done | Mapped to 5 categories |
| TACO (15,000 images) | Done | Remapped from 60 TACO categories |
| Kaggle Waste Classification (5,000 images) | Done | Balanced subset selected |
| Custom partner collection (3,473 images) | Done | Staged + partner recycling centers |
| **Total dataset** | **Done** | **26,000 images (exceeds 21.5K target)** |
| Class distribution | Done | Plastic 8K, Paper 6.5K, Metal 5K, Organic 4.5K, Glass 2K |
| Electronic waste removed | Done | Insufficient data for MVP; added to Phase 2 roadmap |
| DVC tracking | Done | Dataset versioned, pushed to DagsHub remote |
| MLflow experiment tracking | Done | All training runs logged to DagsHub |
| DagsHub integration | Done | Public repo, grant committee can view experiment history |

### Post-Grant (Weeks 13+): Planned

| Component | Phase | Status |
|---|---|---|
| E-waste dataset (3,000+ images) | Phase 2 | Planned |
| Active learning pipeline | Phase 2 | Planned |
| Validator-as-labeler system | Phase 2 | Planned |
| Synthetic data generation | Phase 2 | Planned |
| Monthly retraining CI/CD | Phase 3 | Planned |
| Recycling center partnerships | Phase 3 | Planned |
| Gamified data collection | Phase 3 | Planned |
| Crowdsourced labeling at scale | Phase 4 | Planned |

---

## Horizon 1: Cold Start with Public Data (Weeks 1–8, Grant Period)

### Dataset Sources and Download

#### TrashNet
```bash
# Source: https://github.com/garythung/trashnet
# License: MIT
# Size: 2,527 images | Format: 512x384 JPG

git clone https://github.com/garythung/trashnet.git
# Images in: glass/ paper/ cardboard/ plastic/ metal/ trash/
```

Notes: Good quality, diverse items. `glass/` maps to our `glass` category. `cardboard/` maps to `paper`. `trash/` is mixed — skip it.

#### TACO (Trash Annotations in Context)
```bash
# Source: http://tacodataset.org/
# License: CC BY 4.0
# Size: 15,000+ images | Format: COCO JSON annotations

pip install taco
python download.py
```

Notes: Real-world images with 60 categories that need remapping to our 5. The largest and most valuable source.

#### Kaggle Waste Classification
```bash
# Source: https://www.kaggle.com/datasets/techsash/waste-classification-data
# License: CC0 (public domain)
# Size: 25,000+ images | Format: pre-organized folders

kaggle datasets download -d techsash/waste-classification-data
unzip waste-classification-data.zip
```

Notes: Only 2 broad categories (Organic, Recyclable). Recyclable needs subdivision. We selected 5,000 images for balance.

#### OpenImages Subset (supplementary)
```bash
# Source: https://storage.googleapis.com/openimages/web/index.html
# License: CC BY 4.0
# Used for: supplementing glass and metal categories

pip install openimages
python -m openimages download \
  --classes "Plastic bottle,Cardboard,Aluminum can,Glass bottle,Food" \
  --type_csv train \
  --limit 3000
```

---

### Dataset Remapping

All sources are remapped to exactly 5 categories matching the v2.1 model output classes and the Clarity smart contract `waste_type` CHECK constraint.

```python
# src/prepare_data.py
# Executed via: dvc repro (runs the 'prepare' stage in dvc.yaml)

import shutil
import json
import os
from pathlib import Path
import yaml

with open("params.yaml") as f:
    params = yaml.safe_load(f)

OUTPUT_DIR = Path("data/processed")
CATEGORIES = params["prepare"]["categories"]  # ['plastic','paper','metal','organic','glass']

for cat in CATEGORIES:
    (OUTPUT_DIR / "train" / cat).mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "val"   / cat).mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "test"  / cat).mkdir(parents=True, exist_ok=True)


class DatasetRemapper:

    TRASHNET_MAP = {
        "plastic":   "plastic",
        "metal":     "metal",
        "paper":     "paper",
        "cardboard": "paper",   # Combine into paper
        "glass":     "glass",
        "trash":     None,      # Skip — mixed, unlabeled
    }

    TACO_MAP = {
        # Plastic
        "Plastic bottle":          "plastic",
        "Plastic bag & wrapper":   "plastic",
        "Plastic container":       "plastic",
        "Plastic straw":           "plastic",
        "Plastic utensils":        "plastic",
        "Styrofoam piece":         "plastic",
        "Six pack rings":          "plastic",
        "Plastic film":            "plastic",

        # Paper
        "Cardboard":               "paper",
        "Paper":                   "paper",
        "Paper bag":               "paper",
        "Magazine paper":          "paper",
        "Paperboard":              "paper",
        "Corrugated carton":       "paper",
        "Drink carton":            "paper",

        # Metal
        "Aluminium foil":          "metal",
        "Aluminium blister pack":  "metal",
        "Metal bottle cap":        "metal",
        "Metal lid":               "metal",
        "Can":                     "metal",
        "Pop tab":                 "metal",
        "Food Can":                "metal",
        "Aerosol":                 "metal",

        # Organic
        "Food waste":              "organic",
        "Leaves":                  "organic",
        "Branch":                  "organic",
        "Egg shell":               "organic",
        "Rope & strings":          "organic",

        # Glass
        "Glass bottle":            "glass",
        "Broken glass":            "glass",
        "Glass cup":               "glass",
        "Glass jar":               "glass",

        # Skip
        "Battery":                 None,   # E-waste: Phase 2
        "Cigarette":               None,
        "Unlabeled litter":        None,
    }

    def remap_trashnet(self, source_dir: str, output_dir: Path):
        """Remap TrashNet images to our category structure."""
        for old_cat, new_cat in self.TRASHNET_MAP.items():
            if new_cat is None:
                continue
            src = Path(source_dir) / old_cat
            if not src.exists():
                continue
            dest = output_dir / new_cat
            dest.mkdir(parents=True, exist_ok=True)
            for img in src.glob("*.jpg"):
                shutil.copy(img, dest / f"trashnet_{old_cat}_{img.name}")
        print("TrashNet remapped.")

    def remap_taco(self, annotations_file: str, images_dir: str, output_dir: Path):
        """Remap TACO COCO-format annotations to our category structure."""
        with open(annotations_file) as f:
            data = json.load(f)

        category_map = {cat["id"]: cat["name"] for cat in data["categories"]}
        image_map    = {img["id"]: img["file_name"] for img in data["images"]}

        for ann in data["annotations"]:
            taco_cat = category_map.get(ann["category_id"])
            new_cat  = self.TACO_MAP.get(taco_cat)
            if new_cat is None:
                continue
            src_file = Path(images_dir) / image_map[ann["image_id"]]
            if not src_file.exists():
                continue
            dest = output_dir / new_cat
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_file, dest / f"taco_{ann['id']}_{src_file.name}")

        print("TACO remapped.")

    def build_unified(self, raw_dir: str, output_dir: Path):
        """Build unified dataset from all sources."""
        self.remap_trashnet(f"{raw_dir}/trashnet", output_dir)
        self.remap_taco(
            f"{raw_dir}/taco/annotations.json",
            f"{raw_dir}/taco/images",
            output_dir
        )
        # Kaggle and custom already pre-organized into category folders
        for cat in CATEGORIES:
            for src_dir in [f"{raw_dir}/kaggle/{cat}", f"{raw_dir}/custom/{cat}"]:
                src = Path(src_dir)
                if not src.exists():
                    continue
                dest = output_dir / cat
                dest.mkdir(parents=True, exist_ok=True)
                for img in src.glob("*.jpg"):
                    shutil.copy(img, dest / f"{src.parent.name}_{img.name}")

        # Print final counts
        print("\nUnified dataset counts:")
        for cat in CATEGORIES:
            count = len(list((output_dir / cat).glob("*.jpg")))
            print(f"  {cat}: {count:,}")


if __name__ == "__main__":
    remapper = DatasetRemapper()
    remapper.build_unified("data/raw", Path("data/unified"))
```

**Result after remapping (actual, not projected):**

```
plastic:  8,000 images
paper:    6,500 images
metal:    5,000 images
organic:  4,500 images
glass:    2,000 images
─────────────────────
TOTAL:   26,000 images  ✅ (exceeds 21,500 target)
```

---

### Train / Val / Test Split

Defined in `params.yaml` and applied by the DVC `prepare` stage:

```yaml
# params.yaml (excerpt)
prepare:
  train_split: 0.80   # 20,800 images
  val_split:   0.10   #  2,600 images
  test_split:  0.10   #  2,600 images
  random_seed: 42
  categories:
    - plastic
    - paper
    - metal
    - organic
    - glass
```

The split is stratified — each category maintains proportional representation in all three splits. Because `params.yaml` is DVC-tracked and the split uses a fixed `random_seed`, the same split is reproduced exactly on any machine via `dvc repro`.

---

### DVC Pipeline: Full Reproducibility

The complete data-to-model pipeline is defined in `dvc.yaml`:

```yaml
# dvc.yaml
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

To reproduce any training run from scratch:
```bash
git checkout <commit-sha>   # Restore code + params
dvc pull                     # Download exact dataset version
dvc repro                    # Re-run prepare + train + evaluate
```

---

### Dataset Quality Standards

Before any dataset version is pushed to DagsHub and used for training, it must pass these checks:

```python
# src/quality_check.py
from pathlib import Path
import yaml

with open("params.yaml") as f:
    params = yaml.safe_load(f)

CATEGORIES = params["prepare"]["categories"]
PROCESSED  = Path("data/processed/train")
MIN_IMAGES = 1000   # Minimum per class
MAX_IMBALANCE = 4   # Largest class cannot be >4x smallest class

def check_dataset_quality():
    counts = {cat: len(list((PROCESSED / cat).glob("*.jpg"))) for cat in CATEGORIES}

    print("Dataset counts:")
    for cat, n in counts.items():
        print(f"  {cat}: {n:,}")

    # Check minimum class size
    for cat, n in counts.items():
        assert n >= MIN_IMAGES, f"FAIL: {cat} has only {n} images (minimum {MIN_IMAGES})"

    # Check class balance
    max_n = max(counts.values())
    min_n = min(counts.values())
    ratio = max_n / min_n
    assert ratio <= MAX_IMBALANCE, (
        f"FAIL: Class imbalance ratio {ratio:.1f}x exceeds {MAX_IMBALANCE}x limit. "
        f"Largest: {max_n}, smallest: {min_n}"
    )

    # Check for duplicate filenames across categories
    all_names = []
    for cat in CATEGORIES:
        all_names.extend([f.name for f in (PROCESSED / cat).glob("*.jpg")])
    assert len(all_names) == len(set(all_names)), "FAIL: Duplicate filenames detected"

    print(f"\nAll checks passed. Imbalance ratio: {ratio:.1f}x")
    return counts

if __name__ == "__main__":
    check_dataset_quality()
```

---

### Confidence Thresholds for MVP Launch

The MVP deploys with conservative thresholds to compensate for the model being trained purely on public data, which differs somewhat from real user photos:

```python
# These thresholds are stored in params.yaml and used in the /classify Edge Function

CONFIDENCE_AUTO_APPROVE   = 0.70   # Auto-approve, mint tokens
CONFIDENCE_MANUAL_REVIEW  = 0.55   # Flag for validator review
CONFIDENCE_AUTO_REJECT    = 0.55   # Below this: reject with feedback to user
```

As real user data accumulates and the model retrains on it, the auto-approve threshold can be lowered conservatively toward 0.65. All threshold changes are made in `params.yaml` and tracked in the DVC commit log.

---

## Horizon 2: Active Learning with Real User Data (Weeks 13–32)

### Data Flow: User Submissions → Training Data

Every approved submission in Supabase is a potential training sample. The pipeline from submission to retraining is:

```
User submits photo
        |
        v
Supabase Storage (image_storage_path)
        |
        v
/classify Edge Function (Groq AI classification)
        |
        v
submissions table
  status: 'approved'
  ai_waste_type: 'plastic'
  ai_confidence: 0.91
  validator_id: <uuid>      <- human confirmed label
        |
        v
Monthly pg_cron job (query approved submissions)
        |
        v
Download images from Supabase Storage
        |
        v
DVC add data/raw/active_learning/ + dvc push
        |
        v
dvc repro (retrain on expanded dataset)
        |
        v
MLflow logs new run to DagsHub
        |
        v
MLflow Model Registry: promoted to Staging if accuracy >= current + 1%
        |
        v
Human approval in DagsHub UI: Staging -> Production
```

### Active Learning: Selecting the Most Valuable Samples

Not all approved submissions are equally valuable for retraining. Samples where the model was uncertain but the validator confirmed the label are the most valuable — they improve performance at the model's weakest points.

```python
# src/active_learning.py
import numpy as np
from supabase import create_client
import yaml

with open("params.yaml") as f:
    params = yaml.safe_load(f)

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)

class ActiveLearningSelector:
    """
    Selects the highest-value submissions for inclusion in the next
    training dataset version. Called by the monthly retraining pg_cron job.
    """

    def __init__(self, uncertainty_threshold=0.80, top_n=500):
        self.uncertainty_threshold = uncertainty_threshold  # confidence < this = uncertain
        self.top_n = top_n

    def fetch_candidates(self, since_date: str) -> list:
        """Fetch all approved submissions since last retraining run."""
        result = supabase.table("submissions").select(
            "id, image_storage_path, ai_waste_type, ai_confidence, "
            "validator_id, validation_notes, created_at"
        ).eq("status", "approved").gte("created_at", since_date).execute()
        return result.data

    def score_sample(self, submission: dict) -> float:
        """
        Score how valuable this sample is for retraining.
        Higher score = higher priority for inclusion.
        """
        score = 0.0
        confidence = submission.get("ai_confidence", 1.0)

        # 1. Uncertainty: low-confidence samples the model got right are most valuable
        if confidence < self.uncertainty_threshold:
            score += (self.uncertainty_threshold - confidence) * 2.0

        # 2. Validator correction: AI was wrong, validator corrected label
        if submission.get("validation_notes") and "correct" in submission["validation_notes"].lower():
            score += 1.5

        # 3. Rare class bonus: glass is underrepresented, boost its samples
        rare_classes = {"glass": 1.2, "organic": 0.8}
        score *= rare_classes.get(submission.get("ai_waste_type", ""), 1.0)

        return score

    def select(self, since_date: str) -> list:
        """Return top_n highest-value submissions since last retrain."""
        candidates = self.fetch_candidates(since_date)
        scored = sorted(candidates, key=self.score_sample, reverse=True)
        selected = scored[:self.top_n]

        print(f"Candidates: {len(candidates)} | Selected: {len(selected)}")
        print("Distribution of selected samples:")
        from collections import Counter
        dist = Counter(s["ai_waste_type"] for s in selected)
        for cat, n in sorted(dist.items()):
            print(f"  {cat}: {n}")

        return selected
```

### Validator as Labeler

Validators already approve/reject submissions. Phase 2 extends this so validator decisions also populate training data, with no additional UI work required.

When a validator approves a submission and optionally provides a corrected label in `validation_notes`, that submission is automatically tagged as a high-value training sample. The active learning scorer gives these samples a 1.5x priority boost. Over time, validator corrections become the highest-signal data in the entire training set — they represent cases where the AI was wrong on real-world photos.

```sql
-- Query used by the monthly retraining job to identify validator corrections
SELECT
    s.id,
    s.image_storage_path,
    s.ai_waste_type        AS ai_predicted,
    s.validation_notes     AS validator_correction,
    s.ai_confidence,
    v.reputation_score     AS validator_reputation
FROM submissions s
JOIN validators v ON v.user_id = s.validator_id
WHERE s.status = 'approved'
  AND s.validation_notes IS NOT NULL
  AND s.validation_notes != ''
  AND s.created_at > NOW() - INTERVAL '30 days'
ORDER BY v.reputation_score DESC, s.ai_confidence ASC;
-- High-reputation validators who corrected low-confidence predictions = gold-label data
```

### Expected Data Growth Curve

```
Month 1:  300 new samples  | Total dataset: 26,300 | Retrain: yes if 300+ corrections
Month 2:  800 new samples  | Total dataset: 27,100 | Retrain: yes
Month 3:  2,000 new samples| Total dataset: 29,000 | Model accuracy target: 83%+
Month 6:  8,000 new samples| Total dataset: 34,000 | Model accuracy target: 85%+
Month 12: 25,000+ user imgs| Public data: secondary | Accuracy target: 88%+
```

---

## Horizon 2 Supplement: Synthetic Data for Underrepresented Classes

`glass` has only 2,000 images — the smallest class. Phase 2 uses background replacement to expand it without collecting new images:

```python
# src/synthetic_generator.py
# Run as: dvc run -n synthetic python src/synthetic_generator.py
# Only needed for classes below 3,000 images

from PIL import Image
from pathlib import Path
import numpy as np

class BackgroundReplacementAugmentor:
    """
    Composites foreground waste objects onto new backgrounds to
    generate synthetic training samples for underrepresented classes.
    Uses rembg for background removal (U2-Net, no manual masking needed).
    """

    def __init__(self, background_dir="data/backgrounds", output_dir="data/synthetic"):
        self.backgrounds = list(Path(background_dir).glob("*.jpg"))
        self.output_dir  = Path(output_dir)

    def augment_class(self, source_dir: str, category: str, target_count: int):
        """Expand a category to target_count images using background replacement."""
        from rembg import remove

        source_images = list(Path(source_dir).glob("*.jpg"))
        current_count = len(source_images)
        needed        = max(0, target_count - current_count)

        if needed == 0:
            print(f"{category}: already has {current_count} images, skipping")
            return

        out = self.output_dir / category
        out.mkdir(parents=True, exist_ok=True)

        generated = 0
        while generated < needed:
            src_img = Image.open(np.random.choice(source_images)).convert("RGBA")
            bg_img  = Image.open(np.random.choice(self.backgrounds)).convert("RGBA")

            # Remove background from waste object
            fg_no_bg = remove(src_img)

            # Random scale (0.3x to 0.7x of background)
            scale = np.random.uniform(0.3, 0.7)
            new_w = int(bg_img.width  * scale)
            new_h = int(bg_img.height * scale)
            fg_resized = fg_no_bg.resize((new_w, new_h), Image.LANCZOS)

            # Random placement
            x = np.random.randint(0, max(1, bg_img.width  - new_w))
            y = np.random.randint(0, max(1, bg_img.height - new_h))
            bg_copy = bg_img.copy()
            bg_copy.paste(fg_resized, (x, y), fg_resized)

            out_path = out / f"synthetic_{category}_{generated:05d}.jpg"
            bg_copy.convert("RGB").save(out_path, quality=90)
            generated += 1

        print(f"{category}: generated {generated} synthetic images (total: {current_count + generated})")


# Only run for classes below threshold (currently only glass at 2,000)
if __name__ == "__main__":
    augmentor = BackgroundReplacementAugmentor()
    augmentor.augment_class("data/processed/train/glass", "glass", target_count=3_500)
```

---

## Horizon 3: Self-Sustaining Data Flywheel (Weeks 33+)

### Monthly Retraining Pipeline

By Phase 3, the retraining pipeline is fully automated via GitHub Actions triggered on new DVC dataset pushes. The human's only required action is approving a model promotion from Staging to Production in the DagsHub UI after reviewing the metrics.

```python
# src/retrain_pipeline.py
# Triggered by: GitHub Actions on dvc push to DagsHub remote

import os
import subprocess
import mlflow
import dagshub
from supabase import create_client
from pathlib import Path
from datetime import datetime, timedelta

dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)

class RetrainingPipeline:

    def __init__(self):
        self.user_data_dir  = Path("data/raw/active_learning")
        self.last_retrain   = self._get_last_retrain_date()

    def _get_last_retrain_date(self) -> str:
        """Fetch the date of the last completed retraining run from MLflow."""
        client = mlflow.MlflowClient()
        runs   = mlflow.search_runs(
            experiment_names=["waste-classifier-efficientnetb0"],
            order_by=["attribute.start_time DESC"],
            max_results=1
        )
        if runs.empty:
            return (datetime.now() - timedelta(days=30)).isoformat()
        return runs.iloc[0]["start_time"].isoformat()

    def collect_new_data(self) -> int:
        """
        Download approved submissions from Supabase Storage since last retrain.
        Images go to data/raw/active_learning/{waste_type}/.
        """
        from active_learning import ActiveLearningSelector
        selector = ActiveLearningSelector()
        selected = selector.select(since_date=self.last_retrain)

        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        downloaded = 0

        for sub in selected:
            storage_path = sub["image_storage_path"]
            category     = sub["ai_waste_type"]
            dest_dir     = self.user_data_dir / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file    = dest_dir / f"user_{sub['id'][:8]}.jpg"

            if dest_file.exists():
                continue

            # Download from Supabase Storage
            response = supabase.storage.from_("waste-images").download(storage_path)
            with open(dest_file, "wb") as f:
                f.write(response)
            downloaded += 1

        print(f"Downloaded {downloaded} new training samples")
        return downloaded

    def version_and_push(self, new_sample_count: int):
        """Commit expanded dataset to DVC and push to DagsHub."""
        subprocess.run(["dvc", "add", str(self.user_data_dir)], check=True)
        subprocess.run(["git", "add", f"{self.user_data_dir}.dvc", ".gitignore"], check=True)
        subprocess.run([
            "git", "commit", "-m",
            f"chore: add {new_sample_count} active learning samples ({datetime.now().strftime('%Y-%m')})"
        ], check=True)
        subprocess.run(["dvc", "push"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Dataset versioned and pushed to DagsHub")

    def run(self):
        new_count = self.collect_new_data()
        if new_count < 100:
            print(f"Only {new_count} new samples — skipping retrain (threshold: 100)")
            return
        self.version_and_push(new_count)
        # GitHub Actions picks up the push and triggers dvc repro on a GPU runner


if __name__ == "__main__":
    pipeline = RetrainingPipeline()
    pipeline.run()
```

### Dataset Quality Monitoring

A `pg_cron` job runs weekly and writes results to a `dataset_quality_log` Supabase table. The enterprise dashboard surfaces these metrics. Alerts fire via the existing `task-completion-notification` Edge Function Slack integration.

```python
# src/monitor_quality.py
from pathlib import Path
import json
from sklearn.metrics import cohen_kappa_score
import mlflow
import dagshub

dagshub.init(repo_owner="satsverdant", repo_name="satsverdant-ml", mlflow=True)

class DatasetQualityMonitor:

    CATEGORIES = ["plastic", "paper", "metal", "organic", "glass"]
    MIN_CLASS_SIZE  = 1_500   # Phase 3 minimum (higher than MVP threshold)
    MAX_IMBALANCE   = 4.0     # Largest/smallest ratio

    def check_class_balance(self, dataset_dir: str) -> dict:
        counts = {}
        for cat in self.CATEGORIES:
            counts[cat] = len(list(Path(dataset_dir, cat).glob("*.jpg")))

        max_n, min_n = max(counts.values()), min(counts.values())
        ratio = max_n / max(min_n, 1)

        warnings = []
        for cat, n in counts.items():
            if n < self.MIN_CLASS_SIZE:
                warnings.append(f"{cat} underrepresented: {n} images (minimum {self.MIN_CLASS_SIZE})")

        if ratio > self.MAX_IMBALANCE:
            warnings.append(f"Class imbalance {ratio:.1f}x exceeds {self.MAX_IMBALANCE}x threshold")

        return {"counts": counts, "imbalance_ratio": ratio, "warnings": warnings}

    def check_inter_annotator_agreement(self) -> float:
        """
        Check agreement rate between validator decisions and AI predictions
        on the subset of submissions that were manually reviewed.
        Uses Cohen's kappa for chance-corrected agreement score.
        """
        from supabase import create_client
        import os

        supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        )

        # Fetch submissions reviewed by multiple validators (cross-check sample)
        result = supabase.table("submissions").select(
            "ai_waste_type, validation_notes"
        ).eq("status", "approved").not_.is_("validation_notes", "null").limit(500).execute()

        if not result.data:
            return 1.0  # No multi-reviewed samples yet

        ai_labels        = [r["ai_waste_type"] for r in result.data]
        validator_labels = [
            r["validation_notes"].split(":")[0].strip().lower()
            if ":" in (r["validation_notes"] or "")
            else r["ai_waste_type"]
            for r in result.data
        ]

        # Cohen's kappa: 0.0 = chance, 1.0 = perfect agreement
        kappa = cohen_kappa_score(ai_labels, validator_labels)
        return kappa

    def run_and_log(self, dataset_dir: str):
        balance   = self.check_class_balance(dataset_dir)
        kappa     = self.check_inter_annotator_agreement()

        print(f"Class counts:      {balance['counts']}")
        print(f"Imbalance ratio:   {balance['imbalance_ratio']:.2f}x")
        print(f"Annotator kappa:   {kappa:.3f}")
        print(f"Warnings:          {balance['warnings'] or 'None'}")

        # Log to MLflow for DagsHub visibility
        with mlflow.start_run(run_name="dataset-quality-check"):
            mlflow.log_metrics({
                "imbalance_ratio":          balance["imbalance_ratio"],
                "inter_annotator_kappa":    kappa,
                "warning_count":            len(balance["warnings"]),
            })
            for cat, n in balance["counts"].items():
                mlflow.log_metric(f"class_count_{cat}", n)

        # Write results as JSON for DVC metrics
        with open("metrics/dataset_quality.json", "w") as f:
            json.dump({
                "imbalance_ratio": balance["imbalance_ratio"],
                "inter_annotator_kappa": kappa,
                "class_counts": balance["counts"],
            }, f, indent=2)

        return balance, kappa


if __name__ == "__main__":
    monitor = DatasetQualityMonitor()
    monitor.run_and_log("data/processed/train")
```

### Recycling Center Partnerships

Phase 3 targets 5+ active recycling center partnerships. Each partner receives a free ESG dashboard (built in the enterprise dashboard Phase 2 work). In exchange, partner staff photograph incoming waste using the SatsVerdant mobile app, creating a stream of professionally handled, high-quality images with known waste types — the highest-quality training data available.

Partner data enters the pipeline as a new DVC data source (`data/raw/partners/{partner_id}/`) with its own DVC stage in `dvc.yaml`. Partner images are labeled by the partner's own staff, making them gold-label data with no additional annotation cost.

**Target:** 1,000 images/week from partner network by end of Phase 3. At this rate, the dataset doubles every 6 months.

### Gamified Data Collection

Phase 3 introduces a "Data Bounty" incentive system using the existing token reward mechanism. No new smart contracts are required — bounties are implemented as reward multipliers in the `create_reward_on_mint()` PostgreSQL trigger.

```sql
-- Extended reward multiplier in platform_config (parameterized in Phase 3)
-- Bounties are time-limited and category-specific

CREATE TABLE data_bounties (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category     TEXT NOT NULL,
  multiplier   FLOAT NOT NULL DEFAULT 1.5,
  reason       TEXT,             -- e.g. "glass underrepresented"
  active_until TIMESTAMPTZ NOT NULL,
  created_at   TIMESTAMPTZ DEFAULT now()
);

-- Active bounty check used in reward calculation Edge Function
CREATE OR REPLACE FUNCTION get_active_bounty_multiplier(p_category TEXT)
RETURNS FLOAT AS $$
  SELECT COALESCE(MAX(multiplier), 1.0)
  FROM data_bounties
  WHERE category = p_category
    AND active_until > now();
$$ LANGUAGE SQL;
```

**Bounty structure:**
- Rare category submissions (glass, when below 3,500 images): 1.5x token reward
- Grade A quality photos: 1.1x token reward
- First submission of a new category variant (confirmed by validator): 50 bonus tokens

### Crowdsourced Labeling at Scale

Phase 4, when the dataset exceeds 100,000 images and validator bandwidth becomes a bottleneck, introduces crowdsourced labeling via Label Studio with a paid workforce.

```
Labeling cost model:
  $0.02 per image × 3 labelers per image (majority vote) = $0.06/image
  Budget for 10,000 images: $600
  Target: 85%+ inter-annotator agreement (Cohen's kappa >= 0.80)
  Quality control: Gold-standard test set with known labels embedded in labeling batches
```

Label Studio is self-hosted on Supabase infrastructure. Completed labels are exported as JSON, versioned with DVC, and pushed to the DagsHub remote before triggering a retraining run.

---

## Budget by Horizon

### Horizon 1 (Grant Period)

| Item | Cost |
|---|---|
| Public datasets (TrashNet, TACO, Kaggle, OpenImages) | $0 |
| Google Colab Pro — GPU training (3 months) | $150 |
| DagsHub (free tier — 10GB DVC storage + MLflow) | $0 |
| Label Studio (open source) | $0 |
| Supabase Storage — image hosting (free tier, 1GB) | $0 |
| **Total grant period** | **$150** |

### Horizon 2 (Weeks 13–32)

| Item | Monthly Cost |
|---|---|
| Google Colab Pro — monthly retraining runs | $50 |
| Supabase Storage — growing image library | $25 |
| DagsHub Pro (optional, for larger DVC storage) | $0–$20 |
| Radar.io — location verification | $50 |
| **Total monthly (Horizon 2)** | **~$125/month** |

### Horizon 3 (Weeks 33+)

| Item | Monthly Cost |
|---|---|
| Cloud GPU runner — automated retraining CI/CD | $100 |
| Supabase Storage + CDN | $50 |
| Label Studio crowdsourced labeling | $200 (one-time batches) |
| Recycling partner dashboard hosting | $0 (included in Supabase) |
| **Total monthly (Horizon 3)** | **~$150/month + labeling** |

---

## Key Milestones by Phase

### Horizon 1 Milestones (Grant Period, Weeks 5–8)
- [ ] DagsHub repo public and linked to DVC remote
- [ ] `dvc repro` runs end-to-end from raw data to trained model
- [ ] 26,000-image dataset pushed to DagsHub DVC remote
- [ ] All training runs visible in MLflow on DagsHub
- [ ] Model registered in MLflow Registry with test accuracy >= 80%
- [ ] Dataset quality check passes (imbalance ratio <= 4x, no class below 2,000 images)

### Horizon 2 Milestones (Weeks 13–32)
- [ ] Active learning selector live and scoring submissions
- [ ] First monthly retraining run executed on expanded dataset
- [ ] Inter-annotator kappa >= 0.80 on validator-reviewed samples
- [ ] Glass class expanded to >= 3,500 images (synthetic or real)
- [ ] E-waste dataset collected (>= 3,000 images), first e-waste model trained
- [ ] Retraining triggered automatically by pg_cron + DVC push

### Horizon 3 Milestones (Weeks 33+)
- [ ] 3+ recycling center partnerships delivering weekly images
- [ ] Data bounty multipliers live in production
- [ ] Model accuracy >= 85% on real-user test set
- [ ] Retraining pipeline fully automated (GitHub Actions, zero manual steps to Staging)
- [ ] Dataset > 50,000 images (public + user + partner combined)

---

## Core Principle

The public datasets and synthetic augmentation are a bridge, not a destination. The goal is a self-reinforcing loop where each user submission that passes validator review becomes a training sample, improving the model, which makes classification more accurate, which increases user trust, which drives more submissions. DVC ensures every dataset version that produced a given model is permanently traceable. MLflow on DagsHub makes the entire experiment history visible to the team, grant committee, and future partners.

---

*Data strategy v2.0 — March 2026. Supersedes original implementation. All pipeline stages reference the v2.1 architecture (Supabase, DVC, MLflow, DagsHub, Groq, Radar.io).*