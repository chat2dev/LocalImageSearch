#!/usr/bin/env python3
"""
Test Doubao (豆包) vision model for image tagging

Requirements:
- DOUBAO_API_KEY and DOUBAO_BASE_URL must be set in environment
- For Doubao, model_name should be the endpoint ID (e.g., ep-xxxxx)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.model_factory import OpenAICompatibleModel, ModelAPIError
from src.image_processor import load_and_preprocess_image
from src.tagging import parse_tags


def test_doubao_api():
    """Test basic Doubao API connectivity"""
    api_key = os.getenv("DOUBAO_API_KEY")
    api_base = os.getenv("DOUBAO_BASE_URL")

    if not api_key or not api_base:
        print("❌ Error: DOUBAO_API_KEY and DOUBAO_BASE_URL must be set")
        print("   Please check your ~/.bashrc configuration")
        return False

    print("=" * 70)
    print("Doubao Configuration")
    print("=" * 70)
    print(f"API Base: {api_base}")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print()

    return True


def test_doubao_tagging(model_name: str, test_images: list, language: str = "zh", tag_count: int = 10):
    """
    Test Doubao vision model for image tagging

    Args:
        model_name: Doubao endpoint ID (e.g., ep-20250206174555-xxxxx)
        test_images: List of image file paths to test
        language: Language for tags (zh or en)
        tag_count: Number of tags to generate
    """
    api_key = os.getenv("DOUBAO_API_KEY")
    api_base = os.getenv("DOUBAO_BASE_URL")

    if not test_doubao_api():
        return

    print("=" * 70)
    print("Testing Doubao Image Tagging")
    print("=" * 70)
    print(f"Model/Endpoint: {model_name}")
    print(f"Language: {language}")
    print(f"Tag Count: {tag_count}")
    print(f"Test Images: {len(test_images)}")
    print()

    # Create Doubao model instance
    try:
        model = OpenAICompatibleModel(
            model_name=model_name,
            api_base=api_base,
            api_key=api_key,
            language=language
        )
        print("✓ Doubao model initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Doubao model: {e}")
        return

    # Test each image
    success_count = 0
    failure_count = 0

    for i, image_path in enumerate(test_images, 1):
        print()
        print("=" * 70)
        print(f"Test {i}/{len(test_images)}: {Path(image_path).name}")
        print("=" * 70)

        if not Path(image_path).exists():
            print(f"❌ Image not found: {image_path}")
            failure_count += 1
            continue

        try:
            # Load and preprocess image
            print("Loading image...")
            image_bytes = load_and_preprocess_image(image_path, 512, 512)

            if not image_bytes:
                print(f"❌ Failed to load image: {image_path}")
                failure_count += 1
                continue

            print(f"✓ Image loaded ({len(image_bytes)} bytes)")

            # Generate tags
            print(f"Generating {tag_count} tags using Doubao...")
            raw_tags = model.generate_tags(image_bytes, tag_count)

            # Parse tags from raw response
            tags = parse_tags(raw_tags, tag_count)

            if tags:
                print(f"✓ Successfully generated {len(tags)} tags:")
                for j, tag in enumerate(tags, 1):
                    print(f"  {j}. {tag}")
                success_count += 1
            else:
                print("❌ No tags generated")
                print(f"   Raw response: {raw_tags[:200]}")
                failure_count += 1

        except ModelAPIError as e:
            print(f"❌ Model API Error:")
            print(f"   Error Type: {e.error_type}")
            print(f"   Message: {str(e)}")
            if e.raw_response:
                print(f"   Details: {e.raw_response[:300]}")
            failure_count += 1

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            failure_count += 1

    # Summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total: {len(test_images)}")
    print(f"✓ Success: {success_count}")
    print(f"❌ Failed: {failure_count}")
    print(f"Success Rate: {success_count}/{len(test_images)} ({100*success_count/len(test_images):.1f}%)")
    print()


if __name__ == "__main__":
    import argparse

    # Get defaults from environment variables
    default_model = os.getenv("DOUBAO_MODEL_NAME", "")

    parser = argparse.ArgumentParser(description="Test Doubao vision model for image tagging")
    parser.add_argument(
        "--model",
        type=str,
        default=default_model,
        help=f"Doubao endpoint ID (default from DOUBAO_MODEL_NAME: {default_model or 'not set'})"
    )
    parser.add_argument(
        "--images",
        nargs="+",
        help="Image file paths to test (default: use test images)"
    )
    parser.add_argument(
        "--language",
        choices=["zh", "en", "ja", "ko"],
        default="zh",
        help="Language for tags (default: zh)"
    )
    parser.add_argument(
        "--tag-count",
        type=int,
        default=10,
        help="Number of tags to generate (default: 10)"
    )

    args = parser.parse_args()

    # Check if model is provided
    if not args.model:
        print("❌ Error: Doubao model name not provided")
        print("   Either:")
        print("   1. Set DOUBAO_MODEL_NAME in environment")
        print("   2. Use --model parameter")
        sys.exit(1)

    # Determine test images
    if args.images:
        test_images = args.images
    else:
        # Use default test images
        test_dir = Path(__file__).parent / "prompt" / "test_images"
        if test_dir.exists():
            test_images = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
            test_images = [str(p) for p in test_images[:3]]  # Test first 3 images
        else:
            print("❌ No test images found. Please specify --images")
            sys.exit(1)

    if not test_images:
        print("❌ No images to test. Please specify --images")
        sys.exit(1)

    # Run tests
    test_doubao_tagging(
        model_name=args.model,
        test_images=test_images,
        language=args.language,
        tag_count=args.tag_count
    )
