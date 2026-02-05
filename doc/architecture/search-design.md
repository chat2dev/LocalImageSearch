# 搜索功能设计文档

## 1. 概述

本文档详细描述了 LocalImageSearch 项目中搜索功能的设计方案。该搜索功能基于图像标签的向量表示和 FAISS 索引，提供高效的相似图像搜索、标签搜索和文本搜索功能。

## 2. 功能需求

### 2.1 核心搜索功能

1. **相似图像搜索**：根据查询图像的标签向量，搜索数据库中最相似的图像
2. **标签搜索**：根据用户输入的标签，直接匹配包含该标签的图像
3. **文本搜索**：将用户输入的文本查询转换为向量，搜索语义相似的图像
4. **高级搜索**：支持组合条件搜索（标签、文本、时间、状态等）

### 2.2 搜索结果展示

1. **结果排序**：按相似度分数排序，支持其他排序方式（时间、标签数量等）
2. **结果分页**：支持分页显示搜索结果
3. **结果预览**：显示图像缩略图、路径、标签、相似度分数等信息
4. **相似度可视化**：显示相似度分数或进度条

## 3. 系统架构

### 3.1 搜索流程

```
┌─────────────────────────────────────────────────────────┐
│ 用户界面层 (UI Layer)                                     │
│  - 搜索栏（文本输入、图像上传）                          │
│  - 结果展示（网格视图、列表视图）                        │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ API 服务层 (API Layer)                                   │
│  - /api/search/text      # 文本搜索                      │
│  - /api/search/tags      # 标签搜索                      │
│  - /api/search/similar   # 相似图像搜索                  │
│  - /api/search/advanced   # 高级搜索                     │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 搜索引擎层 (Search Engine Layer)                          │
│  - SearchEngine 类                                       │
│  - 负责查询解析、向量化、搜索、结果处理                    │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ 索引与存储层 (Index & Storage Layer)                      │
│  - FAISS 向量索引                                        │
│  - SQLite 图像标注数据库                                 │
└─────────────────────────────────────────────────────────┘
```

## 4. 搜索算法设计

### 4.1 文本搜索

```python
def search_by_text(query_text: str, k: int = 10) -> List[Dict]:
    """
    根据文本查询搜索图像
    1. 查询文本向量化
    2. 在 FAISS 索引中搜索相似向量
    3. 结果映射和排序
    4. 返回搜索结果
    """
    # 1. 向量化
    query_vector = vectorizer.vectorize(query_text)

    # 2. 搜索
    distances, indices = index.search(query_vector.reshape(1, -1), k)

    # 3. 结果处理
    results = []
    for i, idx in enumerate(indices[0]):
        image_info = metadata.get(idx)
        if image_info:
            results.append({
                "image_unique_id": image_info["image_unique_id"],
                "image_path": image_info["image_path"],
                "tags": image_info["tags"],
                "similarity": 1 - distances[0][i] / np.max(distances[0]),
                "generated_at": image_info["generated_at"]
            })

    return results
```

### 4.2 标签搜索

```python
def search_by_tags(tags: List[str], k: int = 10) -> List[Dict]:
    """
    根据标签搜索图像
    1. 解析标签列表
    2. 在 SQLite 中执行 SQL 查询
    3. 结果排序和分页
    """
    # 构建查询条件
    tag_conditions = " OR ".join([f"tags LIKE ?" for _ in tags])
    params = [f"%{tag}%" for tag in tags]

    # 查询
    query = """
        SELECT image_unique_id, image_path, tags, generated_at
        FROM image_tags
        WHERE status = 'success' AND ({})
        ORDER BY tag_count DESC
        LIMIT ?
    """.format(tag_conditions)

    params.append(k)
    results = db.execute_query(query, params)

    return [
        {
            "image_unique_id": row["image_unique_id"],
            "image_path": row["image_path"],
            "tags": row["tags"],
            "score": len(set(tags) & set(row["tags"].split(","))) / len(tags),
            "generated_at": row["generated_at"]
        }
        for row in results
    ]
```

### 4.3 相似图像搜索

