#!/usr/bin/env python3
"""
Script to extract all image file paths in a directory
"""
import argparse
from pathlib import Path
from typing import List


def get_image_files(directory: str, recursive: bool = True) -> List[str]:
    """
    Get all image files in a directory

    Args:
        directory: Directory path
        recursive: Whether to recursively search subdirectories

    Returns:
        List of image file paths
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
    directory_path = Path(directory)
    image_files = []

    if not directory_path.exists():
        print(f"Error: Directory does not exist: {directory}")
        return []

    if directory_path.is_dir():
        if recursive:
            # Recursively search all subdirectories
            for ext in image_extensions:
                image_files.extend(directory_path.rglob(f"*{ext}"))
                image_files.extend(directory_path.rglob(f"*{ext.upper()}"))
        else:
            # Search current directory only
            for ext in image_extensions:
                image_files.extend(directory_path.glob(f"*{ext}"))
                image_files.extend(directory_path.glob(f"*{ext.upper()}"))
    elif directory_path.is_file() and directory_path.suffix.lower() in image_extensions:
        image_files.append(directory_path)

    return sorted([str(file.resolve()) for file in image_files])


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Extract all image file paths from a specified directory"
    )
    parser.add_argument(
        "--directory",
        type=str,
        required=True,
        help="Directory path to search"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="image_paths.txt",
        help="Output file path (default: image_paths.txt)"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not recursively search subdirectories"
    )
    parser.add_argument(
        "--relative",
        action="store_true",
        help="Save relative paths instead of absolute paths"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Image Path Extraction Tool")
    print("=" * 60)
    print(f"Search directory: {args.directory}")
    print(f"Recursive search: {'No' if args.no_recursive else 'Yes'}")
    print(f"Output file: {args.output}")
    print(f"Path type: {'Relative' if args.relative else 'Absolute'}")
    print("=" * 60)

    # Get image file list
    image_files = get_image_files(args.directory, not args.no_recursive)

    if not image_files:
        print("No image files found")
        return

    print(f"Found {len(image_files)} image files")

    # Process path format
    if args.relative:
        base_path = Path(args.directory).resolve()
        processed_files = []
        for file_path in image_files:
            try:
                rel_path = Path(file_path).relative_to(base_path)
                processed_files.append(str(rel_path))
            except ValueError:
                # If relative path cannot be computed, use absolute path
                processed_files.append(file_path)
        image_files = processed_files

    # Write to output file
    output_path = Path(args.output)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for file_path in image_files:
                f.write(f"{file_path}\n")

        print(f"\nSuccessfully saved {len(image_files)} image paths to: {output_path.resolve()}")

        # Show a few paths as examples
        print("\nFirst 10 image paths:")
        print("-" * 60)
        for file_path in image_files[:10]:
            print(file_path)

        if len(image_files) > 10:
            print("...")
            print(f"({len(image_files) - 10} more files)")

    except Exception as e:
        print(f"Error: Cannot write to file {args.output}: {e}")
        return

    print("\n" + "=" * 60)
    print("Done")
    print("=" * 60)


if __name__ == "__main__":
    main()
