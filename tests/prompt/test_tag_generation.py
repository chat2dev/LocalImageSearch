#!/usr/bin/env python3
"""
Prompt Tag Generation Test
Tests that models output clean tags without reasoning process
"""
import sys
import os
import sqlite3
import random
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Test configuration
DOWNLOADS_DIR = Path.home() / "Downloads"
DB_PATH = Path.home() / ".LocalImageSearch" / "data" / "image_tags.db"
TEST_LANGUAGES = ["en", "zh", "ja", "ko"]
SAMPLE_SIZE = 3  # Test 3 images per language

# Reasoning keywords to check for (should NOT appear in clean tags)
REASONING_KEYWORDS = [
    "Okay,", "let's see", "First,", "I need", "The user",
    "looking at", "appears to be", "seems to", "probably",
    "I think", "maybe", "might be", "could be", "Let me"
]


def find_test_images(directory: Path, count: int = 5):
    """Find random image files from directory"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    all_images = [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not all_images:
        return []

    # Return random sample or all if fewer than requested
    sample_count = min(count, len(all_images))
    return random.sample(all_images, sample_count)


def check_tag_quality(tags: str, language: str) -> dict:
    """Check if tags are clean (no reasoning process)"""
    result = {
        "clean": True,
        "issues": [],
        "tag_count": len([t.strip() for t in tags.split(",") if t.strip()])
    }

    # Check for reasoning keywords
    tags_lower = tags.lower()
    for keyword in REASONING_KEYWORDS:
        if keyword.lower() in tags_lower:
            result["clean"] = False
            result["issues"].append(f"Contains reasoning keyword: '{keyword}'")

    # Check if starts with reasoning
    if any(tags.startswith(kw) for kw in ["Okay", "Let's", "First", "Looking"]):
        result["clean"] = False
        result["issues"].append("Starts with reasoning phrase")

    # Check tag count
    if result["tag_count"] < 2:
        result["clean"] = False
        result["issues"].append(f"Too few tags: {result['tag_count']}")

    # Check for overly long "tags" (likely full sentences)
    for tag in tags.split(","):
        if len(tag.strip()) > 100:
            result["clean"] = False
            result["issues"].append("Contains overly long tag (likely a sentence)")
            break

    return result


def run_tagging_test(image_path: Path, language: str) -> dict:
    """Run tagging on a single image and return results"""
    import subprocess

    cmd = [
        "uv", "run", "python", "src/main.py",
        "--image-path", str(image_path),
        "--language", language,
        "--tag-count", "10",
        "--reprocess"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Query database for result
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tags, status FROM image_tags
            WHERE image_path = ? AND language = ?
            ORDER BY generated_at DESC LIMIT 1
        """, (str(image_path), language))

        row = cursor.fetchone()
        conn.close()

        if row:
            tags, status = row
            quality = check_tag_quality(tags, language)
            return {
                "success": True,
                "tags": tags,
                "status": status,
                "quality": quality
            }
        else:
            return {
                "success": False,
                "error": "No database entry found"
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Run prompt quality tests"""
    print("=" * 70)
    print("Prompt Tag Generation Quality Test")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Find test images
    print(f"Looking for test images in: {DOWNLOADS_DIR}")
    test_images = find_test_images(DOWNLOADS_DIR, SAMPLE_SIZE)

    if not test_images:
        print(f"❌ No images found in {DOWNLOADS_DIR}")
        print("Please add some test images to ~/Downloads")
        return 1

    print(f"✓ Found {len(test_images)} test images")
    for img in test_images:
        print(f"  - {img.name}")
    print()

    # Run tests
    all_results = []
    total_tests = len(test_images) * len(TEST_LANGUAGES)
    current_test = 0

    for language in TEST_LANGUAGES:
        print(f"\nTesting language: {language.upper()}")
        print("-" * 70)

        for image_path in test_images:
            current_test += 1
            print(f"[{current_test}/{total_tests}] {image_path.name}...", end=" ")

            result = run_tagging_test(image_path, language)
            result["image"] = image_path.name
            result["language"] = language
            all_results.append(result)

            if result["success"]:
                if result["quality"]["clean"]:
                    print("✓ PASS")
                else:
                    print("✗ FAIL")
                    for issue in result["quality"]["issues"]:
                        print(f"    Issue: {issue}")
            else:
                print(f"✗ ERROR: {result.get('error', 'Unknown error')}")

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    total = len(all_results)
    successful = sum(1 for r in all_results if r["success"])
    clean = sum(1 for r in all_results if r.get("success") and r.get("quality", {}).get("clean"))
    failed = total - successful
    dirty = successful - clean

    print(f"Total tests: {total}")
    print(f"Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"  Clean tags: {clean} ({clean/total*100:.1f}%)")
    print(f"  Dirty tags (with reasoning): {dirty} ({dirty/total*100:.1f}%)")
    print(f"Failed/Error: {failed} ({failed/total*100:.1f}%)")
    print()

    # Show dirty examples
    if dirty > 0:
        print("Examples of dirty tags (with reasoning):")
        print("-" * 70)
        for r in all_results:
            if r.get("success") and not r.get("quality", {}).get("clean"):
                print(f"\nImage: {r['image']}")
                print(f"Language: {r['language']}")
                print(f"Tags: {r['tags'][:200]}...")
                print(f"Issues: {', '.join(r['quality']['issues'])}")

    print()
    if clean == successful == total:
        print("🎉 All tests passed! Tags are clean.")
        return 0
    else:
        print("⚠️  Some tests failed. Check prompts configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
