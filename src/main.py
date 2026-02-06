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


def process_single_image(image_path, config, resize_width, resize_height, db_path):
    """Process a single image

    Args:
        image_path: Path to the image file
        config: Configuration object
        resize_width: Target width for image resize
        resize_height: Target height for image resize
        db_path: Path to database file (each thread creates its own connection)

    Returns:
        tuple: (image_path, success: bool, error: str or None)
    """
    # Each thread must create its own database connection
    # SQLite connections cannot be shared across threads
    db = Database(db_path)
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
    finally:
        # Always close the database connection
        db.close()


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
    all_image_files = get_image_files(config.image_path)
    if not all_image_files:
        print("No image files found")
        sys.exit(1)

    print(f"Found {len(all_image_files)} image files")

    # Filter out already processed images if not in reprocess mode
    if not config.reprocess:
        from src.utils import generate_unique_id
        db = Database(config.db_path)

        unprocessed_files = []
        for image_file in all_image_files:
            image_id = generate_unique_id(image_file)
            existing_tags = db.get_tags_by_image_id(image_id)
            if not existing_tags:
                unprocessed_files.append(image_file)

        db.close()

        processed_count_before = len(all_image_files) - len(unprocessed_files)
        print(f"  Already processed: {processed_count_before}")
        print(f"  To process: {len(unprocessed_files)}")

        image_files = unprocessed_files
    else:
        print(f"  Reprocess mode: will process all images")
        image_files = all_image_files

    # Apply batch size limit (only to images that will be processed)
    if len(image_files) > config.batch_size:
        print(f"\nBatch size limit: processing first {config.batch_size} images")
        print(f"  Remaining: {len(image_files) - config.batch_size} images")
        print(f"  Tip: Run again to process the next batch")
        image_files = image_files[:config.batch_size]

    if not image_files:
        print("\nAll images already processed. Use --reprocess to force reprocess.")
        sys.exit(0)

    print(f"\nWill process: {len(image_files)} images")
    print()

    # Parse resize dimensions
    resize_width, resize_height = config.get_resize_dimensions()

    # Process images with parallel workers
    # Note: Each worker thread will create its own database connection
    # to avoid SQLite threading issues
    processed_count = 0
    failed_count = 0

    if config.max_workers == 1:
        # Serial processing (no parallelism)
        with tqdm(total=len(image_files), desc="Processing", unit="img") as pbar:
            for image_path in image_files:
                _, success, error = process_single_image(
                    image_path, config, resize_width, resize_height, config.db_path
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
                    config.db_path  # Pass db_path, not db object
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
    print(f"Total files found: {len(all_image_files)}")
    print(f"Files in this batch: {len(image_files)}")
    print(f"Successfully processed: {processed_count}")
    print(f"Failed: {failed_count}")
    print(f"Database location: {Path(config.db_path).resolve()}")


if __name__ == "__main__":
    main()