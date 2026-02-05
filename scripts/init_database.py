#!/usr/bin/env python3
"""
Database Initialization Script
Initializes the database schema without processing any images.
Use this before starting the Web UI if you haven't tagged any images yet.
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from db_manager import Database
from index_builder import IndexBuilder
import os

def init_database(db_path: str = None):
    """Initialize database with schema and indexes"""
    # Default database path
    if db_path is None:
        home_dir = Path.home()
        data_dir = home_dir / '.LocalImageSearch' / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(data_dir / 'image_tags.db')

    print(f"Initializing database at: {db_path}")
    print()

    # Create database with schema
    db = Database(db_path)
    print("✓ Created image_tags table")
    print("✓ Created database indexes")

    # Initialize search indexes
    index_builder = IndexBuilder(db_path)
    try:
        stats = index_builder.build()
        print(f"✓ Created inverted index (tag_index): {stats['tag_index_rows']} rows")
        print(f"✓ Created full-text index (image_fts): {stats['fts_index_rows']} rows")
    finally:
        index_builder.close()

    db.close()

    print()
    print("=" * 60)
    print("Database initialized successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Tag some images:")
    print(f"     uv run python src/main.py --image-path ~/Pictures")
    print()
    print("  2. Start Web UI:")
    print("     cd ui && npm run dev")
    print()
    print(f"Database location: {db_path}")
    print()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Initialize LocalImageSearch database'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        help='Database path (default: ~/.LocalImageSearch/data/image_tags.db)'
    )

    args = parser.parse_args()
    init_database(args.db_path)
