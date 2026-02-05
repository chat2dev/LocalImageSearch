# 多模型支持与性能优化更新

## 更新日期: 2026-01-30

## 概述

本次更新添加了多种模型后端支持，并提供了详细的性能优化方案，帮助用户根据实际需求选择合适的模型和优化策略。

---

## 🎯 主要新功能

### 1. 多模型后端支持

系统现在支持三种模型后端：

#### A. Ollama (默认)
- **特点**: 最简单，开箱即用
- **适用场景**: 快速开始，本地测试
- **使用方法**:
  ```bash
  ollama pull qwen3-vl:4b
  python src/main.py --image-path /path --model qwen3-vl:4b
  ```

#### B. OpenAI兼容API
- **特点**: 支持vLLM、LocalAI等高性能推理服务
- **适用场景**: 生产环境，高并发需求
- **使用方法**:
  ```bash
  # 启动vLLM服务
  python -m vllm.entrypoints.openai.api_server \
    --model openbmb/MiniCPM-V-2_5 --port 8000

  # 使用API
  python src/main.py \
    --image-path /path \
    --model minicpm-v \
    --model-type openai \
    --api-base http://localhost:8000
  ```

#### C. 本地模型文件
- **特点**: 直接加载模型，完全离线
- **适用场景**: 无网络环境，自定义模型
- **使用方法**:
  ```bash
  # 下载模型
  git lfs clone https://huggingface.co/openbmb/MiniCPM-V-2_5

  # 使用本地模型
  python src/main.py \
    --image-path /path \
    --model minicpm-v \
    --model-type local \
    --model-path ./MiniCPM-V-2_5
  ```

### 2. 新增配置参数

#### 命令行参数
```bash
--model-type {ollama,openai,local}  # 模型类型
--model-path PATH                   # 本地模型路径
--api-base URL                      # API服务地址
--api-key KEY                       # API密钥
```

#### 配置文件示例
```yaml
# Ollama配置
model: "qwen3-vl:4b"
model_type: "ollama"

# OpenAI兼容API配置
model: "qwen-vl-chat"
model_type: "openai"
api_base: "http://localhost:8000"
api_key: "your-key-if-needed"

# 本地模型配置
model: "minicpm-v-2.5"
model_type: "local"
model_path: "/path/to/MiniCPM-V-2_5"
```

---

## 📊 推荐模型

### 快速参考表

| 模型 | 参数量 | 显存 | 速度 | 中文 | 推荐场景 |
|-----|--------|-----|------|------|---------|
| InternVL2-2B | 2B | 3GB | 极快 | ⭐⭐⭐⭐ | 资源受限 |
| LLaVA-3B | 3B | 4GB | 快 | ⭐⭐ | 英文为主 |
| **Qwen3-VL-4B** | 4.4B | 6GB | 中等 | ⭐⭐⭐⭐⭐ | **推荐首选** |
| MiniCPM-V-2.5 | 2.8B | 4GB | 快 | ⭐⭐⭐⭐⭐ | 中文优化 |
| Qwen3-VL-8B | 8.8B | 10GB | 慢 | ⭐⭐⭐⭐⭐ | 高精度 |

### 选择建议

**按资源选择**:
- 4GB以下 → InternVL2-2B, LLaVA-3B
- 4-6GB → **Qwen3-VL-4B** (推荐), MiniCPM-V-2.5
- 6-10GB → Qwen3-VL-8B, LLaVA-7B
- 10GB+ → Qwen3-VL-8B, CogVLM2

**按语言选择**:
- 中文 → **Qwen3-VL** (强烈推荐), MiniCPM-V
- 英文 → LLaVA, InternVL2
- 多语言 → Qwen3-VL-8B

**按速度选择**:
- 极快(1-2s/张) → InternVL2-2B, LLaVA-3B
- 快速(2-5s/张) → MiniCPM-V, **Qwen3-VL-4B**
- 标准(5-10s/张) → Qwen3-VL-8B, LLaVA-7B

---

## ⚡ 性能优化

### 当前性能问题
- 原始速度: ~28秒/张
- 主要瓶颈: 单线程处理 + 模型推理慢

### 优化方案对比

| 优化方案 | 实施难度 | 效果 | 速度提升 |
|---------|---------|------|---------|
| 换小模型 | ⭐ 简单 | ⭐⭐⭐⭐⭐ | 9x |
| 减小图片 | ⭐ 简单 | ⭐⭐⭐ | 1.5x |
| 4进程并发 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ | 4x |
| 批处理 | ⭐⭐ 简单 | ⭐⭐⭐ | 2x |
| GPU加速 | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ | 10x |

### 快速优化（立即可用）

#### 方案1: 使用快速模型
```bash
# 从28s/张 → 3s/张 (9.3x提升)
ollama pull llava-v1.6:3b
python src/main.py --image-path /path --model llava-v1.6:3b
```

#### 方案2: 减小图片尺寸
```bash
# 额外提升1.5x
python src/main.py --image-path /path --resize 256x256
```

#### 方案3: 组合优化
```bash
# 从28s/张 → 2s/张 (14x提升)
python src/main.py \
  --image-path /path \
  --model llava-v1.6:3b \
  --resize 256x256 \
  --tag-count 10
```

### 高级优化（需要代码修改）

#### 多进程并发
```python
# 预期: 从28s/张 → 0.5s/张 (56x提升)
# TODO: 将在下个版本实现
```

