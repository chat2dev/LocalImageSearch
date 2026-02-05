#!/usr/bin/env python3
"""
Image auto-tagging system main entry point
"""
import sys
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.cli_config import Config
from src.utils import get_image_files
from src.tagging import process_image
from src.db_manager import Database


def process_single_image(image_path, config, resize_width, resize_height, db):
    """Process a single image

    Args:
        image_path: Path to the image file
        config: Configuration object
        resize_width: Target width for image resize
        resize_height: Target height for image resize
        db: Database instance

    Returns:
        tuple: (image_path, success: bool, error: str or None)
    """
    try:
        success = process_image(
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
        )
        return (image_path, success, None)
    except Exception as e:
        return (image_path, False, str(e))


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

    # Process images with parallel workers
    processed_count = 0
    failed_count = 0

    if config.max_workers == 1:
        # Serial processing (no parallelism)
        with tqdm(total=len(image_files), desc="Processing", unit="img") as pbar:
            for image_path in image_files:
                _, success, error = process_single_image(
                    image_path, config, resize_width, resize_height, db
                )
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
                    if error:
                        print(f"\nError processing {image_path}: {error}")
                pbar.update(1)
    else:
        # Parallel processing
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            # Submit all tasks
            future_to_image = {
                executor.submit(
                    process_single_image,
                    image_path,
                    config,
                    resize_width,
                    resize_height,
                    db
                ): image_path
                for image_path in image_files
            }

            # Process completed tasks with progress bar
            with tqdm(total=len(image_files), desc="Processing", unit="img") as pbar:
                for future in as_completed(future_to_image):
                    image_path, success, error = future.result()
                    if success:
                        processed_count += 1
                    else:
                        failed_count += 1
                        if error:
                            print(f"\nError processing {image_path}: {error}")
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