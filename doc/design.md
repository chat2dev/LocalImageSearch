[English](design.md) | [中文](design.zh.md)

---

# System Design Document

**LocalImageSearch - Image Auto-Tagging and Search System**

This document describes the overall architecture, core module design, data flow, indexing mechanisms, and extensibility considerations of the system.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Design](#2-architecture-design)
3. [Core Module Design](#3-core-module-design)
4. [Data Flow Design](#4-data-flow-design)
5. [Model Abstraction Layer](#5-model-abstraction-layer)
6. [Index System Design](#6-index-system-design)
7. [Prompt Management](#7-prompt-management)
8. [Configuration Management](#8-configuration-management)
9. [Error Handling and Status Tracking](#9-error-handling-and-status-tracking)
10. [Extensibility Design](#10-extensibility-design)
11. [Performance Optimization](#11-performance-optimization)

---

## 1. System Overview

### 1.1 Goals

Build a localized image auto-tagging and retrieval system with the following capabilities:

- Automatically generate image tags and descriptions
- Support multiple vision-language model backends
- Multi-language tag generation (8 languages)
- Incremental processing to avoid redundant computation
- Efficient tag retrieval (exact matching + full-text search)

### 1.2 Core Design Principles

| Principle | Description |
|-----------|-------------|
| **Modularity** | Single responsibility per component with clear interfaces |
| **Extensibility** | Easy to add new models, languages, and index types |
| **Incremental** | Support resume-after-interrupt, avoid reprocessing |
| **Non-invasive** | Read images only, never modify original files |
| **Local-first** | Prioritize local models to minimize API costs |

---

## 2. Architecture Design

### 2.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Presentation Layer (Web UI)                │
│            Next.js App (ui/) - Bilingual Interface          │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │ Tag Cloud    │  │ Image Grid   │  │ Search Bar   │     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────────┬──────────────────────────────┘
                               │ (API Routes)
┌──────────────────────────────┴──────────────────────────────┐
│                     Application Layer (CLI)                 │
│                  main.py + config.py                        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                      Business Logic Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ tagging.py   │  │ index_builder│  │ prompt_mgr   │      │
│  │ (Tagging)    │  │ (Indexing)   │  │ (Prompts)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                      Data Access Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ models.py    │  │ database.py  │  │ image_proc   │      │
│  │ (Model Abs.) │  │ (Database)   │  │ (Image Proc.)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                     Infrastructure Layer                    │
│     Ollama API / OpenAI API / Local Models / SQLite / FTS5  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **Application Entry** | `main.py` | CLI entry point, orchestrates workflow |
| **Configuration** | `config.py` | Parse CLI arguments and YAML config |
| **Tagging Coordinator** | `tagging.py` | Coordinates image processing, model calls, storage |
| **Model Abstraction** | `models.py` | Unified interface for multiple model backends |
| **Image Processing** | `image_processor.py` | Image loading, preprocessing, encoding |
| **Database** | `database.py` | SQLite CRUD operations |
| **Index System** | `index_builder.py` | Inverted index + FTS5 full-text search |
| **Prompt Management** | `prompt_manager.py` | Multi-language prompt template loading |
| **Utilities** | `utils.py` | File discovery, unique ID generation |

---

## 3. Core Module Design

### 3.1 main.py - Application Entry

**Responsibilities:**
- Parse configuration (CLI / YAML)
- Discover image files to process
- Loop through images calling `process_image`
- Trigger index building after processing
- Output statistics

**Key Logic:**
```python
config = Config().parse_args()
image_files = get_image_files(config.image_path)
db = Database(config.db_path)

for image_path in image_files:
    process_image(image_path, config, db)

# Auto-build indexes after processing
IndexBuilder(db_path).build()
```

### 3.2 tagging.py - Tagging Coordinator

**Responsibilities:**
- Generate unique image ID (SHA-256)
- Check database to skip already-processed images
- Call `image_processor` to preprocess images
- Call model to generate tags and description
- Parse model output to extract tags
- Write results to database

**Core Function Signature:**
```python
def process_image(
    image_path: str,
    model_name: str,
    resize_width: int,
    resize_height: int,
    tag_count: int,
    generate_description: bool,
    db: Database,
    language: str,
    model_type: str,
    force_reprocess: bool,
    prompt_config_path: str
) -> bool:
    """Process a single image, return success status"""
```

**Status Recording:**
- Success: `status='success'`, record tags, description, processing_time
- Failure: `status='failed'`, record error_message

### 3.3 models.py - Model Abstraction Layer

**Design Pattern:** Strategy Pattern

**Interface Definition:**
```python
class BaseModel:
    def generate_tags(self, image_bytes: bytes, prompt: str) -> str:
        """Generate tags, return raw model output"""
        raise NotImplementedError

    def generate_description(self, image_bytes: bytes, prompt: str) -> str:
        """Generate description, return raw model output"""
        raise NotImplementedError
```

**Implementation Classes:**
- `OllamaModel`: Ollama local service (default)
- `OpenAIModel`: OpenAI-compatible API (vLLM / cloud providers)
- `LocalModel`: Local Transformers model files
- `GeminiModel`: Google Gemini API

**Factory Function:**
```python
def get_model(model_type: str, model_name: str, **kwargs) -> BaseModel:
    """Return corresponding model instance based on model_type"""
```

### 3.4 image_processor.py - Image Processing

**Responsibilities:**
- Load images (supports JPEG, PNG, BMP, GIF, WEBP)
- Convert to RGB mode
- Resize to target dimensions (forced resize, no aspect ratio preservation)
- Encode to JPEG bytes (for model API)
- Return original metadata (width, height, format)

**Key Function:**
```python
def load_and_preprocess_image(
    image_path: str,
    target_width: int,
    target_height: int
) -> Tuple[bytes, dict]:
    """Return (JPEG bytes, metadata)"""
```

### 3.5 database.py - Database Operations

**Responsibilities:**
- Manage SQLite connection lifecycle
- Create `image_tags` table and indexes
- Provide CRUD methods

**Core Methods:**
```python
class Database:
    def insert_tag(self, image_unique_id, image_path, tags, ...):
        """Insert or replace tag record"""

    def get_tags_by_image_id(self, image_unique_id):
        """Query single record (for deduplication)"""

    def get_all_tags(self):
        """Query all records"""
```

**Table Structure:** See [doc/table-design.md](table-design.md)

### 3.6 index_builder.py - Index System

See [Section 6: Index System Design](#6-index-system-design)

### 3.7 prompt_manager.py - Prompt Management

**Responsibilities:**
- Load prompt templates from YAML file
- Select prompt based on language and task type
- Replace template variables (`{language}`, `{tag_count}`, etc.)

**Core Methods:**
```python
class PromptManager:
    def get_tag_prompt(self, language: str, tag_count: int) -> str:
        """Get tag generation prompt"""

    def get_description_prompt(self, language: str) -> str:
        """Get description generation prompt"""
```

### 3.8 utils.py - Utility Functions

**Key Functions:**
```python
def generate_unique_id(image_path: str) -> str:
    """SHA-256(absolute path) → unique ID"""

def get_image_files(directory: str) -> List[str]:
    """Recursively scan directory, return all image file paths"""
```

---

## 4. Data Flow Design

### 4.1 Tagging Flow

```
User Input (CLI / YAML)
    ↓
Config Parsing → Config Object
    ↓
Image File Discovery → List[image_path]
    ↓
Loop Through Each Image:
    ├─ Generate unique_id = SHA256(abs_path)
    ├─ Database Deduplication → Already exists? → Skip
    ├─ Image Preprocessing → (image_bytes, metadata)
    ├─ Load Prompt Templates → (tag_prompt, desc_prompt)
    ├─ Call Model:
    │   ├─ generate_tags(image_bytes, tag_prompt) → raw_output
    │   ├─ Parse tags → List[str]
    │   └─ (Optional) generate_description(image_bytes, desc_prompt)
    ├─ Write to Database:
    │   └─ INSERT (unique_id, path, tags, desc, model, ..., status, time)
    └─ Return success/failed
        ↓
All Images Processed
    ↓
IndexBuilder.build() → Build Inverted Index + FTS5
    ↓
Output Statistics → Success count, failure count, DB path
```

### 4.2 Search Flow

```
User Search Request (CLI)
    ↓
IndexSearcher(db_path)
    ↓
Based on Search Mode:
    ├─ --mode tag → search_by_tag(tag)
    │   └─ SELECT FROM tag_index WHERE tag = ?
    │
    ├─ --mode tags → search_by_tags(tags, match='any'|'all')
    │   ├─ match=any → tag IN (...)
    │   └─ match=all → GROUP BY ... HAVING COUNT = ?
    │
    └─ --mode fts → search_keyword(query)
        ├─ Step 1: FTS5 MATCH → Results? → Return
        └─ Step 2: LIKE Fallback → tag LIKE %query%
            ↓
Return List[{id, path, tags, description}]
    ↓
Format Output → Filename + tags + desc
```

---

## 5. Model Abstraction Layer

### 5.1 Design Goals

- **Unified Interface**: Different model backends use the same calling method
- **Easy Extension**: Add new models by implementing `BaseModel` interface only
- **Configuration-Driven**: Switch models via `model_type` parameter

### 5.2 Interface Design

```python
class BaseModel:
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        # kwargs accepts api_base, api_key, model_path, etc.

    def generate_tags(self, image_bytes: bytes, prompt: str) -> str:
        """Input image and prompt, return raw model output"""
        raise NotImplementedError

    def generate_description(self, image_bytes: bytes, prompt: str) -> str:
        """Input image and prompt, return raw model output"""
        raise NotImplementedError
```

### 5.3 Implementation Class Comparison

| Class | Communication | Dependencies | Advantages | Disadvantages |
|-------|---------------|--------------|------------|---------------|
| `OllamaModel` | HTTP API (localhost:11434) | requests | Simple deployment, multi-model switching | Requires local Ollama service |
| `OpenAIModel` | HTTP API (custom endpoint) | requests | Strong compatibility, cloud support | Requires API key, potential costs |
| `LocalModel` | Direct Python calls | transformers, torch | Fully local, no network | High memory usage, slow initialization |
| `GeminiModel` | HTTP API (Google) | requests | Cloud-based large model, high quality | Requires API key, rate limits |

### 5.4 Factory Pattern

```python
def get_model(model_type: str, model_name: str, **kwargs) -> BaseModel:
    if model_type == "ollama":
        return OllamaModel(model_name, **kwargs)
    elif model_type == "openai":
        return OpenAIModel(model_name, api_base=kwargs.get('api_base'), ...)
    elif model_type == "local":
        return LocalModel(model_name, model_path=kwargs.get('model_path'), ...)
    elif model_type == "gemini":
        return GeminiModel(model_name, api_key=kwargs.get('api_key'), ...)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
```

### 5.5 Tag Parsing Strategy

Model output formats vary, requiring unified parsing logic:

```python
def parse_tags(raw_output: str, language: str) -> List[str]:
    """Extract tag list from raw model output"""
    # 1. Extract content after "Tags:" or "标签:"
    # 2. Select regex based on language:
    #    - Chinese: [\u4e00-\u9fff]+
    #    - English: [a-zA-Z]+
    #    - Japanese: [\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+
    #    ...
    # 3. Deduplicate, filter empty values
    # 4. Return List[str]
```

---

## 6. Index System Design

### 6.1 Design Goals

- **Exact Retrieval**: Support tag exact matching, multi-tag intersection/union
- **Fuzzy Retrieval**: Support keyword substring matching, full-text search
- **High Performance**: Utilize database indexes, avoid full table scans
- **Auto Update**: Automatically refresh indexes after tagging process

### 6.2 Dual-Layer Index Architecture

```
image_tags (main table)
    ├─ Basic Indexes (B-Tree)
    │   ├─ idx_image_unique_id
    │   ├─ idx_model_name
    │   └─ idx_generated_at
    │
    ├─ tag_index (Inverted Index)
    │   ├─ Structure: (tag, image_id, image_unique_id)
    │   ├─ Indexes: idx_ti_tag, idx_ti_image_id
    │   └─ Use: Exact tag queries, multi-tag combinations
    │
    └─ image_fts (FTS5 Full-Text Index)
        ├─ Virtual Table: (tags, description)
        ├─ tokenize: unicode61 (default CJK tokenization)
        └─ Use: Keyword search, relevance ranking
```

### 6.3 Inverted Index (tag_index) Design

**Table Structure:**
```sql
CREATE TABLE tag_index (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tag             TEXT    NOT NULL,
    image_id        INTEGER NOT NULL,  -- FK -> image_tags.id
    image_unique_id TEXT    NOT NULL,
    UNIQUE(tag, image_id)
);

CREATE INDEX idx_ti_tag      ON tag_index(tag);
CREATE INDEX idx_ti_image_id ON tag_index(image_id);
```

**Build Process:**
```python
# Full rebuild
DELETE FROM tag_index;

for row in SELECT id, tags FROM image_tags WHERE status='success':
    for tag in row.tags.split(','):
        INSERT INTO tag_index (tag, image_id, image_unique_id)
        VALUES (tag.strip(), row.id, row.unique_id);
```

**Query Examples:**
```python
# Single tag exact match
SELECT it.* FROM tag_index ti
JOIN image_tags it ON ti.image_id = it.id
WHERE ti.tag = 'artificial intelligence';

# Multi-tag union (any)
WHERE ti.tag IN ('AI', 'machine learning');

# Multi-tag intersection (all)
WHERE ti.tag IN ('AI', 'machine learning')
GROUP BY it.id
HAVING COUNT(DISTINCT ti.tag) = 2;  -- Must match all tags
```

### 6.4 FTS5 Full-Text Index (image_fts) Design

**Virtual Table Structure:**
```sql
CREATE VIRTUAL TABLE image_fts USING fts5(
    tags,
    description,
    tokenize = 'unicode61'
);

-- rowid aligns with image_tags.id
INSERT INTO image_fts(rowid, tags, description)
SELECT id, REPLACE(tags, ',', ' '), COALESCE(description, '')
FROM image_tags WHERE status='success';
```

**Tokenization Mechanism:**
- `REPLACE(tags, ',', ' ')`: Replace commas with spaces, making each tag an independent token
- `unicode61`: Default tokenizer, CJK character sequences as single tokens
- Example: `"人工智能,机器学习"` → `"人工智能 机器学习"` → tokens: `["人工智能", "机器学习"]`

**Search Strategy:**
```python
def search_keyword(query: str):
    # Step 1: FTS5 exact token match
    results = fts.MATCH(query)
    if results:
        return results

    # Step 2: LIKE substring match (fallback)
    results = tag_index WHERE tag LIKE %query%
    return results
```

**FTS5 Query Syntax:**
```sql
-- Single word match
WHERE image_fts MATCH 'artificial intelligence';

-- AND query (default)
WHERE image_fts MATCH 'artificial intelligence robot';

-- OR query
WHERE image_fts MATCH 'AI OR machine learning';

-- NOT exclusion
WHERE image_fts MATCH 'intelligence NOT machine';

-- Column-specific search
WHERE image_fts MATCH 'tags:artificial intelligence';
```

### 6.5 Index Update Strategy

**Update Timing:**
1. `main.py` auto-calls `IndexBuilder.build()` after processing all images
2. User manually runs `python src/index_builder.py build`

**Update Method:**
- **Full Rebuild** (current implementation)
  - Pros: Simple, strong consistency
  - Cons: Time-consuming for large datasets

- **Incremental Update** (future optimization)
  - Process only new/changed image_tags records
  - Requires maintaining `last_indexed_at` timestamp

**Performance Optimization:**
```python
# Batch insert, disable auto-commit
conn.execute("BEGIN TRANSACTION")
for tag_record in tag_records:
    conn.execute("INSERT INTO tag_index ...")
conn.execute("COMMIT")
```

### 6.6 IndexSearcher API Design

```python
class IndexSearcher:
    def search_by_tag(self, tag: str) -> List[Dict]:
        """Single tag exact match"""

    def search_by_tags(self, tags: List[str], mode: str) -> List[Dict]:
        """Multi-tag match, mode='any'|'all'"""

    def search_fulltext(self, query: str) -> List[Dict]:
        """FTS5 full-text search"""

    def search_keyword(self, keyword: str) -> List[Dict]:
        """Smart search: FTS → LIKE fallback"""

    def get_tag_stats(self) -> List[Dict]:
        """Return all tags with frequency counts"""

    def get_similar_tags(self, keyword: str) -> List[Dict]:
        """Fuzzy tag matching (LIKE %keyword%)"""
```

---

## 7. Prompt Management

### 7.1 YAML Configuration Structure

```yaml
# prompts.yaml
system_prompts:
  zh: "You are an image tagger..."
  en: "You are a vision AI..."
  default: "..."

tag_prompts:
  zh: "Generate {tag_count} Chinese tags..."
  en: "List {tag_count} tags..."
  default: "..."

description_prompts:
  zh: "Describe this image in detail in Chinese..."
  en: "Describe this image in detail..."
  default: "..."

language_names:
  zh: "Chinese"
  en: "English"
  ja: "Japanese"
  ...
```

### 7.2 PromptManager Implementation

```python
class PromptManager:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.prompts = yaml.safe_load(f)

    def get_tag_prompt(self, language: str, tag_count: int) -> str:
        template = self.prompts['tag_prompts'].get(language)
        if not template:
            template = self.prompts['tag_prompts']['default']

        lang_name = self.prompts['language_names'].get(language, 'English')
        return template.format(
            language=language,
            language_name=lang_name,
            tag_count=tag_count
        )
```

### 7.3 Adding New Languages

1. Add corresponding language's `tag_prompts` and `description_prompts` in `prompts.yaml`
2. Add language name mapping in `language_names`
3. Add regex for that language in `models.py`'s `parse_tags` function
4. Add new language code to `--language` choices in `config.py`

---

## 8. Configuration Management

### 8.1 Configuration Source Priority

```
CLI Arguments > YAML Config File > Default Values
```

### 8.2 Config Class Design

```python
class Config:
    # Default values
    model = "qwen3-vl:4b"
    model_type = "ollama"
    language = "en"
    tag_count = 10
    resize = "512x512"
    db_path = "./data/image_tags.db"
    ...

    def parse_args(self):
        """Parse CLI arguments, override defaults"""
        parser = argparse.ArgumentParser()
        parser.add_argument('--model', ...)
        parser.add_argument('--config', help='YAML config file path')
        args = parser.parse_args()

        # Load YAML first (if provided)
        if args.config:
            self.load_yaml(args.config)

        # Override with CLI arguments
        if args.model:
            self.model = args.model
        ...

    def load_yaml(self, path: str):
        """Load configuration from YAML file"""
        with open(path) as f:
            config = yaml.safe_load(f)
        for key, value in config.items():
            setattr(self, key, value)
```

### 8.3 Configuration Validation

```python
def validate(self):
    """Validate configuration legality"""
    if self.model_type == 'local' and not self.model_path:
        raise ValueError("model_type=local requires model_path")

    if self.model_type == 'openai' and not self.api_base:
        raise ValueError("model_type=openai requires api_base")

    if self.tag_count < 1:
        raise ValueError("tag_count must be >= 1")
```

---

## 9. Error Handling and Status Tracking

### 9.1 Error Classification

| Error Type | Handling Strategy | Recording Method |
|------------|-------------------|------------------|
| **Image Read Failure** | Skip image, record error | `status='failed'`, `error_message='File not found'` |
| **Model Call Failure** | Skip image, record error | `status='failed'`, `error_message='API timeout'` |
| **Tag Parsing Failure** | Skip image, record error | `status='failed'`, `error_message='No tags found'` |
| **Database Write Failure** | Skip image, record error | Print log, don't write to database |

### 9.2 Status Tracking

```python
try:
    start_time = time.time()

    # 1. Preprocess image
    image_bytes, metadata = load_and_preprocess_image(...)

    # 2. Call model
    raw_output = model.generate_tags(image_bytes, prompt)

    # 3. Parse tags
    tags = parse_tags(raw_output, language)
    if not tags:
        raise ValueError("No tags extracted")

    # 4. Write to database
    processing_time = int((time.time() - start_time) * 1000)
    db.insert_tag(
        ...,
        status='success',
        processing_time=processing_time
    )
    return True

except Exception as e:
    # Record failure
    db.insert_tag(
        ...,
        status='failed',
        error_message=str(e)
    )
    print(f"Error processing {image_path}: {e}")
    return False
```

### 9.3 Progress Display

```python
from tqdm import tqdm

with tqdm(total=len(image_files), desc="Processing", unit="images") as pbar:
    for image_path in image_files:
        process_image(...)
        pbar.update(1)
```

---

## 10. Extensibility Design

### 10.1 Adding New Model Backend

1. Create new class in `models.py`, inherit `BaseModel`
2. Implement `generate_tags` and `generate_description` methods
3. Add new branch in `get_model` factory function
4. Add new type to `--model-type` choices in `config.py`

**Example: Adding Claude Support**
```python
class ClaudeModel(BaseModel):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        self.api_key = api_key

    def generate_tags(self, image_bytes: bytes, prompt: str) -> str:
        # Call Anthropic Claude API
        ...
```

### 10.2 Adding New Language

See [Section 7.3](#73-adding-new-languages)

### 10.3 Adding New Index Type

**Example: Adding Vector Index (Image Similarity Search)**

1. Add `VectorIndex` class in `index_builder.py`
2. Use CLIP / ResNet to extract image feature vectors
3. Store in SQLite BLOB column or external vector database (e.g., Faiss)
4. Provide `search_similar(image_path, top_k=10)` interface

### 10.4 Database Migration

Currently using SQLite, can migrate to:

- **PostgreSQL**: Higher concurrency, more complex queries
- **MySQL**: Suitable for distributed deployment
- **MongoDB**: Suitable for unstructured data (e.g., JSON tags)

**Migration Steps:**
1. Abstract `database.py` to interface class `BaseDatabase`
2. Implement `SQLiteDatabase`, `PostgreSQLDatabase` subclasses
3. Provide data export/import scripts

---

## 11. Performance Optimization

### 11.1 Current Bottlenecks

| Stage | Time Proportion | Optimization Direction |
|-------|----------------|------------------------|
| **Model Inference** | 80-90% | Use smaller models, quantization, GPU acceleration |
| **Image I/O** | 5-10% | Batch reading, memory caching |
| **Database Writes** | 3-5% | Batch inserts, transaction optimization |
| **Network Requests** | Variable | Local deployment, connection pooling |

### 11.2 Optimization Strategies

**1. Concurrent Processing**
```python
from multiprocessing import Pool

def worker(image_path):
    process_image(image_path, config, db)

with Pool(processes=4) as pool:
    pool.map(worker, image_files)
```

**2. Batch Database Operations**
```python
conn.execute("BEGIN TRANSACTION")
for record in records:
    conn.execute("INSERT INTO ...")
conn.execute("COMMIT")
```

**3. Model Optimization**
- Use quantized models (e.g., 4-bit, 8-bit)
- Reduce image resolution (256x256 vs 512x512)
- Choose smaller models (2B vs 7B)

**4. Index Optimization**
- Regularly `VACUUM` to clean SQLite fragmentation
- Regularly `ANALYZE` to update query statistics
- Create covering indexes for common queries

See detailed optimization plans in [doc/performance_optimization.md](performance_optimization.md)

---

## 12. Summary

### 12.1 Core Design Highlights

1. **Modular Architecture**: Clear layering, easy to maintain and test
2. **Model Abstraction**: Unified interface supporting multiple backends, lower migration cost
3. **Dual-Layer Indexing**: Inverted index + FTS5 full-text search, balancing precision and flexibility
4. **Incremental Processing**: SHA-256 based deduplication, avoid redundant computation
5. **Configuration-Driven**: CLI + YAML + Prompt templates, highly configurable
6. **Error Tolerance**: Single image failure doesn't affect overall process, detailed error logging

### 12.2 Future Evolution Directions

- **Concurrent Processing**: Support multi-process/async I/O for dramatically improved throughput
- **Incremental Indexing**: Optimize index update strategy, avoid full rebuilds
- **Vector Retrieval**: Add image similarity search (based on CLIP embeddings)
- **Web Interface**: Provide Web UI for visual search and management
- **Distributed Deployment**: Support multi-machine collaborative processing for large-scale image libraries

---

**Document Version**: v1.0
**Last Updated**: 2024-02-04
