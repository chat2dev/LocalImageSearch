# FAISS 索引设计文档

## 1. 概述

本文档详细描述了 LocalImageSearch 项目中使用 FAISS（Facebook AI Similarity Search）进行图像标签向量索引和搜索的设计方案。该方案基于现有的 `image_tags` 表（存储图片标注结果），实现高效的相似图像搜索功能。

## 2. 需求分析

### 2.1 数据来源

图像标注数据存储在 SQLite 数据库的 `image_tags` 表中，该表包含以下关键字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| image_unique_id | TEXT | 图片唯一标识符（SHA-256 哈希） |
| image_path | TEXT | 图片文件路径 |
| tags | TEXT | 标注标签（逗号分隔字符串） |
| description | TEXT | 图片描述（可选） |
| model_name | TEXT | 使用的模型名称 |
| status | TEXT | 标注状态（成功/失败/处理中） |

### 2.2 核心需求

1. **向量表示**：将图像标签转换为高维向量
2. **索引构建**：创建高效的向量索引
3. **相似搜索**：根据查询向量找到最相似的图像
4. **增量更新**：支持向现有索引添加新数据
5. **查询优化**：提供快速、准确的搜索结果

## 3. 技术选型

### 3.1 向量化方案

**Sentence-BERT (SBERT)**：

- 使用预训练的 Sentence-BERT 模型
- 能够将文本转换为语义丰富的向量表示
- 对短句和长文本都有良好的表现
- 预训练模型：`all-MiniLM-L6-v2`（768 维向量）

### 3.2 索引方案

**FAISS (Facebook AI Similarity Search)**：

- 高性能相似性搜索库
- 支持多种索引类型
- 内存高效的向量存储
- GPU 加速支持

### 3.3 索引类型选择

| 索引类型 | 特点 | 适用场景 |
|---------|------|----------|
| IVFPQ | 倒排索引 + 乘积量化 | 中等规模数据（10万级） |
| Flat | 精确搜索，无压缩 | 小规模数据（1万级） |
| IVFFlat | 倒排索引 + 平坦量化 | 平衡速度和准确性 |
| HNSW | 图索引 | 超大规模数据（百万级） |

**选择 IVFPQ 作为默认索引类型**，平衡搜索速度和内存使用。

## 4. 系统架构

### 4.1 索引流程

```
┌──────────────────────────────────────────────────────┐
│ 1. 数据读取 (Data Loading)                           │
│    - 从 image_tags 表读取成功标注的记录             │
│    - 过滤无效数据和失败记录                         │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ 2. 数据预处理 (Data Preprocessing)                   │
│    - 解析标签字符串（逗号分隔）                      │
│    - 文本清洗和标准化                               │
│    - 处理多标签合并策略                             │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ 3. 文本向量化 (Text Vectorization)                   │
│    - 使用 Sentence-BERT 模型                         │
│    - 标签文本 → 768 维向量                           │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ 4. 索引构建 (Index Construction)                     │
│    - 初始化 FAISS 索引                              │
│    - 添加向量到索引                                  │
│    - 训练索引（IVFPQ 需要）                          │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ 5. 索引存储 (Index Storage)                          │
│    - 保存索引到文件                                 │
│    - 保存索引配置信息                               │
└──────────────────────────────────────────────────────┘
```

### 4.2 搜索流程

```
┌──────────────────────────────────────────────────────┐
│ 1. 查询预处理 (Query Preprocessing)                  │
│    - 查询文本清洗和标准化                           │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ 2. 查询向量化 (Query Vectorization)                  │
│    - 使用 Sentence-BERT 模型                         │
│    - 查询文本 → 768 维向量                           │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ 3. 相似搜索 (Similarity Search)                      │
│    - 在 FAISS 索引中搜索                             │
│    - 返回最相似的向量及其 ID                        │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ 4. 结果映射 (Result Mapping)                         │
│    - 向量 ID → 图像信息                              │
│    - 排序和过滤结果                                 │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ 5. 结果返回 (Result Return)                          │
│    - 返回图像路径、标签、相似度分数等                │
└──────────────────────────────────────────────────────┘
```