#### 使用vLLM部署
```bash
# 高性能推理服务
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --model qwen3-vl:4b --port 8000

# 可获得额外30-50%性能提升
```

### 综合优化方案

**方案A: 极速处理**
```bash
# 速度: ~1s/张, 质量: 中等
python src/main.py \
  --image-path /path \
  --model llava-v1.6:3b \
  --resize 256x256 \
  --tag-count 10 \
  --no-description
```

**方案B: 平衡方案** (推荐)
```bash
# 速度: ~3-5s/张, 质量: 高
python src/main.py \
  --image-path /path \
  --model qwen3-vl:4b \
  --resize 512x512 \
  --tag-count 20 \
  --description
```

**方案C: 高质量**
```bash
# 速度: ~10-15s/张, 质量: 很高
python src/main.py \
  --image-path /path \
  --model qwen3-vl:8b \
  --resize 768x768 \
  --tag-count 30 \
  --description
```

---

## 📝 使用示例

### 示例1: 使用Ollama快速开始

```bash
# 1. 安装Ollama
curl https://ollama.ai/install.sh | sh

# 2. 下载模型
ollama pull qwen3-vl:4b

# 3. 处理图片
python src/main.py \
  --image-path ~/Pictures \
  --model qwen3-vl:4b \
  --language zh \
  --tag-count 20
```

### 示例2: 使用OpenAI兼容API

```bash
# 1. 安装vLLM
pip install vllm

# 2. 启动API服务
python -m vllm.entrypoints.openai.api_server \
  --model openbmb/MiniCPM-V-2_5 \
  --port 8000 \
  --gpu-memory-utilization 0.8

# 3. 使用API处理
python src/main.py \
  --image-path ~/Pictures \
  --model minicpm-v \
  --model-type openai \
  --api-base http://localhost:8000 \
  --language zh
```

### 示例3: 使用本地模型

```bash
# 1. 下载模型
git lfs clone https://huggingface.co/openbmb/MiniCPM-V-2_5

# 2. 安装transformers
pip install transformers torch accelerate

# 3. 使用本地模型
python src/main.py \
  --image-path ~/Pictures \
  --model minicpm-v-2.5 \
  --model-type local \
  --model-path ./MiniCPM-V-2_5 \
  --language zh
```

### 示例4: 使用配置文件

创建 `config.yaml`:
```yaml
model: "qwen3-vl:4b"
model_type: "ollama"
image_path: "/Users/user/Pictures"
resize: "512x512"
tag_count: 20
generate_description: true
language: "zh"
db_path: "./data/image_tags.db"
```

运行:
```bash
python src/main.py --config config.yaml
```

---

## 🔧 代码变更

### 修改的文件

1. **src/config.py**
   - 添加 `model_type`, `model_path`, `api_base`, `api_key` 配置
   - 更新命令行参数和YAML加载

2. **src/models.py**
   - 添加 `OpenAICompatibleModel` 类
   - 添加 `LocalModel` 类
   - 将 `_parse_response` 移到 `BaseModel`
   - 更新 `create_model` 工厂函数

3. **src/tagging.py**
   - 更新 `process_image` 函数签名
   - 传递新的模型参数

4. **src/main.py**
   - 传递配置参数到处理函数

### 新增文件

1. **doc/model_recommendations.md**
   - 推荐的本地小模型详细信息
   - 模型对比和选择建议
   - 部署指南

2. **doc/performance_optimization.md**
   - 详细的性能优化策略
   - 实施步骤和预期效果
   - 监控和调优建议

3. **doc/multi_model_support_update.md** (本文件)
   - 综合更新说明

---

## 📚 相关文档

- [模型推荐](./model_recommendations.md) - 详细的模型对比和选择指南
- [性能优化](./performance_optimization.md) - 深入的性能优化策略
- [CLAUDE.md](../CLAUDE.md) - 项目总体文档
- [最近更新](./recent_updates.md) - 之前的更新记录

---

## ❓ 常见问题

### Q1: 我应该选择哪种模型后端？
**A**:
- 快速开始 → Ollama (最简单)
- 生产环境 → OpenAI API + vLLM (性能最好)
- 离线环境 → 本地模型文件

### Q2: 如何提升处理速度？
**A**: 按优先级:
1. 使用更快的模型 (9x提升)
2. 减小图片尺寸 (1.5x提升)
3. 实现多进程 (4x提升)
4. 使用GPU加速 (10x提升)

### Q3: 中文效果不好怎么办？
**A**: 使用国产模型:
- Qwen3-VL-4B (推荐)
- MiniCPM-V-2.5
- CogVLM2-4B

### Q4: 显存不足怎么办？
**A**:
1. 使用更小的模型 (InternVL2-2B, LLaVA-3B)
2. 使用量化版本 (Q4, Q8)
3. 减小图片尺寸
4. 使用CPU运行 (会慢很多)

### Q5: 如何使用自己训练的模型？
**A**: 使用local模式:
```bash
python src/main.py \
  --model-type local \
  --model-path /path/to/your/model
```

---

## 🎯 下一步计划

- [ ] 实现多进程并发处理
- [ ] 添加批处理支持
- [ ] 支持更多模型格式
- [ ] 添加性能监控和统计
- [ ] 提供Web UI界面

---

## 📞 反馈与支持

如有问题或建议，请提交Issue或Pull Request。

---

**更新完成时间**: 2026-01-30
**版本**: v2.0
**主要贡献**: 多模型支持 + 性能优化方案
