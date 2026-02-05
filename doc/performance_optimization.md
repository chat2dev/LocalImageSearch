# 性能优化指南

## 问题分析

当前系统处理速度较慢的主要原因：
1. **单线程处理**: 图片逐个处理，无法并发
2. **模型推理开销**: 视觉-语言模型推理耗时长（每张20-30秒）
3. **网络请求**: Ollama API调用存在网络延迟
4. **图片I/O**: 大图片的读取和预处理耗时

## 优化策略

### 1. 并发处理（最有效）⭐⭐⭐⭐⭐

#### 方案A: 多进程处理

**优点**:
- 充分利用多核CPU
- 绕过Python GIL限制
- 实现简单

**实现**:
```python
from multiprocessing import Pool, cpu_count

def process_batch(image_paths, workers=4):
    with Pool(processes=workers) as pool:
        results = pool.map(process_single_image, image_paths)
    return results
```

**预期提升**: 4核CPU可提升3-4倍速度

**使用**:
```bash
python src/main.py --image-path /path --workers 4
```

#### 方案B: 异步I/O + 队列

**优点**:
- 适合I/O密集型操作
- 更好的资源控制
- 可限制并发数

**实现**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_concurrent(image_paths, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)
    async def process_with_semaphore(path):
        async with semaphore:
            return await process_image_async(path)

    tasks = [process_with_semaphore(p) for p in image_paths]
    return await asyncio.gather(*tasks)
```

**预期提升**: 2-5倍速度（取决于网络延迟）

### 2. 批处理优化 ⭐⭐⭐⭐

#### 批量API调用

某些模型API支持批量处理：

```python
def process_batch_images(image_list, batch_size=4):
    # 一次API调用处理多张图片
    responses = model.generate_batch(image_list)
    return responses
```

**预期提升**: 1.5-2倍速度

### 3. 模型优化 ⭐⭐⭐⭐⭐

#### 3.1 使用更快的模型

| 模型 | 单张耗时 | 质量 | 建议场景 |
|-----|---------|------|---------|
| InternVL2-2B | ~1-2s | 中 | 快速处理 |
| LLaVA-3B | ~2-3s | 中 | 平衡 |
| Qwen3-VL-4B | ~3-5s | 高 | 推荐 |
| Qwen3-VL-8B | ~8-10s | 很高 | 高质量 |

**使用**:
```bash
# 使用更快的模型
python src/main.py --image-path /path --model llava-v1.6:3b
```

#### 3.2 模型量化

使用量化模型可以显著提升速度：

```bash
# Q4量化（推荐）
ollama pull qwen3-vl:4b-q4

# Q2量化（极致速度）
ollama pull qwen3-vl:4b-q2
```

**预期提升**: 20-40%速度提升，轻微精度损失

#### 3.3 GPU加速

确保模型运行在GPU上：

```bash
# 检查GPU是用
nvidia-smi

# 确保CUDA可用
python -c "import torch; print(torch.cuda.is_available())"
```

**预期提升**: 5-10倍速度（相比CPU）

### 4. 图片预处理优化 ⭐⭐⭐

#### 4.1 减小图片尺寸

```bash
# 使用更小的尺寸
python src/main.py --image-path /path --resize 256x256
```

| 尺寸 | 处理时间 | 质量影响 |
|------|---------|---------|
| 256x256 | 100% | 轻微降低 |
| 512x512 | 150% | 基准 |
| 768x768 | 220% | 略有提升 |
| 1024x1024 | 300% | 明显提升 |

#### 4.2 图片缓存

缓存预处理后的图片：

```python
@lru_cache(maxsize=100)
def load_and_cache_image(image_path):
    return load_and_preprocess_image(image_path)
```

### 5. 数据库优化 ⭐⭐

#### 5.1 批量插入

```python
def batch_insert(db, records, batch_size=100):
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        db.insert_batch(batch)
        db.commit()
```

**预期提升**: 10-20%（大批量时）

#### 5.2 关闭同步写入

```python
# 在处理开始时
db.execute("PRAGMA synchronous = OFF")
db.execute("PRAGMA journal_mode = MEMORY")

# 处理完成后恢复
db.execute("PRAGMA synchronous = FULL")
```

**注意**: 仅在确保不会中断时使用

### 6. 网络优化 ⭐⭐⭐

#### 6.1 本地部署

使用本地模型替代API调用：

```bash
# 方案1: 直接使用Transformers
python src/main.py --model-type local --model-path /path/to/model

# 方案2: 使用vLLM本地API
vllm serve qwen3-vl:4b --port 8000
python src/main.py --model-type openai --api-base http://localhost:8000
```

**预期提升**: 消除网络延迟，提升30-50%

#### 6.2 连接池

复用HTTP连接：

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.1)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount('http://', adapter)
```

### 7. 跳过已处理图片 ⭐⭐⭐⭐

系统已实现增量处理，但可以优化：

