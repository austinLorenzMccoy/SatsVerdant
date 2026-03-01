#!/usr/bin/env python3
"""
Generate synthetic data for underrepresented categories (especially electronic waste).
Uses background replacement and augmentation techniques.
"""
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import albumentations as A

# Directories
UNIFIED_DATA_DIR = Path("data/unified")
SYNTHETIC_DATA_DIR = Path("data/synthetic")
BACKGROUNDS_DIR = Path("data/raw/backgrounds")


class SyntheticDataGenerator:
    """Generate synthetic waste images using augmentation."""
    
    def __init__(self):
        # Create output directories
        for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
            (SYNTHETIC_DATA_DIR / category).mkdir(parents=True, exist_ok=True)
        
        # Load backgrounds
        self.backgrounds = list(BACKGROUNDS_DIR.glob("*.jpg")) if BACKGROUNDS_DIR.exists() else []
        
        # Define augmentation pipeline
        self.augmentation = A.Compose([
            A.RandomRotate90(p=0.5),
            A.Flip(p=0.5),
            A.Transpose(p=0.3),
            A.OneOf([
                A.GaussNoise(p=1),
                A.GaussianBlur(p=1),
                A.MotionBlur(p=1),
            ], p=0.3),
            A.OneOf([
                A.OpticalDistortion(p=1),
                A.GridDistortion(p=1),
                A.ElasticTransform(p=1),
            ], p=0.2),
            A.OneOf([
                A.CLAHE(clip_limit=2, p=1),
                A.Sharpen(p=1),
                A.Emboss(p=1),
            ], p=0.3),
            A.HueSaturationValue(p=0.3),
            A.RandomBrightnessContrast(p=0.3),
            A.RandomGamma(p=0.2),
        ])
        
        self.stats = {
            'plastic': 0,
            'paper': 0,
            'metal': 0,
            'organic': 0,
            'electronic': 0
        }
    
    def simple_background_removal(self, image):
        """Simple background removal using GrabCut."""
        mask = np.zeros(image.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        # Define rectangle around object (assume center)
        h, w = image.shape[:2]
        rect = (int(w*0.1), int(h*0.1), int(w*0.8), int(h*0.8))
        
        try:
            cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            result = image * mask2[:, :, np.newaxis]
            return result, mask2
        except:
            return image, np.ones(image.shape[:2], dtype=np.uint8)
    
    def composite_on_background(self, foreground, background_path):
        """Place foreground on new background."""
        # Load background
        bg = cv2.imread(str(background_path))
        if bg is None:
            return foreground
        
        # Resize background to match foreground
        bg = cv2.resize(bg, (foreground.shape[1], foreground.shape[0]))
        
        # Remove background from foreground
        fg_no_bg, mask = self.simple_background_removal(foreground)
        
        # Composite
        mask_3ch = cv2.merge([mask, mask, mask])
        result = np.where(mask_3ch == 1, fg_no_bg, bg)
        
        return result.astype(np.uint8)
    
    def generate_augmented_variant(self, image):
        """Generate augmented variant of image."""
        augmented = self.augmentation(image=image)
        return augmented['image']
    
    def generate_variants(self, image_path, num_variants=10, use_backgrounds=True):
        """Generate multiple synthetic variants of an image."""
        # Read original image
        image = cv2.imread(str(image_path))
        if image is None:
            return []
        
        variants = []
        
        for i in range(num_variants):
            variant = image.copy()
            
            # Apply background replacement (50% of the time if backgrounds available)
            if use_backgrounds and self.backgrounds and np.random.random() < 0.5:
                bg = np.random.choice(self.backgrounds)
                variant = self.composite_on_background(variant, bg)
            
            # Apply augmentation
            variant = self.generate_augmented_variant(variant)
            
            variants.append(variant)
        
        return variants
    
    def augment_category(self, category, target_count=5000):
        """Augment a specific category to reach target count."""
        print(f"\n🔄 Augmenting {category} category")
        print("="*60)
        
        source_dir = UNIFIED_DATA_DIR / category
        output_dir = SYNTHETIC_DATA_DIR / category
        
        if not source_dir.exists():
            print(f"⚠️  Source directory not found: {source_dir}")
            return
        
        # Get existing images
        existing_images = list(source_dir.glob("*.jpg")) + list(source_dir.glob("*.png"))
        current_count = len(existing_images)
        
        print(f"📊 Current: {current_count} images")
        print(f"🎯 Target: {target_count} images")
        
        if current_count >= target_count:
            print(f"✅ Already have enough images for {category}")
            return
        
        needed = target_count - current_count
        variants_per_image = max(1, needed // max(1, current_count))
        
        print(f"📈 Generating {variants_per_image} variants per image")
        
        generated = 0
        for img_path in tqdm(existing_images, desc=f"  Generating {category}"):
            variants = self.generate_variants(
                img_path,
                num_variants=variants_per_image,
                use_backgrounds=(len(self.backgrounds) > 0)
            )
            
            for idx, variant in enumerate(variants):
                output_path = output_dir / f"{img_path.stem}_syn_{idx}.jpg"
                cv2.imwrite(str(output_path), variant)
                generated += 1
                self.stats[category] += 1
                
                if generated >= needed:
                    break
            
            if generated >= needed:
                break
        
        print(f"✅ Generated {generated} synthetic images for {category}")
    
    def balance_dataset(self):
        """Balance dataset by augmenting underrepresented categories."""
        print("\n" + "="*60)
        print("⚖️  Balancing Dataset")
        print("="*60)
        
        # Count current images per category
        counts = {}
        for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
            source_dir = UNIFIED_DATA_DIR / category
            if source_dir.exists():
                counts[category] = len(list(source_dir.glob("*.jpg"))) + len(list(source_dir.glob("*.png")))
            else:
                counts[category] = 0
        
        # Find max count
        max_count = max(counts.values()) if counts else 0
        target_count = min(max_count, 8000)  # Cap at 8000 per category
        
        print(f"\n📊 Current distribution:")
        for category, count in counts.items():
            percentage = (count / max_count * 100) if max_count > 0 else 0
            print(f"  {category:12s}: {count:6,} ({percentage:5.1f}%)")
        
        print(f"\n🎯 Target per category: {target_count:,} images")
        
        # Augment underrepresented categories
        for category, count in counts.items():
            if count < target_count:
                self.augment_category(category, target_count)
    
    def print_statistics(self):
        """Print synthetic data generation statistics."""
        print("\n" + "="*60)
        print("📊 SYNTHETIC DATA STATISTICS")
        print("="*60)
        
        total_synthetic = 0
        for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
            count = self.stats[category]
            total_synthetic += count
            print(f"{category:12s}: {count:6,} synthetic images")
        
        print(f"\n{'TOTAL':12s}: {total_synthetic:6,} synthetic images")
        
        # Combined statistics
        print("\n" + "="*60)
        print("📊 COMBINED DATASET (Original + Synthetic)")
        print("="*60)
        
        grand_total = 0
        for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
            original = len(list((UNIFIED_DATA_DIR / category).glob("*.jpg"))) if (UNIFIED_DATA_DIR / category).exists() else 0
            synthetic = self.stats[category]
            total = original + synthetic
            grand_total += total
            print(f"{category:12s}: {total:6,} images ({original:,} original + {synthetic:,} synthetic)")
        
        print(f"\n{'GRAND TOTAL':12s}: {grand_total:6,} images")
        
        print("\n✅ Synthetic data generation complete!")


if __name__ == "__main__":
    print("🚀 SatsVerdant Synthetic Data Generator")
    
    generator = SyntheticDataGenerator()
    
    # Balance dataset
    generator.balance_dataset()
    
    # Print statistics
    generator.print_statistics()
    
    print("\nNext step: python scripts/train_model.py")