```python
def search_by_image(image_unique_id: str, k: int = 10) -> List[Dict]:
    """
    根据图像搜索相似图像
    1. 获取目标图像的向量
    2. 在 FAISS 索引中搜索
    3. 结果过滤（排除自身）
    """
    # 获取图像向量
    image_vector = get_image_vector(image_unique_id)
    if image_vector is None:
        return []

    # 搜索
    distances, indices = index.search(image_vector.reshape(1, -1), k + 1)  # +1 排除自身

    # 过滤结果
    results = []
    for i, idx in enumerate(indices[0]):
        image_info = metadata.get(idx)
        if image_info and image_info["image_unique_id"] != image_unique_id:
            results.append({
                "image_unique_id": image_info["image_unique_id"],
                "image_path": image_info["image_path"],
                "tags": image_info["tags"],
                "similarity": 1 - distances[0][i] / np.max(distances[0]),
                "generated_at": image_info["generated_at"]
            })

    return results[:k]
```

### 4.4 高级搜索

```python
def search_advanced(query: Dict) -> List[Dict]:
    """
    高级搜索：组合条件搜索
    """
    conditions = []
    params = []

    # 标签条件
    if "tags" in query:
        tag_conditions = " OR ".join([f"tags LIKE ?" for _ in query["tags"]])
        conditions.append(f"({tag_conditions})")
        params.extend([f"%{tag}%" for tag in query["tags"]])

    # 文本条件
    if "text" in query:
        # 使用文本搜索的结果作为基础
        text_results = search_by_text(query["text"])
        if not text_results:
            return []

        # 获取相关图像的唯一 ID
        relevant_ids = [result["image_unique_id"] for result in text_results]
        id_conditions = " OR ".join([f"image_unique_id = ?" for _ in relevant_ids])
        conditions.append(f"({id_conditions})")
        params.extend(relevant_ids)

    # 时间条件
    if "start_time" in query:
        conditions.append("generated_at >= ?")
        params.append(query["start_time"])

    if "end_time" in query:
        conditions.append("generated_at <= ?")
        params.append(query["end_time"])

    # 状态条件
    if "status" in query:
        conditions.append("status = ?")
        params.append(query["status"])

    # 执行查询
    where_clause = " AND ".join(conditions)
    query_sql = """
        SELECT image_unique_id, image_path, tags, generated_at, status
        FROM image_tags
        WHERE {}
    """.format(where_clause)

    results = db.execute_query(query_sql, params)

    return [
        {
            "image_unique_id": row["image_unique_id"],
            "image_path": row["image_path"],
            "tags": row["tags"],
            "generated_at": row["generated_at"],
            "status": row["status"]
        }
        for row in results
    ]
```

## 5. API 接口设计

### 5.1 文本搜索接口

```http
POST /api/search/text HTTP/1.1
Content-Type: application/json

{
  "query": "风景,山脉",
  "k": 10
}

HTTP/1.1 200 OK
{
  "results": [
    {
      "image_unique_id": "1",
      "image_path": "/path/to/image1.jpg",
      "tags": "风景,山脉,天空",
      "similarity": 0.95,
      "generated_at": "2026-01-29T10:30:00"
    },
    {
      "image_unique_id": "2",
      "image_path": "/path/to/image2.jpg",
      "tags": "风景,海洋,沙滩",
      "similarity": 0.85,
      "generated_at": "2026-01-29T11:00:00"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 10
}
```

### 5.2 标签搜索接口

```http
GET /api/search/tags?tags=风景,山脉&k=10 HTTP/1.1

HTTP/1.1 200 OK
{
  "results": [
    {
      "image_unique_id": "1",
      "image_path": "/path/to/image1.jpg",
      "tags": "风景,山脉,天空",
      "score": 1.0,
      "generated_at": "2026-01-29T10:30:00"
    },
    {
      "image_unique_id": "3",
      "image_path": "/path/to/image3.jpg",
      "tags": "山脉,森林,河流",
      "score": 0.5,
      "generated_at": "2026-01-29T12:00:00"
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 10
}
```

