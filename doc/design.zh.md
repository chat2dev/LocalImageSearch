[English](design.md) | [中文](design.zh.md)

---

# 系统设计文档

**LocalImageSearch - 图片自动标注与搜索系统**

本文档描述系统的整体架构、核心模块设计、数据流、索引机制及扩展性考虑。

---

## 目录

1. [系统概述](#1-系统概述)
2. [架构设计](#2-架构设计)
3. [核心模块设计](#3-核心模块设计)
4. [数据流设计](#4-数据流设计)
5. [模型抽象层设计](#5-模型抽象层设计)
6. [索引系统设计](#6-索引系统设计)
7. [Prompt 管理设计](#7-prompt-管理设计)
8. [配置管理设计](#8-配置管理设计)
9. [错误处理与状态跟踪](#9-错误处理与状态跟踪)
10. [扩展性设计](#10-扩展性设计)
11. [性能优化考虑](#11-性能优化考虑)

---

## 1. 系统概述

### 1.1 目标

构建一个本地化的图片自动标注与检索系统，具备以下能力：

- 自动生成图片标签和描述
- 支持多种视觉语言模型后端
- 多语言标签生成（8 种语言）
- 增量处理，避免重复计算
- 高效的标签检索（精确匹配 + 全文搜索）

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **模块化** | 各组件职责单一，接口清晰 |
| **可扩展** | 易于添加新模型、新语言、新索引方式 |
| **增量式** | 支持中断续跑，避免重复处理 |
| **无侵入** | 仅读取图片，不修改原文件 |
| **本地优先** | 优先支持本地模型，降低 API 成本 |

---

## 2. 架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        应用层 (CLI)                          │
│                  main.py + config.py                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                        业务逻辑层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ tagging.py   │  │ index_builder│  │ prompt_mgr   │      │
│  │ (标注协调)   │  │ (索引构建)   │  │ (Prompt管理) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                        数据访问层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ models.py    │  │ database.py  │  │ image_proc   │      │
│  │ (模型抽象)   │  │ (数据库操作) │  │ (图片处理)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                        基础设施层                             │
│     Ollama API / OpenAI API / 本地模型 / SQLite / FTS5      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **应用入口** | `main.py` | CLI 入口，编排整体流程 |
| **配置管理** | `config.py` | 解析 CLI 参数和 YAML 配置 |
| **标注协调** | `tagging.py` | 协调图片处理、模型调用、数据存储 |
| **模型抽象** | `models.py` | 统一多种模型后端的调用接口 |
| **图片处理** | `image_processor.py` | 图片加载、预处理、编码 |
| **数据库** | `database.py` | SQLite CRUD 操作 |
| **索引系统** | `index_builder.py` | 倒排索引 + FTS5 全文搜索 |
| **Prompt 管理** | `prompt_manager.py` | 多语言 Prompt 模板加载 |
| **工具函数** | `utils.py` | 文件发现、唯一 ID 生成 |

---

## 3. 核心模块设计

### 3.1 main.py - 应用入口

**职责：**
- 解析配置（CLI / YAML）
- 发现待处理图片文件
- 循环调用 `process_image` 处理每张图片
- 处理完成后触发索引构建
- 输出统计信息

**关键逻辑：**
```python
config = Config().parse_args()
image_files = get_image_files(config.image_path)
db = Database(config.db_path)

for image_path in image_files:
    process_image(image_path, config, db)

# 处理完成后自动构建索引
IndexBuilder(db_path).build()
```

### 3.2 tagging.py - 标注流程协调

**职责：**
- 生成图片唯一 ID（SHA-256）
- 检查数据库，跳过已处理图片
- 调用 `image_processor` 预处理图片
- 调用模型生成标签和描述
- 解析模型输出，提取标签
- 将结果写入数据库

**核心函数签名：**
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
    """处理单张图片，返回是否成功"""
```

**状态记录：**
- 成功: `status='success'`, 记录 tags, description, processing_time
- 失败: `status='failed'`, 记录 error_message

### 3.3 models.py - 模型抽象层

**设计模式：** 策略模式 (Strategy Pattern)

**接口定义：**
```python
class BaseModel:
    def generate_tags(self, image_bytes: bytes, prompt: str) -> str:
        """生成标签，返回模型原始输出"""
        raise NotImplementedError

    def generate_description(self, image_bytes: bytes, prompt: str) -> str:
        """生成描述，返回模型原始输出"""
        raise NotImplementedError
```

**实现类：**
- `OllamaModel`: Ollama 本地服务（默认）
- `OpenAIModel`: OpenAI 兼容 API（vLLM / 云厂商）
- `LocalModel`: Transformers 本地模型文件
- `GeminiModel`: Google Gemini API

**工厂函数：**
```python
def get_model(model_type: str, model_name: str, **kwargs) -> BaseModel:
    """根据 model_type 返回对应的模型实例"""
```

### 3.4 image_processor.py - 图片处理

**职责：**
- 加载图片（支持 JPEG, PNG, BMP, GIF, WEBP）
- 转换为 RGB 模式
- 缩放至目标尺寸（强制 resize，不保持比例）
- 编码为 JPEG bytes（用于模型 API）
- 返回原始元数据（宽度、高度、格式）

**关键函数：**
```python
def load_and_preprocess_image(
    image_path: str,
    target_width: int,
    target_height: int
) -> Tuple[bytes, dict]:
    """返回 (JPEG bytes, metadata)"""
```

### 3.5 database.py - 数据库操作

**职责：**
- 管理 SQLite 连接生命周期
- 创建 `image_tags` 表和索引
- 提供 CRUD 方法

**核心方法：**
```python
class Database:
    def insert_tag(self, image_unique_id, image_path, tags, ...):
        """插入或替换标签记录"""

    def get_tags_by_image_id(self, image_unique_id):
        """查询单条记录（用于去重）"""

    def get_all_tags(self):
        """查询所有记录"""
```

**表结构：** 见 [doc/table-design.md](table-design.md)

### 3.6 index_builder.py - 索引系统

见 [第 6 节：索引系统设计](#6-索引系统设计)

### 3.7 prompt_manager.py - Prompt 管理

**职责：**
- 从 YAML 文件加载 Prompt 模板
- 根据语言和任务类型选择 Prompt
- 替换模板变量（`{language}`, `{tag_count}` 等）

**核心方法：**
```python
class PromptManager:
    def get_tag_prompt(self, language: str, tag_count: int) -> str:
        """获取标签生成 Prompt"""

    def get_description_prompt(self, language: str) -> str:
        """获取描述生成 Prompt"""
```

### 3.8 utils.py - 工具函数

**关键函数：**
```python
def generate_unique_id(image_path: str) -> str:
    """SHA-256(绝对路径) → 唯一 ID"""

def get_image_files(directory: str) -> List[str]:
    """递归扫描目录，返回所有图片文件路径"""
```

---

## 4. 数据流设计

### 4.1 标注流程

```
用户输入 (CLI / YAML)
    ↓
Config 解析 → 配置对象
    ↓
图片文件发现 → List[image_path]
    ↓
循环处理每张图片:
    ├─ 生成 unique_id = SHA256(abs_path)
    ├─ 数据库查重 → 已存在？→ 跳过
    ├─ 图片预处理 → (image_bytes, metadata)
    ├─ 加载 Prompt 模板 → (tag_prompt, desc_prompt)
    ├─ 调用模型:
    │   ├─ generate_tags(image_bytes, tag_prompt) → raw_output
    │   ├─ 解析 tags → List[str]
    │   └─ (可选) generate_description(image_bytes, desc_prompt)
    ├─ 写入数据库:
    │   └─ INSERT (unique_id, path, tags, desc, model, ..., status, time)
    └─ 返回 success/failed
        ↓
所有图片处理完成
    ↓
IndexBuilder.build() → 构建倒排索引 + FTS5
    ↓
输出统计 → 成功数、失败数、数据库路径
```

### 4.2 搜索流程

```
用户搜索请求 (CLI)
    ↓
IndexSearcher(db_path)
    ↓
根据搜索模式:
    ├─ --mode tag → search_by_tag(tag)
    │   └─ SELECT FROM tag_index WHERE tag = ?
    │
    ├─ --mode tags → search_by_tags(tags, match='any'|'all')
    │   ├─ match=any → tag IN (...)
    │   └─ match=all → GROUP BY ... HAVING COUNT = ?
    │
    └─ --mode fts → search_keyword(query)
        ├─ 第一步: FTS5 MATCH → 有结果？→ 返回
        └─ 第二步: LIKE fallback → tag LIKE %query%
            ↓
返回 List[{id, path, tags, description}]
    ↓
格式化输出 → 文件名 + tags + desc
```

---

## 5. 模型抽象层设计

### 5.1 设计目标

- **统一接口**: 不同模型后端使用相同的调用方式
- **易扩展**: 添加新模型只需实现 `BaseModel` 接口
- **配置驱动**: 通过 `model_type` 参数切换模型

### 5.2 接口设计

```python
class BaseModel:
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        # kwargs 接收 api_base, api_key, model_path 等参数

    def generate_tags(self, image_bytes: bytes, prompt: str) -> str:
        """输入图片和 Prompt，返回模型原始输出"""
        raise NotImplementedError

    def generate_description(self, image_bytes: bytes, prompt: str) -> str:
        """输入图片和 Prompt，返回模型原始输出"""
        raise NotImplementedError
```

### 5.3 实现类对比

| 类 | 通信方式 | 依赖 | 优势 | 劣势 |
|----|----------|------|------|------|
| `OllamaModel` | HTTP API (localhost:11434) | requests | 部署简单，支持多模型切换 | 需要本地运行 Ollama 服务 |
| `OpenAIModel` | HTTP API (自定义 endpoint) | requests | 兼容性强，支持云服务 | 需要 API key，可能有费用 |
| `LocalModel` | Python 直接调用 | transformers, torch | 完全本地化，无网络依赖 | 内存占用大，初始化慢 |
| `GeminiModel` | HTTP API (Google) | requests | 云端大模型，质量高 | 需要 API key，有调用限制 |

### 5.4 工厂模式

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

### 5.5 标签解析策略

模型输出格式不统一，需要统一的解析逻辑：

```python
def parse_tags(raw_output: str, language: str) -> List[str]:
    """从模型原始输出中提取标签列表"""
    # 1. 提取 "标签:" 或 "Tags:" 后的内容
    # 2. 按语言选择正则表达式:
    #    - 中文: [\u4e00-\u9fff]+
    #    - 英文: [a-zA-Z]+
    #    - 日文: [\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+
    #    ...
    # 3. 去重、过滤空值
    # 4. 返回 List[str]
```

---

## 6. 索引系统设计

### 6.1 设计目标

- **精确检索**: 支持 tag 精确匹配、多 tag 交集/并集
- **模糊检索**: 支持关键词子串匹配、全文搜索
- **高性能**: 利用数据库索引，避免全表扫描
- **自动更新**: 标注流程结束后自动刷新索引

### 6.2 双层索引架构

```
image_tags (主表)
    ├─ 基础索引 (B-Tree)
    │   ├─ idx_image_unique_id
    │   ├─ idx_model_name
    │   └─ idx_generated_at
    │
    ├─ tag_index (倒排索引)
    │   ├─ 表结构: (tag, image_id, image_unique_id)
    │   ├─ 索引: idx_ti_tag, idx_ti_image_id
    │   └─ 用途: 精确 tag 查询、多 tag 组合
    │
    └─ image_fts (FTS5 全文索引)
        ├─ 虚拟表: (tags, description)
        ├─ tokenize: unicode61 (默认 CJK 分词)
        └─ 用途: 关键词搜索、相关度排序
```

### 6.3 倒排索引 (tag_index) 设计

**表结构：**
```sql
CREATE TABLE tag_index (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tag             TEXT    NOT NULL,
    image_id        INTEGER NOT NULL,  -- 外键 -> image_tags.id
    image_unique_id TEXT    NOT NULL,
    UNIQUE(tag, image_id)
);

CREATE INDEX idx_ti_tag      ON tag_index(tag);
CREATE INDEX idx_ti_image_id ON tag_index(image_id);
```

**构建流程：**
```python
# 全量重建
DELETE FROM tag_index;

for row in SELECT id, tags FROM image_tags WHERE status='success':
    for tag in row.tags.split(','):
        INSERT INTO tag_index (tag, image_id, image_unique_id)
        VALUES (tag.strip(), row.id, row.unique_id);
```

**查询示例：**
```python
# 单 tag 精确匹配
SELECT it.* FROM tag_index ti
JOIN image_tags it ON ti.image_id = it.id
WHERE ti.tag = '人工智能';

# 多 tag 并集 (any)
WHERE ti.tag IN ('人工智能', '机器学习');

# 多 tag 交集 (all)
WHERE ti.tag IN ('人工智能', '机器学习')
GROUP BY it.id
HAVING COUNT(DISTINCT ti.tag) = 2;  -- 必须匹配所有 tag
```

### 6.4 FTS5 全文索引 (image_fts) 设计

**虚拟表结构：**
```sql
CREATE VIRTUAL TABLE image_fts USING fts5(
    tags,
    description,
    tokenize = 'unicode61'
);

-- rowid 与 image_tags.id 对齐
INSERT INTO image_fts(rowid, tags, description)
SELECT id, REPLACE(tags, ',', ' '), COALESCE(description, '')
FROM image_tags WHERE status='success';
```

**tokenize 机制：**
- `REPLACE(tags, ',', ' ')`: 将逗号替换为空格，使每个 tag 成为独立 token
- `unicode61`: 默认分词器，CJK 字符序列作为单个 token
- 例如: `"人工智能,机器学习"` → `"人工智能 机器学习"` → tokens: `["人工智能", "机器学习"]`

**搜索策略：**
```python
def search_keyword(query: str):
    # 第一步: FTS5 精确 token 匹配
    results = fts.MATCH(query)
    if results:
        return results

    # 第二步: LIKE 子串匹配 (fallback)
    results = tag_index WHERE tag LIKE %query%
    return results
```

**FTS5 查询语法：**
```sql
-- 单词匹配
WHERE image_fts MATCH '人工智能';

-- AND 查询 (默认)
WHERE image_fts MATCH '人工智能 机器人';

-- OR 查询
WHERE image_fts MATCH '人工智能 OR 机器学习';

-- NOT 排除
WHERE image_fts MATCH '智能 NOT 机器';

-- 指定列搜索
WHERE image_fts MATCH 'tags:人工智能';
```

### 6.5 索引更新策略

**更新时机：**
1. `main.py` 处理完所有图片后自动调用 `IndexBuilder.build()`
2. 用户手动执行 `python src/index_builder.py build`

**更新方式：**
- **全量重建** (当前实现)
  - 优点: 简单、一致性强
  - 缺点: 图片数量大时耗时较长

- **增量更新** (未来优化)
  - 仅处理新增/变更的 image_tags 记录
  - 需要维护 `last_indexed_at` 时间戳

**性能优化：**
```python
# 批量插入，关闭事务自动提交
conn.execute("BEGIN TRANSACTION")
for tag_record in tag_records:
    conn.execute("INSERT INTO tag_index ...")
conn.execute("COMMIT")
```

### 6.6 IndexSearcher API 设计

```python
class IndexSearcher:
    def search_by_tag(self, tag: str) -> List[Dict]:
        """单 tag 精确匹配"""

    def search_by_tags(self, tags: List[str], mode: str) -> List[Dict]:
        """多 tag 匹配，mode='any'|'all'"""

    def search_fulltext(self, query: str) -> List[Dict]:
        """FTS5 全文搜索"""

    def search_keyword(self, keyword: str) -> List[Dict]:
        """智能搜索: FTS → LIKE fallback"""

    def get_tag_stats(self) -> List[Dict]:
        """返回所有 tag 及其频率"""

    def get_similar_tags(self, keyword: str) -> List[Dict]:
        """模糊匹配 tag (LIKE %keyword%)"""
```

---

## 7. Prompt 管理设计

### 7.1 YAML 配置结构

```yaml
# prompts.yaml
system_prompts:
  zh: "你是一个图片标签生成器..."
  en: "You are a vision AI..."
  default: "..."

tag_prompts:
  zh: "请为这张图片生成{tag_count}个中文标签..."
  en: "List {tag_count} tags..."
  default: "..."

description_prompts:
  zh: "请用中文详细描述这张图片..."
  en: "Describe this image in detail..."
  default: "..."

language_names:
  zh: "Chinese"
  en: "English"
  ja: "Japanese"
  ...
```

### 7.2 PromptManager 实现

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

### 7.3 扩展新语言

1. 在 `prompts.yaml` 中添加对应语言的 `tag_prompts` 和 `description_prompts`
2. 在 `language_names` 中添加语言名称映射
3. 在 `models.py` 的 `parse_tags` 函数中添加该语言的正则表达式
4. 在 `config.py` 的 `--language` choices 中添加新语言代码

---

## 8. 配置管理设计

### 8.1 配置来源优先级

```
CLI 参数 > YAML 配置文件 > 默认值
```

### 8.2 Config 类设计

```python
class Config:
    # 默认值
    model = "qwen3-vl:4b"
    model_type = "ollama"
    language = "en"
    tag_count = 10
    resize = "512x512"
    db_path = "./data/image_tags.db"
    ...

    def parse_args(self):
        """解析 CLI 参数，覆盖默认值"""
        parser = argparse.ArgumentParser()
        parser.add_argument('--model', ...)
        parser.add_argument('--config', help='YAML 配置文件路径')
        args = parser.parse_args()

        # 先加载 YAML (如果提供)
        if args.config:
            self.load_yaml(args.config)

        # 再用 CLI 参数覆盖
        if args.model:
            self.model = args.model
        ...

    def load_yaml(self, path: str):
        """从 YAML 文件加载配置"""
        with open(path) as f:
            config = yaml.safe_load(f)
        for key, value in config.items():
            setattr(self, key, value)
```

### 8.3 配置验证

```python
def validate(self):
    """验证配置合法性"""
    if self.model_type == 'local' and not self.model_path:
        raise ValueError("model_type=local requires model_path")

    if self.model_type == 'openai' and not self.api_base:
        raise ValueError("model_type=openai requires api_base")

    if self.tag_count < 1:
        raise ValueError("tag_count must be >= 1")
```

---

## 9. 错误处理与状态跟踪

### 9.1 错误分类

| 错误类型 | 处理策略 | 记录方式 |
|----------|----------|----------|
| **图片读取失败** | 跳过该图片，记录错误 | `status='failed'`, `error_message='File not found'` |
| **模型调用失败** | 跳过该图片，记录错误 | `status='failed'`, `error_message='API timeout'` |
| **标签解析失败** | 跳过该图片，记录错误 | `status='failed'`, `error_message='No tags found'` |
| **数据库写入失败** | 跳过该图片，记录错误 | 打印日志，不写入数据库 |

### 9.2 状态跟踪

```python
try:
    start_time = time.time()

    # 1. 预处理图片
    image_bytes, metadata = load_and_preprocess_image(...)

    # 2. 调用模型
    raw_output = model.generate_tags(image_bytes, prompt)

    # 3. 解析标签
    tags = parse_tags(raw_output, language)
    if not tags:
        raise ValueError("No tags extracted")

    # 4. 写入数据库
    processing_time = int((time.time() - start_time) * 1000)
    db.insert_tag(
        ...,
        status='success',
        processing_time=processing_time
    )
    return True

except Exception as e:
    # 记录失败
    db.insert_tag(
        ...,
        status='failed',
        error_message=str(e)
    )
    print(f"Error processing {image_path}: {e}")
    return False
```

### 9.3 进度展示

```python
from tqdm import tqdm

with tqdm(total=len(image_files), desc="处理进度", unit="张") as pbar:
    for image_path in image_files:
        process_image(...)
        pbar.update(1)
```

---

## 10. 扩展性设计

### 10.1 添加新模型后端

1. 在 `models.py` 中创建新类，继承 `BaseModel`
2. 实现 `generate_tags` 和 `generate_description` 方法
3. 在 `get_model` 工厂函数中添加新分支
4. 在 `config.py` 的 `--model-type` choices 中添加新类型

**示例：添加 Claude 支持**
```python
class ClaudeModel(BaseModel):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        self.api_key = api_key

    def generate_tags(self, image_bytes: bytes, prompt: str) -> str:
        # 调用 Anthropic Claude API
        ...
```

### 10.2 添加新语言

见 [第 7.3 节](#73-扩展新语言)

### 10.3 添加新索引方式

**示例：添加向量索引（图片相似度搜索）**

1. 在 `index_builder.py` 中添加 `VectorIndex` 类
2. 使用 CLIP / ResNet 提取图片特征向量
3. 存储到 SQLite BLOB 列或外部向量数据库（如 Faiss）
4. 提供 `search_similar(image_path, top_k=10)` 接口

### 10.4 数据库迁移

当前使用 SQLite，未来可迁移到：

- **PostgreSQL**: 支持更高并发、更复杂的查询
- **MySQL**: 适合分布式部署
- **MongoDB**: 适合非结构化数据（如 JSON tags）

**迁移步骤：**
1. 抽象 `database.py` 为接口类 `BaseDatabase`
2. 实现 `SQLiteDatabase`, `PostgreSQLDatabase` 等子类
3. 提供数据导出/导入脚本

---

## 11. 性能优化考虑

### 11.1 当前瓶颈

| 环节 | 耗时占比 | 优化方向 |
|------|----------|----------|
| **模型推理** | 80-90% | 使用更小的模型、量化、GPU 加速 |
| **图片 I/O** | 5-10% | 批量读取、内存缓存 |
| **数据库写入** | 3-5% | 批量插入、事务优化 |
| **网络请求** | 不定 | 本地部署、连接池 |

### 11.2 优化策略

**1. 并发处理**
```python
from multiprocessing import Pool

def worker(image_path):
    process_image(image_path, config, db)

with Pool(processes=4) as pool:
    pool.map(worker, image_files)
```

**2. 批量数据库操作**
```python
conn.execute("BEGIN TRANSACTION")
for record in records:
    conn.execute("INSERT INTO ...")
conn.execute("COMMIT")
```

**3. 模型优化**
- 使用量化模型（如 4-bit, 8-bit）
- 降低图片分辨率（256x256 vs 512x512）
- 选择更小的模型（2B vs 7B）

**4. 索引优化**
- 定期 `VACUUM` 清理 SQLite 碎片
- 定期 `ANALYZE` 更新查询统计信息
- 为常用查询创建覆盖索引

详细优化方案见 [doc/performance_optimization.md](performance_optimization.md)

---

## 12. 总结

### 12.1 核心设计亮点

1. **模块化架构**: 清晰的层次划分，易于维护和测试
2. **模型抽象**: 统一接口支持多种模型后端，降低迁移成本
3. **双层索引**: 倒排索引 + FTS5 全文搜索，兼顾精确性和灵活性
4. **增量处理**: 基于 SHA-256 去重，避免重复计算
5. **配置驱动**: CLI + YAML + Prompt 模板，高度可配置
6. **错误容忍**: 单张图片失败不影响整体流程，记录详细错误信息

### 12.2 未来演进方向

- **并发处理**: 支持多进程/异步 I/O，大幅提升吞吐量
- **增量索引**: 优化索引更新策略，避免全量重建
- **向量检索**: 添加图片相似度搜索（基于 CLIP embedding）
- **Web 界面**: 提供 Web UI 进行可视化检索和管理
- **分布式部署**: 支持多机协同处理大规模图片库

---

**文档版本**: v1.0
**最后更新**: 2024-02-04
