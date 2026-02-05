#!/usr/bin/env python3
"""
Display image annotation table structure information
"""
from src.db_manager import Database
import sys
from pathlib import Path


def show_table_structure():
    """Display table structure"""
    # Default DB path
    db_path = "./data/image_tags.db"

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print("=" * 60)
    print("Image Auto-Tagging System - Table Structure")
    print("=" * 60)
    print()

    # Initialize database
    try:
        db = Database(db_path)
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    print("Table structure: image_tags")
    print("-" * 60)

    # Query table structure
    db.cursor.execute("PRAGMA table_info(image_tags)")
    columns = db.cursor.fetchall()

    print(f"{'Field':<20} {'Type':<15} {'Not Null':<8} {'Default':<20} {'Description'}")
    print("-" * 100)

    field_descriptions = {
        "id": "Auto-increment primary key",
        "image_unique_id": "Unique image ID (SHA-256 hash based on path)",
        "image_path": "Image file path",
        "tags": "Annotation tags (comma-separated string)",
        "description": "Image description (optional)",
        "model_name": "Model name used",
        "image_size": "Image size during processing (format: width x height)",
        "tag_count": "Tag count",
        "generated_at": "Annotation timestamp (defaults to current time)",
        "original_width": "Original width",
        "original_height": "Original height",
        "image_format": "Image format (JPEG/PNG/BMP etc.)",
        "status": "Annotation status (success/failed/processing)",
        "error_message": "Error message (recorded on failure)",
        "processing_time": "Processing time (milliseconds)"
    }

    for column in columns:
        cid, name, type_str, notnull, dflt_value, pk = column
        notnull_str = "Yes" if notnull else "No"
        dflt_str = str(dflt_value) if dflt_value else ""
        description = field_descriptions.get(name, "")
        print(f"{name:<20} {type_str:<15} {notnull_str:<8} {dflt_str:<20} {description}")

    print()
    print("Index information:")
    print("-" * 60)

    # Query index information
    db.cursor.execute("PRAGMA index_list(image_tags)")
    indexes = db.cursor.fetchall()

    if indexes:
        print(f"{'Index Name':<30} {'Unique':<10} {'Columns'}")
        print("-" * 80)
        for idx in indexes:
            idx_id, name, unique, origin, partial = idx
            unique_str = "Yes" if unique else "No"
            # Get index columns
            db.cursor.execute(f"PRAGMA index_info({name})")
            fields = []
            for info in db.cursor.fetchall():
                seqno, cid, name = info
                fields.append(name)
            field_list = ", ".join(fields)
            print(f"{name:<30} {unique_str:<10} {field_list}")
    else:
        print("No indexes created")

    print()
    print(f"Database file location: {Path(db_path).resolve()}")

    # Data statistics
    count = db.count_tags()
    print(f"Current record count: {count}")

    # Check if there is data
    if count > 0:
        print()
        print("Sample data (first 5 rows):")
        print("-" * 60)
        db.cursor.execute("SELECT id, image_unique_id, image_path, tag_count, status, generated_at FROM image_tags LIMIT 5")
        samples = db.cursor.fetchall()
        print(f"{'ID':<5} {'Unique ID':<12} {'Image Path':<40} {'Tags':<5} {'Status':<8} {'Time'}")
        print("-" * 100)
        for sample in samples:
            id_val, unique_id, img_path, tag_count, status, gen_time = sample
            # Truncate for display
            truncated_path = img_path if len(img_path) <= 40 else "..." + img_path[-37:]
            truncated_id = unique_id[:8] + "..."
            print(f"{id_val:<5} {truncated_id:<12} {truncated_path:<40} {tag_count:<5} {status:<8} {gen_time}")

    db.close()


if __name__ == "__main__":
    show_table_structure()