### 5.3 相似图像搜索接口

```http
POST /api/search/similar HTTP/1.1
Content-Type: application/json

{
  "image_unique_id": "1",
  "k": 10
}

HTTP/1.1 200 OK
{
  "results": [
    {
      "image_unique_id": "2",
      "image_path": "/path/to/image2.jpg",
      "tags": "风景,海洋,沙滩",
      "similarity": 0.85,
      "generated_at": "2026-01-29T11:00:00"
    },
    {
      "image_unique_id": "4",
      "image_path": "/path/to/image4.jpg",
      "tags": "山脉,湖泊,森林",
      "similarity": 0.78,
      "generated_at": "2026-01-29T13:00:00"
    }
  ],
  "total": 30,
  "page": 1,
  "per_page": 10
}
```

### 5.4 高级搜索接口

```http
POST /api/search/advanced HTTP/1.1
Content-Type: application/json

{
  "tags": ["风景", "山脉"],
  "text": "自然风光",
  "start_time": "2026-01-01",
  "end_time": "2026-01-31",
  "status": "success",
  "k": 10
}

HTTP/1.1 200 OK
{
  "results": [
    {
      "image_unique_id": "1",
      "image_path": "/path/to/image1.jpg",
      "tags": "风景,山脉,天空",
      "generated_at": "2026-01-29T10:30:00",
      "status": "success"
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 10
}
```

## 6. 结果排序与分页

### 6.1 排序方式

```python
def sort_results(results: List[Dict], sort_by: str = "similarity", ascending: bool = False) -> List[Dict]:
    """
    结果排序
    """
    if sort_by == "similarity":
        return sorted(results, key=lambda x: x.get("similarity", 0), reverse=not ascending)
    elif sort_by == "generated_at":
        return sorted(results, key=lambda x: x.get("generated_at"), reverse=not ascending)
    elif sort_by == "tag_count":
        return sorted(results, key=lambda x: len(x.get("tags", "").split(",")), reverse=not ascending)
    elif sort_by == "score":
        return sorted(results, key=lambda x: x.get("score", 0), reverse=not ascending)
    else:
        return results
```

### 6.2 分页实现

```python
def paginate_results(results: List[Dict], page: int = 1, per_page: int = 20) -> Dict:
    """
    结果分页
    """
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "results": results[start:end],
        "total": len(results),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(results) + per_page - 1) // per_page
    }
```

## 7. 性能优化

### 7.1 查询优化

```python
def optimize_query(query: Dict) -> Dict:
    """
    查询优化
    """
    optimized = query.copy()

    # 文本查询优化
    if "text" in optimized:
        optimized["text"] = clean_text(optimized["text"])

    # 标签查询优化
    if "tags" in optimized:
        optimized["tags"] = [clean_text(tag) for tag in optimized["tags"]]

    # 时间范围优化
    if "start_time" in optimized and "end_time" in optimized:
        # 检查时间范围是否有效
        if optimized["start_time"] > optimized["end_time"]:
            optimized["start_time"], optimized["end_time"] = optimized["end_time"], optimized["start_time"]

    return optimized
```

### 7.2 缓存策略

```python
@lru_cache(maxsize=1000)
def cached_search_by_text(query: str, k: int) -> List[Dict]:
    """
    文本搜索结果缓存
    """
    return search_by_text(query, k)

@lru_cache(maxsize=1000)
def cached_search_by_tags(tags: Tuple[str, ...], k: int) -> List[Dict]:
    """
    标签搜索结果缓存
    """
    return search_by_tags(list(tags), k)
```

### 7.3 异步搜索

```python
import asyncio

async def async_search(query: Dict) -> List[Dict]:
    """
    异步搜索
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, search_advanced, query)

# 使用示例
results = await async_search({"text": "风景", "k": 5})
```

## 8. 错误处理

### 8.1 搜索错误