## 5. 索引配置

### 5.1 索引参数

```json
{
  "index_type": "IVFPQ",
  "dimension": 768,
  "nlist": 100,
  "m": 8,
  "nbits_per_idx": 8,
  "metric": "L2"
}
```

| 参数 | 说明 |
|------|------|
| index_type | 索引类型（IVFPQ） |
| dimension | 向量维度（768） |
| nlist | 倒排索引的列表数量（100） |
| m | 乘积量化的子向量数量（8） |
| nbits_per_idx | 每个子向量的编码位数（8） |
| metric | 距离度量（L2 欧氏距离） |

### 5.2 搜索参数

```python
search_params = {
    "nprobe": 5,
    "k": 10
}
```

| 参数 | 说明 |
|------|------|
| nprobe | 搜索时访问的倒排列表数量（影响搜索速度和准确性） |
| k | 返回的最相似结果数量 |

## 6. 索引管理

### 6.1 存储结构

```
data/faiss/
├── indexes/                  # 索引文件存储
│   ├── image_tags_index_20260129_1030.index  # 带时间戳的索引文件
│   └── image_tags_index_latest.index        # 最新索引的软链接
└── config/                   # 索引配置
    ├── index_config.json     # 索引参数配置
    └── metadata.json         # 索引元数据（包含向量到图像的映射）
```

### 6.2 索引更新

**全量更新**：
```
1. 从数据库读取所有有效记录
2. 重新计算所有向量
3. 重建索引
4. 保存新索引并更新软链接
```

**增量更新**：
```
1. 读取最近更新的记录
2. 计算新向量
3. 添加到现有索引
4. 保存更新后的索引
```

### 6.3 索引优化

- **定期重建**：根据数据增长情况定期全量重建索引
- **压缩优化**：使用 FAISS 的压缩功能减少索引体积
- **内存管理**：合理配置索引的内存使用

## 7. 性能分析

### 7.1 构建时间

| 数据规模 | 索引类型 | 构建时间 |
|---------|---------|----------|
| 10,000 | IVFPQ | ~30 秒 |
| 50,000 | IVFPQ | ~2 分钟 |
| 100,000 | IVFPQ | ~5 分钟 |

### 7.2 搜索性能

| 数据规模 | 索引类型 | 查询时间 | 准确率 |
|---------|---------|----------|--------|
| 10,000 | IVFPQ | ~10ms | 95% |
| 50,000 | IVFPQ | ~20ms | 92% |
| 100,000 | IVFPQ | ~30ms | 90% |

### 7.3 存储需求

| 数据规模 | 索引类型 | 索引大小 |
|---------|---------|----------|
| 10,000 | IVFPQ | ~10 MB |
| 50,000 | IVFPQ | ~50 MB |
| 100,000 | IVFPQ | ~100 MB |

## 8. 错误处理

### 8.1 数据验证

```python
def validate_image_tags(record):
    """验证 image_tags 表记录是否有效"""
    if record['status'] != 'success':
        return False
    if not record['tags']:
        return False
    if record['tag_count'] <= 0:
        return False
    return True
```

### 8.2 索引修复

```python
def check_index_validity(index_path):
    """检查索引文件的有效性"""
    try:
        index = faiss.read_index(index_path)
        if index.ntotal == 0:
            return False
        return True
    except Exception as e:
        logging.error(f"Index validation failed: {e}")
        return False
```

### 8.3 重试机制

```python
@retry(exceptions=(Exception,), tries=3, delay=1)
def build_index(vectors, config):
    """构建索引的重试机制"""
    index = create_index(config)
    index.add(vectors)
    return index
```

## 9. 代码实现

### 9.1 目录结构

```
app/
├── services/
│   ├── data_loader.py      # 数据读取服务
│   ├── text_vectorizer.py  # 文本向量化服务
│   ├── faiss_indexer.py    # FAISS 索引服务
│   └── search_engine.py    # 搜索引擎服务
└── utils/
    └── file_utils.py       # 文件处理工具
```

