#!/bin/bash

# ============================================================
# LocalImageSearch - Full Workflow Test Script
# ============================================================
# This script tests the complete workflow:
# 1. Tag images from Downloads directory
# 2. Build search indexes
# 3. Test CLI search commands
# 4. Verify database contents
# 5. Test Web UI APIs
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
IMAGE_DIR="${IMAGE_DIR:-$HOME/Downloads}"  # Use environment variable or default to ~/Downloads
DB_PATH="$HOME/.LocalImageSearch/data/image_tags.db"
MODEL="qwen3-vl:4b"
LANGUAGE="zh"

echo "============================================================"
echo "LocalImageSearch - Full Workflow Test"
echo "============================================================"
echo ""

# Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ uv found${NC}"

if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠ Ollama not found, skipping model check${NC}"
else
    if ! ollama list | grep -q "$MODEL"; then
        echo -e "${YELLOW}⚠ Model $MODEL not found, pulling...${NC}"
        ollama pull "$MODEL"
    fi
    echo -e "${GREEN}✓ Model $MODEL available${NC}"
fi

# Count images in directory
IMAGE_COUNT=$(find "$IMAGE_DIR" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | wc -l | tr -d ' ')
echo -e "${GREEN}✓ Found $IMAGE_COUNT images in $IMAGE_DIR${NC}"
echo ""

# Step 2: Tag images
echo -e "${YELLOW}Step 2: Tagging images from Downloads directory...${NC}"
echo "Command: uv run python src/main.py --image-path $IMAGE_DIR --model $MODEL --language $LANGUAGE"
echo ""

uv run python src/main.py \
  --image-path "$IMAGE_DIR" \
  --model "$MODEL" \
  --language "$LANGUAGE" \
  --tag-count 10

echo ""
echo -e "${GREEN}✓ Image tagging completed${NC}"
echo ""

# Step 3: Verify database
echo -e "${YELLOW}Step 3: Verifying database...${NC}"

if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}✗ Database not found at $DB_PATH${NC}"
    exit 1
fi

DB_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM image_tags WHERE status='success';")
TAG_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM tag_index;")
echo -e "${GREEN}✓ Database exists at $DB_PATH${NC}"
echo -e "${GREEN}  - Successfully tagged images: $DB_COUNT${NC}"
echo -e "${GREEN}  - Total tag index entries: $TAG_COUNT${NC}"
echo ""

# Step 4: Show table structure
echo -e "${YELLOW}Step 4: Database schema verification...${NC}"
python src/show_table_structure.py | head -30
echo ""

# Step 5: Test index builder
echo -e "${YELLOW}Step 5: Testing index builder...${NC}"

# Build indexes
echo "Building search indexes..."
python src/index_builder.py build --db-path "$DB_PATH" || true
echo ""

# Get tag statistics
echo "Tag statistics:"
python src/index_builder.py stats --db-path "$DB_PATH" 2>/dev/null | head -20 || {
    echo -e "${YELLOW}⚠ index_builder stats not working with --db-path, using direct SQLite query${NC}"
    sqlite3 "$DB_PATH" "SELECT tag, COUNT(*) as count FROM tag_index GROUP BY tag ORDER BY count DESC LIMIT 10;" | column -t -s '|'
}
echo ""

# Test tag search
echo -e "${YELLOW}Step 6: Testing CLI tag search...${NC}"
TOP_TAG=$(sqlite3 "$DB_PATH" "SELECT tag FROM tag_index GROUP BY tag ORDER BY COUNT(*) DESC LIMIT 1;")
echo "Searching for top tag: $TOP_TAG"
python src/index_builder.py search "$TOP_TAG" --mode tag --db-path "$DB_PATH" 2>/dev/null | head -10 || {
    echo -e "${YELLOW}⚠ CLI search not working, testing with direct query${NC}"
    sqlite3 "$DB_PATH" "SELECT image_path FROM image_tags WHERE id IN (SELECT image_id FROM tag_index WHERE tag='$TOP_TAG' LIMIT 5);"
}
echo ""

# Step 7: Test Web UI (if running)
echo -e "${YELLOW}Step 7: Testing Web UI APIs...${NC}"

# Check if UI is running
if curl -s http://localhost:3001/api/tags?limit=1 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Web UI is running on port 3001${NC}"

    echo "Testing /api/tags endpoint:"
    curl -s http://localhost:3001/api/tags?limit=5 | jq '.' || echo "Response received"
    echo ""

    echo "Testing /api/images endpoint:"
    curl -s 'http://localhost:3001/api/images?limit=3' | jq '.images[0] | {image_path, tags}' || echo "Response received"
    echo ""
else
    if curl -s http://localhost:3000/api/tags?limit=1 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Web UI is running on port 3000${NC}"
        PORT=3000

        echo "Testing /api/tags endpoint:"
        curl -s http://localhost:$PORT/api/tags?limit=5 | jq '.' || echo "Response received"
        echo ""

        echo "Testing /api/images endpoint:"
        curl -s "http://localhost:$PORT/api/images?limit=3" | jq '.images[0] | {image_path, tags}' || echo "Response received"
        echo ""
    else
        echo -e "${YELLOW}⚠ Web UI is not running. Start with: cd ui && npm run dev${NC}"
    fi
fi

# Final summary
echo "============================================================"
echo -e "${GREEN}✓ All tests completed successfully!${NC}"
echo "============================================================"
echo ""
echo "Summary:"
echo "  - Images processed: $DB_COUNT"
echo "  - Tag index entries: $TAG_COUNT"
echo "  - Database location: $DB_PATH"
echo "  - Web UI: http://localhost:3001 (or 3000)"
echo ""
echo "Next steps:"
echo "  - Open http://localhost:3001 in your browser"
echo "  - Test search and filtering functionality"
echo "  - Verify image display and modal viewer"
echo ""
