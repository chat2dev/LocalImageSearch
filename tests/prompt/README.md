# Prompt Testing

Tests for validating prompt quality and tag generation.

## Test Scripts

### `test_tag_generation.py`
Automated test to verify that models output clean comma-separated tags without reasoning process.

**What it tests:**
- Tags don't contain reasoning keywords ("Okay", "let's see", etc.)
- Tags don't start with reasoning phrases
- Tags have reasonable length (not full sentences)
- Sufficient number of tags generated
- Works across multiple languages (en, zh, ja, ko)

**Usage:**
```bash
# Run tests using images from ~/Downloads
cd /path/to/LocalImageSearch
python tests/prompt/test_tag_generation.py

# Or with uv
uv run python tests/prompt/test_tag_generation.py
```

**Requirements:**
- At least a few images in `~/Downloads` directory
- Database initialized at `~/.LocalImageSearch/data/image_tags.db`

### `generate_test_images.py`
Generates synthetic test images for prompt testing.

**Usage:**
```bash
# Generate test images
python tests/prompt/generate_test_images.py

# Images will be created in tests/prompt/test_images/
```

**Generated images:**
1. `test_colored_rectangles.jpg` - Simple colored shapes
2. `test_gradient_shapes.jpg` - Gradient background with shapes
3. `test_text_image.jpg` - Image with text
4. `test_color_stripes.jpg` - Multi-color pattern
5. `test_geometric_pattern.jpg` - Grid of geometric shapes

## Test Workflow

### Option 1: Use real images from Downloads
```bash
# Just run the test (uses random images from ~/Downloads)
python tests/prompt/test_tag_generation.py
```

### Option 2: Use generated test images
```bash
# Generate synthetic images
python tests/prompt/generate_test_images.py

# Test with generated images
uv run python src/main.py \
  --image-path tests/prompt/test_images/ \
  --language en \
  --tag-count 10

# Run validation
python tests/prompt/test_tag_generation.py
```

## Expected Results

### ✅ PASS Example
```
Tags: colored rectangles, geometric shapes, digital art, flat design, blue background, red square, border outline, graphic design, vector style, minimalist composition
```

### ❌ FAIL Example (contains reasoning)
```
Tags: Okay, let's see. The user wants me to list 10 tags for this image. First, I need to analyze what's in the image. It appears to be...
```

## Test Output

```
======================================================================
Prompt Tag Generation Quality Test
======================================================================
Test started at: 2025-02-05 20:30:00

Looking for test images in: /Users/user/Downloads
✓ Found 3 test images
  - photo1.jpg
  - screenshot.png
  - diagram.jpg

Testing language: EN
----------------------------------------------------------------------
[1/12] photo1.jpg... ✓ PASS
[2/12] screenshot.png... ✓ PASS
[3/12] diagram.jpg... ✗ FAIL
    Issue: Contains reasoning keyword: 'Okay,'

...

======================================================================
Test Summary
======================================================================
Total tests: 12
Successful: 12 (100.0%)
  Clean tags: 11 (91.7%)
  Dirty tags (with reasoning): 1 (8.3%)
Failed/Error: 0 (0.0%)
```

## Troubleshooting

### Test fails with "No images found"
- Add some images to `~/Downloads` directory
- Or use `generate_test_images.py` to create test images

### Tags still contain reasoning process
- Check `prompts.yaml` configuration
- Ensure system prompts explicitly forbid reasoning
- Try adjusting model temperature (if supported)

### Database not found error
- Run `uv run python scripts/init_database.py` first
- Ensure database exists at `~/.LocalImageSearch/data/image_tags.db`
