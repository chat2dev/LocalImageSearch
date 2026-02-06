[English](README.md) | [中文](README.zh.md)

---

# LocalImageSearch

本地图片自动标注与搜索系统。使用视觉语言模型（通过 Ollama / OpenAI 兼容接口 / 本地模型）自动为图片生成标签和描述，结果存入 SQLite 数据库，并构建倒排索引和全文搜索索引供后续检索使用。

---

## 功能特性

- **多后端支持**: Ollama、OpenAI 兼容 API、本地 Transformers 模型、Google Gemini
- **多语言标签**: 英文、中文、日文、韩文、西班牙语、法语、德语、俄语
- **并行处理**: 支持多线程并行标注，可配置并行度（默认 5 个线程）
- **增量处理**: 自动跳过已处理图片，中断后可续跑
- **自动索引**: 处理完成后自动构建倒排索引和 FTS5 全文搜索索引
- **可配置 Prompt**: 通过 YAML 文件自定义模型提示词
- **图片描述生成**: 可选开启，独立调用模型生成详细描述

---

## 环境要求

- Python >= 3.8.1
- [uv](https://docs.astral.sh/uv/) (推荐) 或 pip
- 至少一种模型后端:
  - [Ollama](https://ollama.ai) (默认，需本地运行服务)
  - OpenAI 兼容推理服务 (vLLM / Together / 云厂商 API 等)
  - 本地 GPU + transformers 环境
  - Google Gemini API

---

## 安装

```bash
# 克隆仓库
git clone https://github.com/chat2dev/LocalImageSearch.git
cd LocalImageSearch

# 创建虚拟环境并安装依赖
uv sync
```

完成！现在可以使用默认设置开始使用系统。高级配置选项请参见[配置](#配置)章节。

---

## 快速开始

### 步骤 1：初始化数据库

首次使用需要初始化数据库：

```bash
uv run python scripts/init_database.py
```

这将创建 `~/.LocalImageSearch/data/image_tags.db` 并建立所有必要的表结构。

### 步骤 2：标注图片（命令行）

使用默认设置标注图片：

```bash
# 标注目录中的图片（默认中文标签）
uv run python src/main.py --image-path /path/to/images/

# 搜索结果
uv run python src/index_builder.py search "人工智能" --mode tag
```

系统将：
- 使用 Qwen3-VL 模型（通过 Ollama）处理图片
- 为每张图片生成 10 个中文标签
- 保存到 `~/.LocalImageSearch/data/image_tags.db`
- 自动构建搜索索引

### 步骤 3：浏览图片（Web 界面）

启动 Web 界面：

```bash
cd ui
npm run dev
```

在浏览器中打开 [http://localhost:3000](http://localhost:3000)。

功能：标签云、多标签筛选、全文搜索、图片查看器。

> **提示**：可以多次运行标注命令处理不同目录，新图片会添加到现有数据库中。

---

## 详细使用

### 模型类型

| 类型 | `--model-type` | 说明 |
|------|----------------|------|
| Ollama | `ollama`（默认） | 本地 Ollama 服务，端口 11434 |
| OpenAI 兼容 | `openai` | vLLM / 豆包 / OpenAI / Together AI 等云厂商 API |
| 本地模型 | `local` | 通过 Transformers 直接加载模型文件 |
| Gemini | `gemini` | Google Gemini API |

#### 使用 Ollama（默认推荐）

```bash
# Ollama 使用默认模型
uv run python src/main.py --image-path ./images

# Ollama 指定模型
uv run python src/main.py --image-path ./images --model qwen3-vl:4b
```

#### 使用 OpenAI 兼容 API

**通用 OpenAI 兼容 API：**
```bash
uv run python src/main.py --image-path ./images \
  --model-type openai \
  --model your-model-name \
  --api-base http://localhost:8000/v1 \
  --api-key your-api-key
```

**豆包（Doubao）API：**

豆包 API 使用不同的 URL 结构，base URL 已包含版本号（`/api/v3`）：

```bash
# 步骤 1：设置环境变量（推荐）
export DOUBAO_API_KEY="your-doubao-api-key"
export DOUBAO_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
export DOUBAO_MODEL_NAME="ep-xxxxxxxxxxxxx-xxxxx"

# 步骤 2：使用豆包运行
uv run python src/main.py --image-path ./images \
  --model-type openai \
  --model "$DOUBAO_MODEL_NAME" \
  --api-base "$DOUBAO_BASE_URL" \
  --api-key "$DOUBAO_API_KEY" \
  --language zh
```

**使用 .env 文件配置豆包：**
```bash
# 创建 .env 文件
cat > .env << 'EOF'
MODEL_TYPE=openai
MODEL_NAME=${DOUBAO_MODEL_NAME}
API_BASE=${DOUBAO_BASE_URL}
API_KEY=${DOUBAO_API_KEY}
LANGUAGE=zh
TAG_COUNT=10
MAX_WORKERS=5
EOF

# 运行（自动使用环境变量配置）
uv run python src/main.py --image-path ./images
```

**OpenAI 兼容 API 重要说明：**
- **URL 格式**：如果 API base URL 已包含版本号（如 `/v3`），系统会自动检测，无需手动添加 `/v1`
- **豆包特殊配置**：
  - 模型名称是 endpoint ID（格式：`ep-xxxxxxxxxxxxx-xxxxx`）
  - Base URL 包含 `/api/v3`
  - 最小图片尺寸：14×14 像素
- **测试指南**：查看 `tests/README_DOUBAO.md` 了解豆包测试方法

**本地模型文件：**
```bash
uv run python src/main.py --image-path ./images \
  --model minicpm-v \
  --model-type local \
  --model-path /path/to/MiniCPM-V-2_5
```

### 语言支持

通过 `--language` 指定标签和描述的语言:

| 代码 | 语言 | 代码 | 语言 |
|------|------|------|------|
| `en` | English | `ko` | Korean |
| `zh` | Chinese | `es` | Spanish |
| `ja` | Japanese | `fr` | French |
| | | `de` | German |
| | | `ru` | Russian |

### 全部 CLI 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--image-path` | (必填) | 图片文件或目录路径 |
| `--model` | `qwen3-vl:4b` | 模型名称 |
| `--model-type` | `ollama` | 模型后端类型 |
| `--model-path` | — | 本地模型路径 (local 模式) |
| `--api-base` | — | API 地址 (openai 模式) |
| `--api-key` | — | API 密钥 (openai 模式) |
| `--language` | `zh` | 标签语言 (zh/en/ja/ko/es/fr/de/ru) |
| `--tag-count` | `10` | 生成标签数量 |
| `--resize` | `512x512` | 图片缩放尺寸 |
| `--description` | `false` | 开启描述生成 |
| `--db-path` | `./data/image_tags.db` | 数据库路径 |
| `--reprocess` | `false` | 强制重新处理已标注图片 |
| `--max-workers` | `5` | 并行处理线程数（1=串行） |
| `--batch-size` | `100` | 每次运行处理的最大图片数（不含已处理） |
| `--prompt-config` | `prompts.yaml` | 自定义 Prompt 配置文件 |

### YAML 配置文件

所有 CLI 参数均可通过配置文件指定:

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

### 自定义 Prompt

复制 `prompts_custom_example.yaml` 为模板，修改后通过 `--prompt-config` 使用:

```bash
cp prompts_custom_example.yaml my_prompts.yaml
# 编辑 my_prompts.yaml ...
python src/main.py --image-path ./images --model qwen3-vl:4b --language zh \
  --prompt-config my_prompts.yaml
```

Prompt 模板支持变量: `{language}`、`{language_name}`、`{tag_count}`。

---

## 配置

对于高级使用场景，可以使用 `.env` 文件或 CLI 参数自定义系统行为。

### 配置优先级

1. **CLI 参数**（最高）- 覆盖所有配置
2. **.env 文件** - 重复使用的默认值
3. **内置默认值**（最低）

### 创建 .env 文件

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置
nano .env
```

**示例 .env 文件：**
```bash
# 模型配置
MODEL_NAME=qwen3-vl:4b
MODEL_TYPE=ollama
LANGUAGE=zh
TAG_COUNT=10

# 图片处理
IMAGE_RESIZE=512x512
GENERATE_DESCRIPTION=false
MAX_WORKERS=5  # 并行处理线程数（1=串行，5=默认）
BATCH_SIZE=100  # 每次最多处理图片数，不含已处理（0=不限制）

# 数据库路径（支持环境变量引用）
DB_PATH=${HOME}/.LocalImageSearch/data/image_tags.db

# OpenAI 兼容 API 配置
# API_BASE=http://localhost:8000/v1
# API_KEY=your-api-key
```

有了 `.env` 文件，命令会更简洁：
```bash
# 自动使用 .env 中的值
uv run python src/main.py --image-path ~/Pictures

# CLI 参数会覆盖 .env 中的值
uv run python src/main.py --image-path ~/Pictures --language en --tag-count 20
```

### 环境变量展开

`.env` 文件支持使用 `${VAR}` 语法引用系统环境变量：

```bash
# 使用 ${HOME} 引用用户主目录
DB_PATH=${HOME}/.LocalImageSearch/data/image_tags.db
FAISS_INDEX_DIR=${HOME}/.LocalImageSearch/faiss

# 其他环境变量也可以使用
CUSTOM_PATH=${HOME}/Documents/images
```

**注意**：必须使用 `${VAR}` 语法（带花括号），不支持 `$VAR` 格式。

### 并行处理配置

根据系统内存配置 `MAX_WORKERS`：

| 系统内存     | 推荐 MAX_WORKERS | 说明 |
|-------------|------------------|------|
| 8GB 及以下  | 1-2              | 使用串行或最小并行度 |
| 16GB        | 3-5              | 默认配置表现良好 |
| 32GB        | 5-10             | 可使用较高并行度 |
| 64GB 以上   | 10-20            | 大批量处理时性能最佳 |

**性能预期：**
- **小批量（<20张图片）**：并行处理提升 6-9%
- **大批量（>100张图片）**：可能有更多提升，但受 Ollama 限制
- **瓶颈**：等待 Ollama API 响应（I/O 密集型）
- **限制**：Ollama 可能内部串行化请求，限制并行收益
- **警告**：过多 workers（>5）可能导致 API 超时

**基准测试结果：**

*测试1：5张图片*
- 串行（1 worker）：22.8秒
- 并行（3 workers）：20.8秒（提升 9%）
- 并行（5 workers）：19.4秒（提升 15%）

*测试2：17张图片*
- 串行（1 worker）：95.9秒
- 并行（3 workers）：89.6秒（提升 6.6%）
- 并行（5 workers）：87.8秒（提升 8.5%）
- 并行（10 workers）：80.1秒但3张失败（超时）

### Ollama 配置优化

为了获得更好的并行性能，需要配置 Ollama 支持更多并发请求：

```bash
# 停止 Ollama（如果在运行）
pkill ollama

# 启动 Ollama 并增加并行度（允许6个并发请求）
OLLAMA_NUM_PARALLEL=6 ollama serve
```

使用此配置后，性能提升更明显：
- 3 workers：提升 8.5%（默认配置仅 6.6%）
- 5 workers：提升 9.3%（默认配置仅 8.5%）

**注意事项：**
- 每个 worker 会将模型加载到内存中
- 视觉语言模型通常每个 worker 占用 2-4GB 内存
- 处理过程中监控系统资源（内存、CPU）使用情况
- 如遇内存不足错误，请降低 `MAX_WORKERS` 值
- 小批量处理时，串行模式可能已足够
- **推荐配置**：`OLLAMA_NUM_PARALLEL=6` + `MAX_WORKERS=5`

### 批处理配置

为避免处理时间过长，可以限制每次运行处理的图片数：

```bash
# 每次处理 100 张图片（默认）
uv run python src/main.py --image-path /path/to/large-collection/

# 每次处理 50 张图片
uv run python src/main.py --image-path /path/to/large-collection/ --batch-size 50

# 处理所有图片（不限制）
uv run python src/main.py --image-path /path/to/large-collection/ --batch-size 0
```

**注意**：`BATCH_SIZE` 只计数未处理的图片。已处理的图片会自动跳过（除非使用 `--reprocess`）。

### 使用豆包（Doubao）API

豆包是字节跳动的视觉语言模型 API。使用方法：

```bash
# 步骤 1：设置环境变量（首次使用）
export DOUBAO_API_KEY="your-doubao-api-key"
export DOUBAO_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
export DOUBAO_MODEL_NAME="ep-xxxxxxxxxxxxx-xxxxx"

# 步骤 2：使用豆包运行
uv run python src/main.py \
  --image-path /path/to/images/ \
  --model-type openai \
  --model "$DOUBAO_MODEL_NAME" \
  --api-base "$DOUBAO_BASE_URL" \
  --api-key "$DOUBAO_API_KEY" \
  --language zh
```

**使用 .env 文件配置豆包：**
```bash
# 创建 .env 文件
cat > .env << 'EOF'
MODEL_TYPE=openai
MODEL_NAME=${DOUBAO_MODEL_NAME}
API_BASE=${DOUBAO_BASE_URL}
API_KEY=${DOUBAO_API_KEY}
LANGUAGE=zh
TAG_COUNT=10
MAX_WORKERS=5
EOF

# 运行（会自动使用环境变量）
uv run python src/main.py --image-path ./images
```

**性能**：豆包处理单张图片约需 6-8 秒（使用 512×512 缩放后的图片）。

> **豆包测试指南**：详见 `tests/README_DOUBAO.md` 了解测试方法和故障排除。

---

## 索引与搜索

每次处理完成后，`main.py` 自动调用 `IndexBuilder` 构建两层索引。也可手动触发:

```bash
python src/index_builder.py build
```

### 索引结构

| 索引 | 表名 | 机制 | 适用场景 |
|------|------|------|----------|
| 倒排索引 | `tag_index` | 逗号分割的 tag 逐个映射到图片 ID | 精确 tag 筛选 |
| 全文索引 | `image_fts` | FTS5 虚拟表，对 tags + description 分词索引 | 自由关键词搜索 |

### 搜索命令

```bash
# 单 tag 精确匹配
python src/index_builder.py search "网络安全" --mode tag

# 多 tag 并集 (匹配任一)
python src/index_builder.py search "智能,代码" --mode tags --match any

# 多 tag 交集 (必须同时包含)
python src/index_builder.py search "智能,代码" --mode tags --match all

# 关键词搜索 (支持子串，如 "智能" 可匹配 "人工智能")
python src/index_builder.py search "智能" --mode fts

# 查看高频 tag 统计
python src/index_builder.py stats
```

### FTS 搜索语法

当 `description` 有内容时，`--mode fts` 可在描述文本中做更精细的搜索:

| 语法 | 含义 | 示例 |
|------|------|------|
| `词` | 单 token 匹配 | `人工智能` |
| `词A 词B` | AND（默认） | `人工智能 机器人` |
| `词A OR 词B` | OR | `人工智能 OR 机器学习` |
| `词A NOT 词B` | 排除 | `智能 NOT 机器` |
| `列:词` | 指定列搜索 | `tags:人工智能` |

> 注意: FTS5 做的是 token 级别匹配，不是子串匹配。`--mode fts` 会在 FTS 无结果时自动 fallback 到 LIKE 子串搜索，因此日常使用 `--mode fts` 即可。

---

## 数据库操作

数据库为 SQLite，默认路径 `data/image_tags.db`。

```bash
# 查看表结构
python src/show_table_structure.py

# 直接用 sqlite3 查询
sqlite3 data/image_tags.db "SELECT * FROM image_tags LIMIT 10;"
sqlite3 data/image_tags.db "SELECT tag, COUNT(*) as cnt FROM tag_index GROUP BY tag ORDER BY cnt DESC LIMIT 20;"

# 导出为 CSV
sqlite3 -header -csv data/image_tags.db "SELECT * FROM image_tags;" > tags.csv
```

### 数据库表说明

| 表 | 说明 |
|----|------|
| `image_tags` | 主数据表，存储每张图片的标签、描述和元数据 |
| `tag_index` | 倒排索引表，tag → image_id 映射 |
| `image_fts` | FTS5 全文搜索虚拟表 |

### 工具脚本

```bash
# 提取目录下所有图片路径到文件
python src/extract_image_paths.py --directory /path/to/images --output paths.txt

# 提取相对路径
python src/extract_image_paths.py --directory /path/to/images --output paths.txt --relative

# 不递归子目录
python src/extract_image_paths.py --directory /path/to/images --output paths.txt --no-recursive
```

---

## 项目结构

```
.
├── src/
│   ├── main.py               # 主入口，编排整体流程
│   ├── config.py             # CLI 参数解析与配置管理
│   ├── tagging.py            # 标注流程协调
│   ├── image_processor.py    # 图片加载、预处理、编码
│   ├── models.py             # 模型后端抽象层 (Ollama / OpenAI / Local / Gemini)
│   ├── prompt_manager.py     # Prompt 模板管理
│   ├── database.py           # SQLite CRUD 操作
│   ├── index_builder.py      # 倒排索引 + FTS5 索引构建与搜索
│   ├── utils.py              # 工具函数 (唯一 ID 生成、图片文件发现)
│   ├── extract_image_paths.py # 批量提取图片路径
│   ├── show_table_structure.py # 展示数据库表结构
│   ├── download_model.py     # 模型下载辅助
│   └── benchmark_models.py   # 模型基准测试
├── doc/                      # 详细文档 (见下)
├── data/                     # 数据库存储目录
├── models/                   # 本地模型文件目录
├── test_images/              # 测试图片
├── prompts.yaml              # 默认 Prompt 配置
├── prompts_custom_example.yaml # 自定义 Prompt 模板示例
├── benchmark_config.example.json # 基准测试配置示例
├── pyproject.toml
└── requirements.txt
```

### 数据流

```
CLI / YAML 配置
    ↓
图片文件发现 (单文件 / 目录递归)
    ↓
对每张图片:
    生成唯一 ID (SHA-256(绝对路径))
    ↓ 数据库查找 → 已存在则跳过
    ↓
    图片预处理 (→ RGB → resize → JPEG 编码)
    ↓
    调用模型 API → 解析标签
    ↓ (可选) 调用模型生成描述
    ↓
    写入 image_tags 表
        ↓
处理完成 → 构建 tag_index + image_fts 索引
```

---

## 深入阅读

| 文档 | 内容 |
|------|------|
| [doc/model_recommendations.md](doc/model_recommendations.md) | 模型选择指南、资源要求对比、下载方式 |
| [doc/performance_optimization.md](doc/performance_optimization.md) | 并发处理、模型量化、预处理优化等加速策略 |
| [doc/installation.md](doc/installation.md) | 详细安装步骤与常见问题 |
| [doc/usage.md](doc/usage.md) | 完整使用教程 |
| [doc/benchmark_guide.md](doc/benchmark_guide.md) | 模型基准测试说明 |
| [doc/changelog.md](doc/changelog.md) | 版本变更记录 |

---

## 依赖

| 包 | 用途 |
|----|------|
| Pillow | 图片加载与预处理 |
| requests | HTTP 客户端 (Ollama / OpenAI API) |
| PyYAML | 配置文件解析 |
| tqdm | 处理进度条 |
| sqlite3 | 数据库 (Python 内置) |
