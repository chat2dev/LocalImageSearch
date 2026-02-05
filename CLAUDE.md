# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an image auto-tagging system (图片自动标注系统) that uses local vision-language models via Ollama to automatically generate tags and descriptions for images. The system processes images, generates tags using AI models, and stores the results in a SQLite database.

## Development Commands

### Environment Setup

```bash
# Initialize and sync virtual environment using uv (recommended)
uv sync

# This single command will:
# - Create a virtual environment (.venv) if it doesn't exist
# - Install all dependencies from pyproject.toml
# - Lock dependencies in uv.lock for reproducibility

# Activate virtual environment (optional, uv run works without activation)
source .venv/bin/activate  # macOS/Linux
# or on Windows: .venv\Scripts\activate

# Install development dependencies
uv sync --extra dev
```

### Running the Application

```bash
# Using Ollama (default) - recommended
uv run python src/main.py --image-path /path/to/images --model qwen3-vl:4b

# Using OpenAI-compatible API
uv run python src/main.py --image-path /path/to/images \
  --model qwen-vl-chat \
  --model-type openai \
  --api-base http://localhost:8000 \
  --api-key your-key

# Process with Chinese tags and descriptions
uv run python src/main.py --image-path /path/to/images --model qwen3-vl:4b --language zh --description

# Process with Japanese tags
uv run python src/main.py --image-path /path/to/images --model qwen3-vl:4b --language ja

# Use custom prompt configuration
uv run python src/main.py --image-path /path/to/images --model qwen3-vl:4b --language zh \
  --prompt-config prompts_custom_example.yaml

# Force reprocess all images (skip database cache)
uv run python src/main.py --image-path /path/to/images --model qwen3-vl:4b --reprocess
```

### Testing

```bash
# Run system tests
uv run python test_system.py

# View database structure
python src/show_table_structure.py
```

### Utility Scripts

```bash
# Extract all image paths from a directory and save to a file
python src/extract_image_paths.py --directory /path/to/images --output image_paths.txt

# Extract with relative paths
python src/extract_image_paths.py --directory /path/to/images --output image_paths.txt --relative

# Extract without recursing into subdirectories
python src/extract_image_paths.py --directory /path/to/images --output image_paths.txt --no-recursive
```

### Database Operations

```bash
# Open database
sqlite3 data/image_tags.db

# Query all records
sqlite3 data/image_tags.db "SELECT * FROM image_tags;"

# Export to CSV
sqlite3 -header -csv data/image_tags.db "SELECT * FROM image_tags;" > tags.csv
```

## Architecture

### Core Components

1. **src/main.py** - Main entry point that orchestrates the tagging workflow
2. **src/config.py** - Configuration management via command-line args or YAML files
3. **src/tagging.py** - Core tagging logic that coordinates image processing and model inference
4. **src/image_processor.py** - Image loading, preprocessing, and encoding utilities
5. **src/models.py** - Model abstraction layer for Ollama API integration
6. **src/prompt_manager.py** - Prompt template management from YAML configuration files
7. **src/database.py** - SQLite database operations for storing tagging results
8. **src/utils.py** - Utility functions (unique ID generation, file discovery)

### Data Flow

1. Config parsing (CLI args or YAML) → Config object
2. Image file discovery (single file or directory scan) → List of image paths
3. For each image:
   - Generate unique ID (SHA-256 hash of absolute path)
   - Check if already processed (database lookup)
   - Load and preprocess image (resize, convert to RGB, encode to JPEG bytes)
   - Call Ollama model API with image bytes and prompt
   - Parse model response to extract tags
   - Optionally generate description (separate model call)
   - Store results in database with metadata

### Database Schema

The `image_tags` table tracks all processed images with:
- `image_unique_id`: SHA-256 hash of image path (unique constraint)
- `image_path`: Full path to the image file
- `tags`: Comma-separated tag strings
- `description`: Optional AI-generated description
- `model_name`: Which model was used (e.g., "qwen-vl:4b")
- `image_size`: Processing dimensions (e.g., "512x512")
- `tag_count`: Number of tags generated
- `original_width/height`: Original image dimensions
- `image_format`: Source format (JPEG, PNG, etc.)
- `status`: success/failed/processing
- `error_message`: Error details if failed
- `processing_time`: Time in milliseconds
- `language`: Language used for tags and description (e.g., "en", "zh", "ja")
- `generated_at`: Timestamp

Indexes exist on `image_unique_id`, `image_path`, `model_name`, `generated_at`, and `status` for efficient queries.

### Ollama Integration

- The system requires Ollama service running locally on port 11434
- Currently supports vision-language models like qwen-vl:4b, llava-v1.6:3b, etc.
- API endpoint: http://localhost:11434/api/generate
- Image passed as base64-encoded JPEG in the request
- Response parsing handles both `response` and `thinking` fields
- Tag extraction uses regex to find comma-separated English words

## Key Implementation Details

### Incremental Processing

The system automatically skips already-processed images by checking `image_unique_id` in the database. This allows resuming interrupted batch processing.

### Error Handling

Failed processing is recorded in the database with `status='failed'` and an `error_message`. This preserves a complete audit trail.

### Image Preprocessing

Images are converted to RGB, resized (maintaining aspect ratio is NOT done - images are forcibly resized to target dimensions), and saved as JPEG bytes before being sent to the model.

### Tag Parsing

The `models.py` module includes sophisticated regex-based parsing to extract clean tags from model responses, handling various output formats and filtering for unique, valid tags. The parsing logic adapts based on the configured language:

