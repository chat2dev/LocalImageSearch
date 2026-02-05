[English](README.md) | [中文](README.zh.md)

---

# LocalImageSearch

A local image auto-tagging and search system. Uses vision-language models (via Ollama / OpenAI-compatible API / local models) to automatically generate tags and descriptions for images, stores results in a SQLite database, and builds inverted and full-text search indexes for retrieval.

---

## Features

- **Multiple backends**: Ollama (local deployment), OpenAI-compatible API
- **Multi-language tags**: English, Chinese, Japanese, Korean, Spanish, French, German, Russian
- **Optimized Chinese prompts**: Multi-dimensional tagging strategy for high-quality Chinese tags
- **Incremental processing**: Automatically skips already-processed images; safe to resume after interruption
- **Auto indexing**: Inverted index and FTS5 full-text search index are built automatically after each run
- **Configurable prompts**: Customize model prompts via YAML files
- **Image description**: Optionally generate detailed descriptions via a separate model call
- **Fast deployment**: Simple setup with uv package manager
- **Web UI**: Next.js-based web interface for browsing and searching images

---

## Prerequisites

### Required Software

- Python >= 3.8.1
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Node.js >= 18 (for Web UI)
- At least one model backend:
  - [Ollama](https://ollama.ai) (default, recommended for local deployment)
  - OpenAI-compatible inference service (vLLM / Together / cloud provider APIs, etc.)

### Installation by Platform

<details>
<summary><b>macOS</b></summary>

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Node.js (for Web UI)
brew install node

# Install Ollama
brew install ollama
# Or download from: https://ollama.ai/download
```
</details>

<details>
<summary><b>Linux (Ubuntu/Debian)</b></summary>

```bash
# Update package list
sudo apt update

# Install Python
sudo apt install python3 python3-pip python3-venv

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
```
</details>

<details>
<summary><b>Linux (CentOS/RHEL/Fedora)</b></summary>

```bash
# Install Python
sudo dnf install python3 python3-pip

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Node.js
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
```
</details>

<details>
<summary><b>Windows</b></summary>

```powershell
# Install using Scoop (recommended)
# First install Scoop: https://scoop.sh/
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# Install Python
scoop install python

# Install uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install Node.js
scoop install nodejs

# Install Ollama
# Download and install from: https://ollama.com/download/windows
```

Alternatively, use [Chocolatey](https://chocolatey.org/):
```powershell
# Install Python
choco install python

# Install Node.js
choco install nodejs

# uv and Ollama: follow instructions above
```
</details>

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/chat2dev/LocalImageSearch.git
cd LocalImageSearch
```

### 2. Backend Setup

```bash
# Using uv (recommended)
uv sync

# This single command will:
# - Create a virtual environment (.venv) if it doesn't exist
# - Install all dependencies from pyproject.toml
# - Lock dependencies in uv.lock for reproducibility
```

### 3. Install Ollama Model

```bash
# Pull the vision-language model (one-time setup, ~3.3GB)
ollama pull qwen3-vl:4b
```

### 4. Web UI Setup (Optional)

```bash
cd ui
npm install
cd ..
```

---

## Quick Start

### Step 0: Initialize Database (First-Time Setup)

**Important**: Initialize the database before first use:

```bash
# Initialize database with schema
uv run python scripts/init_database.py
```

This creates the database at `~/.LocalImageSearch/data/image_tags.db` with all necessary tables and indexes. You only need to do this once.

> **Note**: If you skip this step and start the Web UI directly, you'll see errors because the database tables don't exist yet.

### Option 1: Command Line Interface

Tag images and search from the command line:

```bash
# Tag a single image with 10 Chinese tags
uv run python src/main.py --image-path /path/to/image.jpg --model qwen3-vl:4b --language zh

# Tag an entire directory and generate descriptions
uv run python src/main.py --image-path /path/to/images/ --model qwen3-vl:4b --language zh --description

# Search the results
uv run python src/index_builder.py search "人工智能" --mode tag
```

Tags are saved to `data/image_tags.db` and indexes are built automatically on completion.

### Option 2: Web UI (Recommended)

Start the web interface for a better browsing experience:

```bash
cd ui
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

**Web UI Features:**
- **Bilingual Interface**: Switch between Chinese and English
- **Tag Cloud**: Browse images by popular tags (configurable TOP 20/100)
- **Multi-tag Filtering**: AND-based filtering using inverted index
- **Full-text Search**: Search across tags and descriptions
- **Responsive Grid**: Image gallery with pagination
- **Image Viewer**: Modal viewer with fullscreen support

**Database Location**: The UI reads from `~/.LocalImageSearch/data/image_tags.db`.

**Recommended Workflow:**
1. Initialize database (first time only): `uv run python scripts/init_database.py`
2. Tag images using CLI: `uv run python src/main.py --image-path ~/Pictures`
3. Start Web UI: `cd ui && npm run dev`
4. Browse and search your tagged images at http://localhost:3000

> **Tip**: You can run the tagging command multiple times with different directories. New images will be added to the existing database.

For detailed Web UI configuration, see [ui/README.md](ui/README.md).

---

## Chinese Tag Quality

This system uses an **optimized multi-dimensional tagging strategy** specifically designed for high-quality Chinese tags:

### Tag Characteristics

- **Minimum 2 characters**: No single-character tags; uses noun phrases
- **Multi-dimensional coverage**:
  - Image type (e.g., 商品照片, 界面截图, 证件照)
  - Object recognition (e.g., 宠物猫咪, 电子产品, 食品包装)
  - Text content (e.g., 品牌名称, 系统功能名)
  - Scene/location (e.g., 室内环境, 户外景观)
  - Visual style (e.g., 扁平设计, 写实摄影)

### Example Tags

**Product packaging**:
```
产品包装, 营养成分表, 饮品标签, 食品包装, 手持特写,
条形码, 营养信息, 饮料产品, 室内场景, 手持商品
```

**System interface screenshot**:
```
界面截图, 用户登录, 企业服务, 系统操作, 界面设计,
登录流程, 企业认证, 系统功能, 用户管理, 企业应用
```

**City night selfie**:
```
城市夜景, 自拍照片, 人物肖像, 户外街道, 夜晚灯光,
建筑群, 城市风光, 夜间自拍, 建筑灯光, 街景摄影
```

---

## Detailed Usage

### Model Types

| Type | `--model-type` | Description |
|------|----------------|-------------|
| Ollama | `ollama` (default) | Local Ollama service on port 11434 |
| OpenAI-compatible | `openai` | vLLM, cloud provider APIs, etc. |

```bash
# Ollama (default, recommended)
uv run python src/main.py --image-path ./images --model qwen3-vl:4b

# OpenAI-compatible API
uv run python src/main.py --image-path ./images \
  --model qwen-vl-chat \
  --model-type openai \
  --api-base http://localhost:8000/v1 \
  --api-key your-key
```

### Language Support

Set the tag and description language via `--language`:

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `ko` | Korean |
| `zh` | Chinese | `es` | Spanish |
| `ja` | Japanese | `fr` | French |
| | | `de` | German |
| | | `ru` | Russian |

### All CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--image-path` | (required) | Image file or directory path |
| `--model` | `qwen3-vl:4b` | Model name |
| `--model-type` | `ollama` | Model backend type (ollama/openai) |
| `--api-base` | — | API base URL (for `openai` type) |
| `--api-key` | — | API key (for `openai` type) |
| `--language` | `zh` | Tag language (zh/en/ja/ko/es/fr/de/ru) |
| `--tag-count` | `10` | Number of tags to generate |
| `--resize` | `512x512` | Image resize dimensions |
| `--description` | `false` | Enable description generation |
| `--db-path` | `./data/image_tags.db` | Database path |
| `--reprocess` | `false` | Force re-process already tagged images |
| `--prompt-config` | `prompts.yaml` | Custom prompt config file |

### YAML Configuration

All CLI options can be specified via a config file:

```yaml
# config.yaml
model: "qwen3-vl:4b"
model_type: "ollama"
image_path: "/path/to/images"
language: "zh"
tag_count: 20
generate_description: true
resize: "512x512"
db_path: "./data/image_tags.db"
```

```bash
python src/main.py --config config.yaml
```

### Custom Prompts

Copy `prompts_custom_example.yaml` as a starting point and pass it via `--prompt-config`:

```bash
cp prompts_custom_example.yaml my_prompts.yaml
# Edit my_prompts.yaml ...
python src/main.py --image-path ./images --model qwen3-vl:4b --language zh \
  --prompt-config my_prompts.yaml
```

Supported template variables: `{language}`, `{language_name}`, `{tag_count}`.

---

## Indexing and Search

Two indexes are built automatically after each processing run. To trigger a manual rebuild:

```bash
python src/index_builder.py build
```

### Index Structure

| Index | Table | Mechanism | Use Case |
|-------|-------|-----------|----------|
| Inverted index | `tag_index` | Each comma-separated tag is mapped individually to image IDs | Exact tag filtering |
| Full-text index | `image_fts` | FTS5 virtual table over tags + description | Free-form keyword search |

### Search Commands

```bash
# Exact single-tag match
python src/index_builder.py search "网络安全" --mode tag

# Multi-tag union (match any)
python src/index_builder.py search "智能,代码" --mode tags --match any

# Multi-tag intersection (must contain all)
python src/index_builder.py search "智能,代码" --mode tags --match all

# Keyword search (supports substrings, e.g. "智能" matches "人工智能")
python src/index_builder.py search "智能" --mode fts

# Show tag frequency statistics
python src/index_builder.py stats
```

### FTS Search Syntax

When `description` contains content, `--mode fts` can perform more granular searches across the description text:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `word` | Single token match | `人工智能` |
| `wordA wordB` | AND (default) | `人工智能 机器人` |
| `wordA OR wordB` | OR | `人工智能 OR 机器学习` |
| `wordA NOT wordB` | Exclude | `智能 NOT 机器` |
| `column:word` | Search specific column | `tags:人工智能` |

> Note: FTS5 matches at the token level, not substring level. `--mode fts` automatically falls back to a LIKE substring search when FTS returns no results, so it is safe to use as the default search mode.

---

## Docker Deployment

**Alternative deployment option**: A complete Docker setup is available with automatic database initialization.

### Quick Start (Docker)

```bash
# 1. Pull the Ollama model (one-time setup)
ollama pull qwen3-vl:4b

# 2. Start all services
docker-compose up -d

# 3. View logs
docker logs -f image-tagger-app
```

The system will:
1. Initialize a fresh database with the latest schema
2. Tag all images in `~/Downloads` (configurable in `docker-compose.yml`)
3. Build search indexes automatically
4. Keep the container running for Web UI access

### Database Behavior

**Important**: The database is **NOT mounted** from the host. It is created fresh inside the container on each startup.

**Why?**
- Ensures the database schema is always up-to-date
- Avoids schema migration issues
- Simplifies deployment and testing

**Implications:**
- Container restart = data loss (tags will be regenerated)
- For production use with persistent data, uncomment the volume mount in `docker-compose.yml`:
  ```yaml
  volumes:
    - ./data:/app/data  # Add this line to persist database
  ```

### Viewing Results

While the container is running:

```bash
# Check tagging progress
docker logs image-tagger-app | grep "Successfully processed"

# Query database inside container
docker exec image-tagger-app uv run python -c "
from src.db_manager import Database
db = Database('data/image_tags.db')
print(f'Total records: {db.count_tags()}')
db.close()
"

# Or use the Web UI
open http://localhost:3000
```

### Configuration

Edit `docker-compose.yml` to customize:
- Image source directory (default: `~/Downloads`)
- Model name (default: `qwen3-vl:4b`)
- Language (default: `zh`)
- Tag count (default: `5`)

---

## Database Operations

The database is SQLite, stored at `data/image_tags.db` by default.

```bash
# View table structure
python src/show_table_structure.py

# Query with sqlite3
sqlite3 data/image_tags.db "SELECT * FROM image_tags LIMIT 10;"
sqlite3 data/image_tags.db "SELECT tag, COUNT(*) as cnt FROM tag_index GROUP BY tag ORDER BY cnt DESC LIMIT 20;"

# Export to CSV
sqlite3 -header -csv data/image_tags.db "SELECT * FROM image_tags;" > tags.csv
```

### Tables

| Table | Description |
|-------|-------------|
| `image_tags` | Main data table: tags, descriptions, and image metadata |
| `tag_index` | Inverted index: tag → image_id mapping |
| `image_fts` | FTS5 full-text search virtual table |

### Utility Scripts

```bash
# Extract all image paths in a directory to a file
python src/extract_image_paths.py --directory /path/to/images --output paths.txt

# Extract relative paths
python src/extract_image_paths.py --directory /path/to/images --output paths.txt --relative

# Do not recurse into subdirectories
python src/extract_image_paths.py --directory /path/to/images --output paths.txt --no-recursive
```

---

## Project Structure

```
.
├── src/
│   ├── main.py               # Entry point, orchestrates the workflow
│   ├── config.py             # CLI argument parsing and config management
│   ├── tagging.py            # Tagging flow coordination
│   ├── image_processor.py    # Image loading, preprocessing, encoding
│   ├── models.py             # Model backend abstraction (Ollama / OpenAI / Local / Gemini)
│   ├── prompt_manager.py     # Prompt template management
│   ├── database.py           # SQLite CRUD operations
│   ├── index_builder.py      # Inverted index + FTS5 index build and search
│   ├── utils.py              # Utilities (unique ID generation, image file discovery)
│   ├── extract_image_paths.py # Batch image path extraction
│   ├── show_table_structure.py # Display database schema
│   ├── download_model.py     # Model download helper
│   └── benchmark_models.py   # Model benchmarking
├── doc/                      # Detailed documentation (see below)
├── ui/                       # Next.js web interface (see ui/README.md)
│   ├── app/                  # Next.js app directory
│   ├── lib/                  # Frontend utilities and database queries
│   └── *.config.*            # Build configuration files
├── data/                     # Database storage directory
├── models/                   # Local model files directory
├── test_images/              # Test images
├── prompts.yaml              # Default prompt configuration
├── prompts_custom_example.yaml # Custom prompt template example
├── benchmark_config.example.json # Benchmark config example
├── pyproject.toml
└── requirements.txt
```

### Data Flow

```
CLI / YAML config
    ↓
Image file discovery (single file / recursive directory scan)
    ↓
For each image:
    Generate unique ID (SHA-256 of absolute path)
    ↓ DB lookup → skip if already exists
    ↓
    Preprocess (→ RGB → resize → JPEG encode)
    ↓
    Call model API → parse tags
    ↓ (optional) Call model → generate description
    ↓
    Write to image_tags table
        ↓
Processing complete → build tag_index + image_fts indexes
```

---

## Further Reading

| Document | Contents |
|----------|----------|
| [doc/model_recommendations.md](doc/model_recommendations.md) | Model selection guide, resource requirements, download instructions |
| [doc/performance_optimization.md](doc/performance_optimization.md) | Concurrency, quantization, preprocessing optimizations |
| [doc/installation.md](doc/installation.md) | Detailed installation steps and troubleshooting |
| [doc/usage.md](doc/usage.md) | Full usage tutorial |
| [doc/benchmark_guide.md](doc/benchmark_guide.md) | Model benchmarking guide |
| [doc/changelog.md](doc/changelog.md) | Version changelog |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| Pillow | Image loading and preprocessing |
| requests | HTTP client (Ollama / OpenAI API) |
| PyYAML | Configuration file parsing |
| tqdm | Processing progress bar |
| sqlite3 | Database (Python built-in) |