### 9.2 主要接口

```python
# 数据加载接口
def load_image_tags() -> List[Dict]:
    """从 image_tags 表加载数据"""

# 向量化接口
def vectorize_text(text: str) -> np.ndarray:
    """将文本转换为向量"""

# 索引接口
def build_faiss_index(vectors: np.ndarray, config: Dict) -> faiss.Index:
    """构建 FAISS 索引"""

def search_index(index: faiss.Index, query_vector: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
    """在索引中搜索"""

# 搜索接口
def search_similar_images(query_text: str, k: int = 10) -> List[Dict]:
    """搜索相似图像"""
```

## 10. 测试计划

### 10.1 单元测试

```python
def test_vectorize_text():
    """测试文本向量化"""
    vector = vectorize_text("风景,山脉,天空")
    assert len(vector) == 768

def test_search_index():
    """测试索引搜索功能"""
    query_vector = vectorize_text("风景")
    distances, indices = search_index(index, query_vector, 5)
    assert len(distances) == 5

def test_similarity_order():
    """测试相似度排序"""
    results = search_similar_images("风景,山脉", 3)
    assert results[0]['similarity'] > results[1]['similarity']
```

### 10.2 集成测试

```python
def test_end_to_end_search():
    """测试端到端搜索流程"""
    # 准备测试数据
    test_image_tags = [
        {"image_unique_id": "1", "image_path": "/test1.jpg", "tags": "风景,山脉"},
        {"image_unique_id": "2", "image_path": "/test2.jpg", "tags": "风景,天空"},
        {"image_unique_id": "3", "image_path": "/test3.jpg", "tags": "动物,狗"}
    ]

    # 构建索引
    index = build_index_from_tags(test_image_tags)

    # 搜索
    results = search_similar_images("风景", 2)

    # 验证结果
    assert len(results) == 2
    assert results[0]['image_unique_id'] in ["1", "2"]
```

## 11. 部署方案

### 11.1 环境要求

```bash
# 核心依赖
pip install faiss-cpu>=1.7.4
pip install sentence-transformers>=2.2.2
pip install numpy>=1.24.3
pip install pandas>=2.0.1
```

### 11.2 启动脚本

```bash
#!/bin/bash
# 构建索引脚本
python -m app.services.faiss_indexer --action build --config config/index_config.json

# 搜索测试脚本
python -m app.services.search_engine --query "风景" --k 5
```

## 12. 扩展计划

### 12.1 多模型支持

```python
class VectorizerFactory:
    """向量化模型工厂"""
    @staticmethod
    def get_vectorizer(model_name: str):
        if model_name == "sbert":
            return SentenceBERTVectorizer()
        elif model_name == "word2vec":
            return Word2VecVectorizer()
        elif model_name == "fasttext":
            return FastTextVectorizer()
        else:
            raise ValueError(f"Unsupported model: {model_name}")
```

### 12.2 GPU 加速

```python
def build_faiss_index_gpu(vectors: np.ndarray, config: Dict) -> faiss.Index:
    """GPU 加速索引构建"""
    ngpus = faiss.get_num_gpus()
    if ngpus == 0:
        return build_faiss_index(vectors, config)

    # 使用 GPU 构建索引
    res = faiss.StandardGpuResources()
    index = build_faiss_index(vectors, config)
    index = faiss.index_cpu_to_gpu(res, 0, index)
    return index
```

### 12.3 分块索引

```python
def build_block_indexes(vectors: np.ndarray, block_size: int = 10000):
    """分块构建索引"""
    blocks = np.array_split(vectors, len(vectors) // block_size)
    for i, block in enumerate(blocks):
        index = build_faiss_index(block, config)
        faiss.write_index(index, f"block_{i}.index")
```

---

**文档版本**：1.0
**创建时间**：2026-01-29
**适用版本**：LocalImageSearch v1.0