- **English (en)**: Extracts alphabetic words and comma-separated sequences
- **Chinese (zh)**: Uses Unicode ranges for Chinese characters (U+4E00-U+9FFF)
- **Japanese (ja)**: Supports hiragana, katakana, and kanji characters
- **Korean (ko)**: Uses Unicode ranges for Hangul characters (U+AC00-U+D7AF)
- **European languages (es, fr, de, ru)**: Supports extended Latin and Cyrillic characters with diacritics

The model prompts are automatically adjusted based on the language setting to request tags and descriptions in the appropriate language.

### Prompt Configuration

The system uses configurable prompt templates stored in YAML files, allowing full customization of how the model is instructed.

**Default Configuration File**: `prompts.yaml` in project root

**Prompt Types**:
1. **System Prompts** - Define the model's role and behavior
2. **Tag Generation Prompts** - Instructions for generating image tags
3. **Description Prompts** - Instructions for generating image descriptions

**Template Variables**:
- `{language}`: Language code (e.g., "zh", "en")
- `{language_name}`: Natural language name (e.g., "Chinese", "English")
- `{tag_count}`: Number of tags to generate

**Using Custom Prompts**:
```bash
# Use custom prompt configuration
python src/main.py --image-path /path/to/images \
  --prompt-config my_custom_prompts.yaml \
  --language zh
```

**Example Custom Prompt** (`prompts_custom_example.yaml`):
```yaml
system_prompts:
  zh: "你是一个专业的图片标签生成器。请直接输出逗号分隔的关键词标签。"
  en: "You are a professional image tagger. Output ONLY comma-separated tags."

tag_prompts:
  zh: |
    请为这张图片生成{tag_count}个中文标签，用逗号分隔。
    标签应该包括：主题、风格、颜色、情绪、构图等方面。
    只输出标签，不要其他内容。
    标签：
```

This allows you to:
- Adjust tag specificity (e.g., request more artistic vs. technical tags)
- Change output format preferences
- Add domain-specific instructions
- Prioritize certain aspects (colors, mood, composition, etc.)

## Configuration

Configuration can be provided via:
1. Command-line arguments (see `src/config.py` for all options)
2. YAML config file (use `--config` flag)

Default configuration:
- Model: qwen-vl:4b
- Model type: ollama
- Resize: 512x512
- Tag count: 10
- Generate description: False
- DB path: ~/LocalImageSearch/.data/image_tags.db
- Model path: ~/LocalImageSearch/.model/ (for downloaded models)
- Language: en

### Application Directory Structure

The system uses a user home directory structure for persistent data:
- `~/LocalImageSearch/.data/` - Database and application data
  - `image_tags.db` - SQLite database with tagging results
- `~/LocalImageSearch/.model/` - Downloaded model files (default location for local models)
  - Model files downloaded via `src/download_model.py` are saved here by default

These directories are automatically created on first run.

### Model Types

The system supports three types of model backends:

1. **ollama** (default): Uses Ollama service
2. **openai**: OpenAI-compatible API
3. **local**: Local model files via Transformers

### Supported Languages

- en (English)
- zh (Chinese)
- ja (Japanese)
- ko (Korean)
- es (Spanish)
- fr (French)
- de (German)
- ru (Russian)

### Configuration Examples

#### Using Ollama:
```yaml
model: "qwen3-vl:4b"
model_type: "ollama"
image_path: "/path/to/your/images"
resize: "512x512"
tag_count: 20
generate_description: true
db_path: "./data/image_tags.db"
language: "zh"
```

#### Using OpenAI-compatible API:
```yaml
model: "qwen-vl-chat"
model_type: "openai"
api_base: "http://localhost:8000"
api_key: "your-api-key"  # optional
image_path: "/path/to/your/images"
language: "zh"
tag_count: 20
```

#### Using Local Model:
```yaml
model: "minicpm-v-2.5"
model_type: "local"
model_path: "/path/to/MiniCPM-V-2_5"
image_path: "/path/to/your/images"
language: "zh"
tag_count: 20
generate_description: true
```

## Dependencies

Core dependencies:
- Pillow (PIL) - Image processing
- requests - HTTP client for Ollama API
- PyYAML - Configuration file parsing
- tqdm - Progress bars
- sqlite3 - Built into Python (no external dependency)

## Notes for Development

- The system uses a single-threaded processing loop (no concurrency)
- All database operations use parameterized queries to prevent SQL injection
- The `Database` class manages connection lifecycle and creates tables/indexes automatically
- Model responses are parsed defensively to handle various output formats
- Supported image formats: JPEG, PNG, BMP, GIF (first frame only), WEBP

## Model Recommendations

See `doc/model_recommendations.md` for detailed information on:
- Recommended vision-language models for local deployment
- Model comparison (speed, accuracy, resource requirements)
- Configuration examples for different model types
- Best practices for model selection

Quick recommendations:
- **Fast processing**: llava-v1.6:3b or InternVL2-2B
- **Balanced (Chinese)**: qwen3-vl:4b or MiniCPM-V-2.5
- **High quality**: qwen3-vl:8b
- **Limited resources**: InternVL2-2B (<4GB VRAM)

## Performance Optimization

See `doc/performance_optimization.md` for detailed optimization strategies:
- Concurrent processing (multi-process/async)
- Batch processing
- Model optimization (quantization, GPU acceleration)
- Image preprocessing optimization
- Network optimization
- Expected performance improvements (up to 56-93x faster)

Current processing speed can be improved from ~28s/image to ~0.3-0.5s/image through proper optimization.
