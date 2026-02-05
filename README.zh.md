[English](README.md) | [中文](README.zh.md)

---

# LocalImageSearch

本地图片自动标注与搜索系统。使用视觉语言模型（通过 Ollama / OpenAI 兼容接口 / 本地模型）自动为图片生成标签和描述，结果存入 SQLite 数据库，并构建倒排索引和全文搜索索引供后续检索使用。

---

## 功能特性

- **多后端支持**: Ollama、OpenAI 兼容 API、本地 Transformers 模型、Google Gemini
- **多语言标签**: 英文、中文、日文、韩文、西班牙语、法语、德语、俄语
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
git clone <repo-url>
cd project-scripts-tag

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## 快速开始

以下以 Ollama + qwen3-vl:4b 为例（需提前 `ollama pull qwen3-vl:4b`）:

```bash
# 处理单个图片，生成 10 个中文标签
python src/main.py --image-path /path/to/image.jpg --model qwen3-vl:4b --language zh

# 处理整个目录，同时生成标签和描述
python src/main.py --image-path /path/to/images/ --model qwen3-vl:4b --language zh --description

# 搜索结果
python src/index_builder.py search "人工智能" --mode tag
```

处理完成后，标签存入 `data/image_tags.db`，索引自动构建。

---

## 详细使用

### 模型类型

| 类型 | `--model-type` | 说明 |
|------|----------------|------|
| Ollama | `ollama`（默认） | 本地 Ollama 服务，端口 11434 |
| OpenAI 兼容 | `openai` | vLLM / 云厂商 API 均可 |
| 本地模型 | `local` | 通过 Transformers 直接加载模型文件 |
| Gemini | `gemini` | Google Gemini API |

```bash
# Ollama (默认)
python src/main.py --image-path ./images --model qwen3-vl:4b

# OpenAI 兼容 API
python src/main.py --image-path ./images \
  --model qwen-vl-chat \
  --model-type openai \
  --api-base http://localhost:8000/v1 \
  --api-key your-key

# 本地模型文件
python src/main.py --image-path ./images \
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
| `--language` | `en` | 标签语言 |
| `--tag-count` | `10` | 生成标签数量 |
| `--resize` | `512x512` | 图片缩放尺寸 |
| `--description` | `false` | 开启描述生成 |
| `--db-path` | `./data/image_tags.db` | 数据库路径 |
| `--reprocess` | `false` | 强制重处理已有记录 |
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
