#!/usr/bin/env python3
"""
Remap public datasets to SatsVerdant's 5 categories:
plastic, paper, metal, organic, electronic
"""
import shutil
import json
from pathlib import Path
from tqdm import tqdm
import cv2
import numpy as np

# Directories
RAW_DATA_DIR = Path("data/raw")
UNIFIED_DATA_DIR = Path("data/unified")

# Create output directories
for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
    (UNIFIED_DATA_DIR / category).mkdir(parents=True, exist_ok=True)


class DatasetRemapper:
    """Remap public datasets to our 5-category taxonomy."""
    
    def __init__(self):
        # TrashNet mapping
        self.trashnet_mapping = {
            'plastic': 'plastic',
            'metal': 'metal',
            'paper': 'paper',
            'cardboard': 'paper',  # Combine with paper
            'glass': None,  # Skip - not in our taxonomy
            'trash': None   # Skip - mixed waste
        }
        
        # TACO mapping (60 categories → 5 categories)
        self.taco_mapping = {
            # Plastic variants
            'Plastic bottle': 'plastic',
            'Plastic bag & wrapper': 'plastic',
            'Plastic container': 'plastic',
            'Plastic straw': 'plastic',
            'Plastic utensils': 'plastic',
            'Styrofoam piece': 'plastic',
            'Plastic film': 'plastic',
            'Six pack rings': 'plastic',
            'Plastic glooves': 'plastic',
            'Other plastic': 'plastic',
            'Clear plastic bottle': 'plastic',
            'Plastic bottle cap': 'plastic',
            
            # Paper variants
            'Cardboard': 'paper',
            'Paper': 'paper',
            'Paper bag': 'paper',
            'Magazine paper': 'paper',
            'Paperboard': 'paper',
            'Carton': 'paper',
            'Egg carton': 'paper',
            'Toilet tube': 'paper',
            
            # Metal variants
            'Aluminium foil': 'metal',
            'Aluminium blister pack': 'metal',
            'Metal bottle cap': 'metal',
            'Metal lid': 'metal',
            'Can': 'metal',
            'Pop tab': 'metal',
            'Scrap metal': 'metal',
            'Aerosol': 'metal',
            'Drink can': 'metal',
            'Food can': 'metal',
            
            # Organic variants
            'Food waste': 'organic',
            'Leaves': 'organic',
            'Rope & strings': 'organic',
            
            # Electronic variants
            'Battery': 'electronic',
            'Electronics': 'electronic',
            
            # Skip these
            'Cigarette': None,
            'Glass bottle': None,
            'Glass jar': None,
            'Broken glass': None,
            'Other': None,
            'Unlabeled litter': None,
        }
        
        self.stats = {
            'plastic': 0,
            'paper': 0,
            'metal': 0,
            'organic': 0,
            'electronic': 0,
            'skipped': 0
        }
    
    def remap_trashnet(self):
        """Remap TrashNet dataset."""
        print("\n" + "="*60)
        print("🔄 Remapping TrashNet Dataset")
        print("="*60)
        
        trashnet_dir = RAW_DATA_DIR / "trashnet" / "data"
        
        if not trashnet_dir.exists():
            print("⚠️  TrashNet not found. Skipping...")
            return
        
        for old_category in trashnet_dir.iterdir():
            if not old_category.is_dir():
                continue
            
            new_category = self.trashnet_mapping.get(old_category.name)
            
            if new_category is None:
                print(f"⏭️  Skipping {old_category.name}")
                continue
            
            dest_dir = UNIFIED_DATA_DIR / new_category
            images = list(old_category.glob("*.jpg"))
            
            print(f"📁 {old_category.name} → {new_category}: {len(images)} images")
            
            for img_path in tqdm(images, desc=f"  Copying {old_category.name}"):
                # Create unique filename
                new_name = f"trashnet_{old_category.name}_{img_path.name}"
                dest_path = dest_dir / new_name
                
                # Copy and verify image
                try:
                    shutil.copy2(img_path, dest_path)
                    # Verify image is readable
                    img = cv2.imread(str(dest_path))
                    if img is None:
                        dest_path.unlink()
                        continue
                    self.stats[new_category] += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to copy {img_path.name}: {e}")
    
    def remap_taco(self):
        """Remap TACO dataset."""
        print("\n" + "="*60)
        print("🔄 Remapping TACO Dataset")
        print("="*60)
        
        taco_dir = RAW_DATA_DIR / "taco"
        annotations_file = taco_dir / "data" / "annotations.json"
        
        if not annotations_file.exists():
            print("⚠️  TACO annotations not found. Skipping...")
            return
        
        print("Loading TACO annotations...")
        with open(annotations_file) as f:
            data = json.load(f)
        
        # Create category mapping
        category_id_to_name = {cat['id']: cat['name'] for cat in data['categories']}
        image_id_to_filename = {img['id']: img['file_name'] for img in data['images']}
        
        # Process annotations
        annotation_map = {}
        for ann in data['annotations']:
            image_id = ann['image_id']
            category_name = category_id_to_name.get(ann['category_id'], 'Unknown')
            new_category = self.taco_mapping.get(category_name)
            
            if new_category and image_id not in annotation_map:
                annotation_map[image_id] = {
                    'filename': image_id_to_filename.get(image_id),
                    'category': new_category
                }
        
        print(f"Found {len(annotation_map)} images to remap")
        
        # Copy images
        images_dir = taco_dir / "data"
        
        for image_id, info in tqdm(annotation_map.items(), desc="  Copying TACO images"):
            if not info['filename']:
                continue
            
            src_path = images_dir / info['filename']
            if not src_path.exists():
                continue
            
            category = info['category']
            dest_dir = UNIFIED_DATA_DIR / category
            new_name = f"taco_{image_id}_{Path(info['filename']).name}"
            dest_path = dest_dir / new_name
            
            try:
                shutil.copy2(src_path, dest_path)
                # Verify image
                img = cv2.imread(str(dest_path))
                if img is None:
                    dest_path.unlink()
                    continue
                self.stats[category] += 1
            except Exception as e:
                continue
    
    def remap_kaggle(self):
        """Remap Kaggle Waste Classification dataset."""
        print("\n" + "="*60)
        print("🔄 Remapping Kaggle Dataset")
        print("="*60)
        
        kaggle_dir = RAW_DATA_DIR / "kaggle_waste"
        
        if not kaggle_dir.exists():
            print("⚠️  Kaggle dataset not found. Skipping...")
            return
        
        # Kaggle dataset structure varies, adapt as needed
        # Common structure: DATASET/TRAIN/O (organic) and DATASET/TRAIN/R (recyclable)
        
        # Map recyclable to plastic/paper/metal based on image analysis or subfolder
        # For now, we'll do a simple mapping
        
        for category_dir in kaggle_dir.rglob("*"):
            if not category_dir.is_dir():
                continue
            
            dir_name = category_dir.name.lower()
            
            # Simple heuristic mapping
            if 'organic' in dir_name or dir_name == 'o':
                new_category = 'organic'
            elif 'plastic' in dir_name:
                new_category = 'plastic'
            elif 'paper' in dir_name or 'cardboard' in dir_name:
                new_category = 'paper'
            elif 'metal' in dir_name or 'can' in dir_name:
                new_category = 'metal'
            elif 'recyclable' in dir_name or dir_name == 'r':
                # Split recyclable randomly between plastic, paper, metal
                new_category = np.random.choice(['plastic', 'paper', 'metal'])
            else:
                continue
            
            images = list(category_dir.glob("*.jpg")) + list(category_dir.glob("*.png"))
            
            if len(images) == 0:
                continue
            
            print(f"📁 {category_dir.name} → {new_category}: {len(images)} images")
            
            for img_path in tqdm(images[:5000], desc=f"  Copying {category_dir.name}"):  # Limit per category
                new_name = f"kaggle_{category_dir.name}_{img_path.name}"
                dest_path = UNIFIED_DATA_DIR / new_category / new_name
                
                try:
                    shutil.copy2(img_path, dest_path)
                    # Verify image
                    img = cv2.imread(str(dest_path))
                    if img is None:
                        dest_path.unlink()
                        continue
                    self.stats[new_category] += 1
                except Exception as e:
                    continue
    
    def print_statistics(self):
        """Print final dataset statistics."""
        print("\n" + "="*60)
        print("📊 UNIFIED DATASET STATISTICS")
        print("="*60)
        
        total = 0
        for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
            count = self.stats[category]
            total += count
            bar = "█" * (count // 100)
            print(f"{category:12s}: {count:6,} images {bar}")
        
        print(f"\n{'TOTAL':12s}: {total:6,} images")
        print(f"{'Skipped':12s}: {self.stats['skipped']:6,} images")
        
        # Check for imbalance
        if total > 0:
            print("\n📈 Class Distribution:")
            for category in ['plastic', 'paper', 'metal', 'organic', 'electronic']:
                percentage = (self.stats[category] / total) * 100
                status = "✅" if percentage > 10 else "⚠️"
                print(f"  {status} {category}: {percentage:.1f}%")
        
        print("\n✅ Dataset remapping complete!")
        print(f"\nUnified dataset location: {UNIFIED_DATA_DIR}")


if __name__ == "__main__":
    print("🚀 SatsVerdant Dataset Remapper")
    
    remapper = DatasetRemapper()
    
    # Remap all datasets
    remapper.remap_trashnet()
    remapper.remap_taco()
    remapper.remap_kaggle()
    
    # Print statistics
    remapper.print_statistics()
    
    print("\nNext step: python scripts/generate_synthetic.py")