```python
# 批量检查，而不是逐个检查
def get_unprocessed_images(image_paths, db):
    existing_ids = set(db.get_all_image_ids())
    return [p for p in image_paths
            if generate_unique_id(p) not in existing_ids]
```

## 综合优化方案

### 方案1: 快速处理（适合大批量）

```bash
python src/main.py \
  --image-path /path/to/images \
  --model llava-v1.6:3b \
  --resize 256x256 \
  --workers 8 \
  --no-description \
  --tag-count 10
```

**特点**:
- 使用轻量模型
- 小图片尺寸
- 8进程并发
- 不生成描述
- 预期速度: ~1秒/张

### 方案2: 平衡方案（推荐）

```bash
python src/main.py \
  --image-path /path/to/images \
  --model qwen3-vl:4b \
  --resize 512x512 \
  --workers 4 \
  --description \
  --tag-count 20
```

**特点**:
- 中等模型
- 标准尺寸
- 4进程并发
- 生成描述
- 预期速度: ~3-5秒/张

### 方案3: 高质量（适合小批量）

```bash
python src/main.py \
  --image-path /path/to/images \
  --model qwen3-vl:8b \
  --resize 768x768 \
  --workers 2 \
  --description \
  --tag-count 30
```

**特点**:
- 大模型
- 高分辨率
- 少量并发（避免显存不足）
- 详细标注
- 预期速度: ~10-15秒/张

## 实施步骤

### 第一阶段: 基础优化（立即可用）

1. ✅ 使用更快的模型
   ```bash
   ollama pull llava-v1.6:3b
   ```

2. ✅ 减小图片尺寸
   ```bash
   --resize 256x256
   ```

3. ✅ 跳过不必要的功能
   ```bash
   --no-description  # 如果不需要描述
   --tag-count 10    # 减少标签数量
   ```

### 第二阶段: 并发优化（需要代码修改）

实现多进程处理：

```python
# src/concurrent_processing.py
from multiprocessing import Pool
import os

def process_image_worker(args):
    image_path, config = args
    # 每个worker独立处理
    return process_image(image_path, config)

def process_images_concurrent(image_paths, config, workers=None):
    if workers is None:
        workers = os.cpu_count()

    args_list = [(path, config) for path in image_paths]

    with Pool(processes=workers) as pool:
        results = pool.map(process_image_worker, args_list)

    return results
```

### 第三阶段: 高级优化（可选）

1. 部署本地高性能API (vLLM)
2. 实现智能批处理
3. 使用GPU集群

## 性能监控

### 添加性能日志

```python
import time

def process_with_timing(image_path):
    start = time.time()

    # 记录各阶段耗时
    load_start = time.time()
    image = load_image(image_path)
    load_time = time.time() - load_start

    infer_start = time.time()
    tags = model.generate_tags(image)
    infer_time = time.time() - infer_start

    db_start = time.time()
    db.insert(tags)
    db_time = time.time() - db_start

    total_time = time.time() - start

    print(f"Timing - Load: {load_time:.2f}s, "
          f"Infer: {infer_time:.2f}s, "
          f"DB: {db_time:.2f}s, "
          f"Total: {total_time:.2f}s")
```

### 性能基准测试

```bash
# 测试10张图片的处理时间
python src/benchmark.py \
  --image-path /path/to/test/images \
  --count 10 \
  --model qwen3-vl:4b
```

## 预期效果

| 优化方案 | 原始速度 | 优化后速度 | 提升倍数 |
|---------|---------|-----------|---------|
| 仅换模型 | 28s/张 | 3s/张 | 9.3x |
| +减小尺寸 | 28s/张 | 2s/张 | 14x |
| +4进程并发 | 28s/张 | 0.5s/张 | 56x |
| +8进程并发 | 28s/张 | 0.3s/张 | 93x |

## 常见问题

### Q: 并发处理时显存不足怎么办？
A: 减少worker数量或使用更小的模型

### Q: 多进程会导致数据库冲突吗？
A: 建议每个进程使用独立的数据库连接，或使用队列统一写入

### Q: GPU利用率低怎么办？
A: 使用批处理或增加并发数

### Q: 如何在CPU上优化？
A: 使用量化模型+多进程并发

## 最佳实践

1. **开发阶段**: 使用小模型+小图片快速迭代
2. **生产阶段**: 根据资源选择合适的并发数
3. **监控**: 记录处理时间，持续优化瓶颈
4. **平衡**: 在速度和质量之间找到最佳点

## 总结

通过综合优化，可以将处理速度从28秒/张提升到0.3-0.5秒/张，提升约56-93倍。

**推荐优化顺序**:
1. 更换更快的模型 → 立即见效
2. 减小图片尺寸 → 简单有效
3. 实现多进程并发 → 效果最好
4. 优化数据库操作 → 锦上添花
5. 本地部署高性能API → 专业方案

选择合适的优化方案，在您的硬件条件下找到速度和质量的最佳平衡点。
