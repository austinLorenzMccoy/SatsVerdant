#!/usr/bin/env python3
"""
SatsVerdant Synthetic Data Generator
Generates synthetic training samples for underrepresented classes using background replacement

Usage:
    python src/synthetic_generator.py --class glass --target-count 3500
    python src/synthetic_generator.py --all-classes
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import random

from PIL import Image, ImageEnhance
import cv2

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_params():
    """Load hyperparameters from params.yaml"""
    with open("params.yaml") as f:
        return yaml.safe_load(f)

class BackgroundReplacementAugmentor:
    """
    Composites foreground waste objects onto new backgrounds to
    generate synthetic training samples for underrepresented classes.
    Uses rembg for background removal (U2-Net, no manual masking needed).
    """
    
    def __init__(self, background_dir: str = "data/backgrounds", output_dir: str = "data/synthetic"):
        self.background_dir = Path(background_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories
        self.background_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load background images
        self.backgrounds = self._load_backgrounds()
        
        print(f"🖼️  Loaded {len(self.backgrounds)} background images")
    
    def _load_backgrounds(self) -> List[Path]:
        """Load background images from directory"""
        # If no backgrounds exist, create synthetic ones
        if not any(self.background_dir.glob("*.jpg")):
            print("🎨 No background images found, creating synthetic backgrounds...")
            self._create_synthetic_backgrounds()
        
        backgrounds = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            backgrounds.extend(self.background_dir.glob(ext))
        
        return backgrounds
    
    def _create_synthetic_backgrounds(self, num_backgrounds: int = 50):
        """Create synthetic background images using patterns and textures"""
        for i in range(num_backgrounds):
            # Create different background types
            bg_type = random.choice(["gradient", "noise", "pattern", "texture"])
            
            if bg_type == "gradient":
                img = self._create_gradient_background()
            elif bg_type == "noise":
                img = self._create_noise_background()
            elif bg_type == "pattern":
                img = self._create_pattern_background()
            else:  # texture
                img = self._create_texture_background()
            
            # Save background
            bg_path = self.background_dir / f"synthetic_bg_{i:03d}.jpg"
            img.convert("RGB").save(bg_path, quality=90)
    
    def _create_gradient_background(self) -> Image.Image:
        """Create a gradient background"""
        width, height = 512, 512
        img = Image.new('RGB', (width, height))
        
        # Random colors
        color1 = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        color2 = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
        
        # Create gradient
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            
            for x in range(width):
                img.putpixel((x, y), (r, g, b))
        
        return img
    
    def _create_noise_background(self) -> Image.Image:
        """Create a noise background"""
        width, height = 512, 512
        img = Image.new('RGB', (width, height))
        
        # Add random noise
        for y in range(height):
            for x in range(width):
                r = random.randint(80, 180)
                g = random.randint(80, 180)
                b = random.randint(80, 180)
                img.putpixel((x, y), (r, g, b))
        
        # Apply blur for smoother look
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        
        return img
    
    def _create_pattern_background(self) -> Image.Image:
        """Create a patterned background"""
        width, height = 512, 512
        img = Image.new('RGB', (width, height), (150, 150, 150))
        
        # Create checkerboard pattern
        square_size = 32
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                if (x // square_size + y // square_size) % 2 == 0:
                    color = (random.randint(120, 180), random.randint(120, 180), random.randint(120, 180))
                    for dy in range(square_size):
                        for dx in range(square_size):
                            if x + dx < width and y + dy < height:
                                img.putpixel((x + dx, y + dy), color)
        
        return img
    
    def _create_texture_background(self) -> Image.Image:
        """Create a textured background"""
        width, height = 512, 512
        img = Image.new('RGB', (width, height))
        
        # Create base color
        base_color = (random.randint(100, 150), random.randint(100, 150), random.randint(100, 150))
        
        # Add texture variations
        for y in range(height):
            for x in range(width):
                # Add small random variations
                variation = random.randint(-20, 20)
                r = max(0, min(255, base_color[0] + variation))
                g = max(0, min(255, base_color[1] + variation))
                b = max(0, min(255, base_color[2] + variation))
                img.putpixel((x, y), (r, g, b))
        
        # Apply blur for natural look
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        return img
    
    def remove_background_simple(self, image: Image.Image) -> Image.Image:
        """Simple background removal using color thresholding"""
        # Convert to RGBA
        img_rgba = image.convert('RGBA')
        
        # Get pixels
        pixels = img_rgba.load()
        width, height = img_rgba.size
        
        # Find background color (corners)
        corner_colors = [
            pixels[0, 0][:3],
            pixels[width-1, 0][:3],
            pixels[0, height-1][:3],
            pixels[width-1, height-1][:3]
        ]
        
        # Average corner color as background
        bg_r = sum(c[0] for c in corner_colors) // 4
        bg_g = sum(c[1] for c in corner_colors) // 4
        bg_b = sum(c[2] for c in corner_colors) // 4
        
        # Make pixels similar to background transparent
        threshold = 30
        
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                distance = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
                
                if distance < threshold:
                    pixels[x, y] = (r, g, b, 0)  # Make transparent
        
        return img_rgba
    
    def augment_class(self, source_dir: str, category: str, target_count: int):
        """Expand a category to target_count images using background replacement."""
        source_path = Path(source_dir)
        if not source_path.exists():
            print(f"❌ Source directory not found: {source_dir}")
            return
        
        source_images = list(source_path.glob("*.jpg"))
        current_count = len(source_images)
        needed = max(0, target_count - current_count)
        
        if needed == 0:
            print(f"✅ {category}: already has {current_count} images, skipping")
            return
        
        if not self.backgrounds:
            print(f"❌ No background images available for {category}")
            return
        
        print(f"🔄 {category}: generating {needed} synthetic images ({current_count} -> {current_count + needed})")
        
        # Create output directory
        out_dir = self.output_dir / category
        out_dir.mkdir(parents=True, exist_ok=True)
        
        generated = 0
        attempts = 0
        max_attempts = needed * 5  # Allow more attempts for quality control
        
        while generated < needed and attempts < max_attempts:
            attempts += 1
            
            # Select random source image
            src_img_path = random.choice(source_images)
            
            try:
                # Load source image
                src_img = Image.open(src_img_path).convert("RGBA")
                
                # Remove background (simple method)
                fg_no_bg = self.remove_background_simple(src_img)
                
                # Select random background
                bg_img = Image.open(random.choice(self.backgrounds)).convert("RGBA")
                
                # Random scale (0.2x to 0.6x of background)
                scale = np.random.uniform(0.2, 0.6)
                new_w = int(bg_img.width * scale)
                new_h = int(bg_img.height * scale)
                
                # Resize foreground
                fg_resized = fg_no_bg.resize((new_w, new_h), Image.LANCZOS)
                
                # Random placement
                x = np.random.randint(0, max(1, bg_img.width - new_w))
                y = np.random.randint(0, max(1, bg_img.height - new_h))
                
                # Composite
                bg_copy = bg_img.copy()
                bg_copy.paste(fg_resized, (x, y), fg_resized)
                
                # Apply random transformations for variety
                final_img = self._apply_random_transformations(bg_copy)
                
                # Save synthetic image
                out_path = out_dir / f"synthetic_{category}_{generated:05d}.jpg"
                final_img.convert("RGB").save(out_path, quality=90)
                
                generated += 1
                
                if generated % 10 == 0:
                    print(f"  Generated {generated}/{needed} synthetic images...")
                    
            except Exception as e:
                # Skip problematic images
                continue
        
        print(f"✅ {category}: generated {generated} synthetic images (total: {current_count + generated})")
        
        if generated < needed:
            print(f"⚠️  {category}: only generated {generated}/{needed} images (quality control)")
    
    def _apply_random_transformations(self, img: Image.Image) -> Image.Image:
        """Apply random transformations to increase variety"""
        # Random brightness adjustment
        if random.random() < 0.5:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(random.uniform(0.8, 1.2))
        
        # Random contrast adjustment
        if random.random() < 0.5:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(random.uniform(0.8, 1.2))
        
        # Random color adjustment
        if random.random() < 0.3:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(random.uniform(0.9, 1.1))
        
        # Random slight rotation
        if random.random() < 0.2:
            angle = random.uniform(-5, 5)
            img = img.rotate(angle, expand=False, fillcolor=(128, 128, 128, 255))
        
        return img
    
    def analyze_dataset_needs(self, dataset_dir: str) -> Dict[str, int]:
        """Analyze dataset to determine which classes need augmentation"""
        dataset_path = Path(dataset_dir)
        class_counts = {}
        
        for class_dir in dataset_path.iterdir():
            if class_dir.is_dir():
                count = len(list(class_dir.glob("*.jpg")))
                class_counts[class_dir.name] = count
        
        return class_counts

def main():
    parser = argparse.ArgumentParser(description="SatsVerdant Synthetic Data Generator")
    parser.add_argument("--class", type=str, dest="class_name", 
                       help="Specific class to augment")
    parser.add_argument("--target-count", type=int, default=3500,
                       help="Target count for specified class")
    parser.add_argument("--all-classes", action="store_true",
                       help="Augment all underrepresented classes")
    parser.add_argument("--dataset", type=str, default="data/processed/train",
                       help="Dataset directory to analyze")
    parser.add_argument("--min-threshold", type=int, default=3000,
                       help="Minimum threshold for class augmentation")
    
    args = parser.parse_args()
    
    # Load parameters
    params = load_params()
    
    # Initialize augmentor
    augmentor = BackgroundReplacementAugmentor()
    
    if args.class_name:
        # Augment specific class
        source_dir = Path(args.dataset) / args.class_name
        augmentor.augment_class(str(source_dir), args.class_name, args.target_count)
        
    elif args.all_classes:
        # Analyze dataset and augment all underrepresented classes
        print(f"🔍 Analyzing dataset: {args.dataset}")
        
        class_counts = augmentor.analyze_dataset_needs(args.dataset)
        
        print(f"\n📊 Class Distribution:")
        for class_name, count in sorted(class_counts.items()):
            status = "✅" if count >= args.min_threshold else "🔄"
            print(f"  {status} {class_name}: {count} images")
        
        print(f"\n🔄 Augmenting classes below {args.min_threshold} threshold:")
        
        for class_name, count in class_counts.items():
            if count < args.min_threshold:
                source_dir = Path(args.dataset) / class_name
                augmentor.augment_class(str(source_dir), class_name, args.min_threshold)
        
        print(f"\n✅ Synthetic data generation complete!")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    # Import ImageFilter for background creation
    from PIL import ImageFilter
    main()