```python
class SearchError(Exception):
    """搜索相关错误"""
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code

def handle_search_error(error: Exception) -> Dict:
    """
    搜索错误处理
    """
    if isinstance(error, SearchError):
        return {
            "error": error.message,
            "code": error.code
        }
    elif isinstance(error, ValueError):
        return {
            "error": "无效的搜索参数",
            "code": 400
        }
    else:
        return {
            "error": "搜索过程中发生未知错误",
            "code": 500
        }
```

### 8.2 空结果处理

```python
def handle_no_results(query: Dict) -> List[Dict]:
    """
    空结果处理
    """
    suggestions = generate_suggestions(query)

    return {
        "results": [],
        "total": 0,
        "suggestions": suggestions,
        "message": "未找到匹配的图像，以下是一些建议："
    }

def generate_suggestions(query: Dict) -> List[str]:
    """
    生成搜索建议
    """
    suggestions = []

    if "text" in query:
        suggestions.append("尝试使用更简单的关键词")
        suggestions.append("检查拼写是否正确")

    if "tags" in query:
        suggestions.append("尝试减少标签数量")
        suggestions.append("使用更通用的标签")

    return suggestions
```

## 9. 代码实现

### 9.1 目录结构

```
app/
├── api/
│   └── search.py      # 搜索 API 接口
├── services/
│   └── search_engine.py  # 搜索引擎核心逻辑
├── utils/
│   └── search_utils.py  # 搜索工具函数
└── models/
    └── search.py      # 搜索请求/响应模型
```

### 9.2 核心类设计

```python
class SearchEngine:
    """搜索引擎核心类"""

    def __init__(self, index: faiss.Index, metadata: Dict):
        self.index = index
        self.metadata = metadata
        self.vectorizer = SentenceBERTVectorizer()

    def search_by_text(self, query_text: str, k: int = 10) -> List[Dict]:
        pass

    def search_by_tags(self, tags: List[str], k: int = 10) -> List[Dict]:
        pass

    def search_by_image(self, image_unique_id: str, k: int = 10) -> List[Dict]:
        pass

    def search_advanced(self, query: Dict) -> List[Dict]:
        pass
```

## 10. 测试计划

### 10.1 单元测试

```python
def test_search_by_text_basic():
    """测试基本文本搜索功能"""
    engine = SearchEngine(index, metadata)
    results = engine.search_by_text("风景", 5)
    assert len(results) <= 5

def test_search_by_tags_basic():
    """测试基本标签搜索功能"""
    engine = SearchEngine(index, metadata)
    results = engine.search_by_tags(["风景"], 5)
    for result in results:
        assert "风景" in result["tags"]

def test_similarity_score():
    """测试相似度分数范围"""
    engine = SearchEngine(index, metadata)
    results = engine.search_by_text("风景", 5)
    for result in results:
        assert 0.0 <= result["similarity"] <= 1.0
```

### 10.2 集成测试

```python
def test_search_api():
    """测试搜索 API 接口"""
    with TestClient(app) as client:
        response = client.post("/api/search/text", json={"query": "风景", "k": 5})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
```

### 10.3 性能测试

```python
def test_search_performance():
    """测试搜索性能"""
    engine = SearchEngine(index, metadata)

    start_time = time.time()
    engine.search_by_text("风景", 10)
    search_time = time.time() - start_time

    assert search_time < 0.1  # 搜索时间应小于 100ms
```

## 11. 部署方案

### 11.1 服务器配置

```yaml
# 建议的服务器配置
server:
  workers: 4
  timeout: 30
  log_level: info

# 搜索配置
search:
  default_k: 10
  max_k: 100
  similarity_threshold: 0.5
  cache_size: 1000
```

### 11.2 监控指标

```python
def track_search_metrics(query: str, results_count: int, search_time: float):
    """
    跟踪搜索指标
    """
    metrics = {
        "query": query,
        "results_count": results_count,
        "search_time": search_time,
        "timestamp": time.time()
    }

    # 发送到监控系统（如 Prometheus）
    prometheus_client.Gauge("search_time").set(search_time)
    prometheus_client.Counter("search_count").inc()
```

---

**文档版本**：1.0
**创建时间**：2026-01-29
**适用版本**：LocalImageSearch v1.0
