#!/usr/bin/env python3
"""
Generate synthetic test images for prompt testing
Creates simple images with text, shapes, and colors
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Test output directory
OUTPUT_DIR = Path(__file__).parent / "test_images"


def create_test_images():
    """Generate various test images"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    images_created = []

    # Test 1: Simple colored rectangles
    img = Image.new('RGB', (800, 600), color='#3498db')
    draw = ImageDraw.Draw(img)
    draw.rectangle([200, 150, 600, 450], fill='#e74c3c', outline='#2c3e50', width=5)
    output_path = OUTPUT_DIR / "test_colored_rectangles.jpg"
    img.save(output_path, quality=95)
    images_created.append(output_path)
    print(f"✓ Created: {output_path.name}")

    # Test 2: Gradient background with shapes
    img = Image.new('RGB', (800, 600))
    pixels = img.load()
    for y in range(600):
        for x in range(800):
            pixels[x, y] = (int(255 * x / 800), int(255 * y / 600), 128)

    draw = ImageDraw.Draw(img)
    draw.ellipse([300, 200, 500, 400], fill='white', outline='black', width=3)
    output_path = OUTPUT_DIR / "test_gradient_shapes.jpg"
    img.save(output_path, quality=95)
    images_created.append(output_path)
    print(f"✓ Created: {output_path.name}")

    # Test 3: Simple text image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a font, fallback to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
    except:
        font = ImageFont.load_default()

    draw.text((100, 250), "TEST IMAGE", fill='black', font=font)
    draw.rectangle([50, 50, 750, 550], outline='red', width=10)

    output_path = OUTPUT_DIR / "test_text_image.jpg"
    img.save(output_path, quality=95)
    images_created.append(output_path)
    print(f"✓ Created: {output_path.name}")

    # Test 4: Multi-color pattern
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    for i, color in enumerate(colors):
        x = i * 160
        draw.rectangle([x, 0, x + 160, 600], fill=color)

    output_path = OUTPUT_DIR / "test_color_stripes.jpg"
    img.save(output_path, quality=95)
    images_created.append(output_path)
    print(f"✓ Created: {output_path.name}")

    # Test 5: Geometric patterns
    img = Image.new('RGB', (800, 600), color='#f0f0f0')
    draw = ImageDraw.Draw(img)

    # Draw grid of circles
    for row in range(4):
        for col in range(5):
            x = 80 + col * 160
            y = 75 + row * 150
            color = '#' + format((row * 5 + col) * 10, '02x') * 3
            draw.ellipse([x-50, y-50, x+50, y+50], fill=color, outline='black', width=2)

    output_path = OUTPUT_DIR / "test_geometric_pattern.jpg"
    img.save(output_path, quality=95)
    images_created.append(output_path)
    print(f"✓ Created: {output_path.name}")

    return images_created


def main():
    """Generate test images"""
    print("=" * 70)
    print("Generating Test Images for Prompt Testing")
    print("=" * 70)
    print()

    images = create_test_images()

    print()
    print("=" * 70)
    print(f"Generated {len(images)} test images in: {OUTPUT_DIR}")
    print("=" * 70)
    print()
    print("You can now run:")
    print(f"  python tests/prompt/test_tag_generation.py")
    print()
    print("Or test manually:")
    for img in images:
        print(f"  uv run python src/main.py --image-path {img} --language en")

    return 0


if __name__ == "__main__":
    sys.exit(main())
