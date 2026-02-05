#!/usr/bin/env python3
"""
Image auto-tagging system main entry point
"""
import sys
from pathlib import Path
from tqdm import tqdm
from src.cli_config import Config
from src.utils import get_image_files
from src.tagging import process_image
from src.db_manager import Database


def main():
    """Main function"""
    config = Config()
    config.parse_args()

    print("=" * 60)
    print("Image Auto-Tagging System")
    print("=" * 60)
    print(config)
    print("=" * 60)

    # Get image files
    image_files = get_image_files(config.image_path)
    if not image_files:
        print("No image files found")
        sys.exit(1)

    print(f"Found {len(image_files)} image files")
    print()

    # Parse resize dimensions
    resize_width, resize_height = config.get_resize_dimensions()

    # Initialize database
    db = Database(config.db_path)

    # Process images
    processed_count = 0
    failed_count = 0

    with tqdm(total=len(image_files), desc="Processing", unit="img") as pbar:
        for image_path in image_files:
            try:
                if process_image(
                    image_path=image_path,
                    model_name=config.model,
                    resize_width=resize_width,
                    resize_height=resize_height,
                    tag_count=config.tag_count,
                    generate_description=config.generate_description,
                    db=db,
                    language=config.language,
                    model_type=config.model_type,
                    api_base=config.api_base,
                    api_key=config.api_key,
                    force_reprocess=config.reprocess,
                    prompt_config_path=config.prompt_config_path
                ):
                    processed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                failed_count += 1
            pbar.update(1)

    db.close()

    # Build index (inverted index + FTS5 full-text search)
    from src.index_builder import IndexBuilder

    print("\nUpdating indexes...")
    index_builder = IndexBuilder(config.db_path)
    index_stats = index_builder.build()
    index_builder.close()
    print(f"Index update complete: inverted index {index_stats['tag_index_rows']} rows, "
          f"full-text index {index_stats['fts_index_rows']} rows")

    # Output statistics
    print()
    print("=" * 60)
    print("Processing complete")
    print("=" * 60)
    print(f"Total files: {len(image_files)}")
    print(f"Successfully processed: {processed_count}")
    print(f"Failed: {failed_count}")
    print(f"Database location: {Path(config.db_path).resolve()}")


if __name__ == "__main__":
    main()