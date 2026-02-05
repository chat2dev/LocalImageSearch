#!/bin/bash
# Database initialization script
# Creates a fresh database with the latest schema if it doesn't exist

set -e

DB_PATH="${DB_PATH:-/app/data/image_tags.db}"

echo "Checking database at: $DB_PATH"

if [ ! -f "$DB_PATH" ]; then
    echo "Database not found. Initializing with latest schema..."
    python3 -c "
from src.db_manager import Database
import sys

try:
    db = Database('$DB_PATH')
    db.close()
    print('✓ Database initialized successfully')
    sys.exit(0)
except Exception as e:
    print(f'✗ Database initialization failed: {e}')
    sys.exit(1)
"
else
    echo "✓ Database already exists"
fi
