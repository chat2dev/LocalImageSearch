# 模型性能基准测试指南

## 概述

本指南介绍如何使用 `benchmark_models.py` 脚本来比较不同模型后端的性能，包括：
- **Ollama**: 本地部署，简单易用
- **本地模型**: 使用Transformers直接加载模型文件
- **在线API**: OpenAI兼容API，如豆包(Doubao)、通义千问等

测试重点关注两个核心指标：
1. **自动标注准确率**: 标签质量和相关性
2. **处理耗时**: 单张图片的处理时间

---

## 快速开始

### 基本用法

```bash
# 使用默认Ollama配置测试5张图片
python src/benchmark_models.py \
  --images /path/to/test/images \
  --count 5

# 指定配置文件测试多个模型
python src/benchmark_models.py \
  --images /path/to/test/images \
  --count 10 \
  --config benchmark_config.json
```

---

## 配置文件格式

### 示例配置文件

创建 `benchmark_config.json`:

```json
{
  "models": [
    {
      "name": "Qwen3-VL-4B (Ollama)",
      "model_name": "qwen3-vl:4b",
      "model_type": "ollama",
      "description": "Ollama本地部署，4B参数"
    },
    {
      "name": "Qwen3-VL-4B (vLLM)",
      "model_name": "Qwen/Qwen3-VL-4B",
      "model_type": "openai",
      "api_base": "http://localhost:8000/v1",
      "description": "vLLM高性能API服务"
    },
    {
      "name": "MiniCPM-V-2.5 (本地)",
      "model_name": "minicpm-v-2.5",
      "model_type": "local",
      "model_path": "/path/to/MiniCPM-V-2_5",
      "description": "本地Transformers加载"
    },
    {
      "name": "豆包多模态 (在线API)",
      "model_name": "doubao-vision-pro",
      "model_type": "openai",
      "api_base": "https://ark.cn-beijing.volces.com/api/v3",
      "api_key": "your-api-key-here",
      "description": "字节跳动豆包在线API"
    }
  ]
}
```

### 配置参数说明

每个模型配置包含以下字段：

| 字段 | 必填 | 说明 |
|-----|------|-----|
| `name` | 是 | 模型显示名称 |
| `model_name` | 是 | 模型标识符 |
| `model_type` | 是 | 模型类型: `ollama`, `local`, `openai` |
| `model_path` | 条件 | 本地模型路径 (仅`local`类型需要) |
| `api_base` | 条件 | API服务地址 (仅`openai`类型需要) |
| `api_key` | 可选 | API密钥 (某些API需要) |
| `description` | 可选 | 模型描述信息 |

---

## 命令行参数

```bash
python src/benchmark_models.py \
  --config CONFIG_FILE \          # 模型配置文件 (JSON格式)
  --images IMAGE_PATH \           # 测试图片目录或单个文件
  --count COUNT \                 # 测试图片数量 (默认: 5)
  --tag-count TAG_COUNT \         # 每张图片的标签数量 (默认: 20)
  --language LANGUAGE \           # 标签语言 (默认: zh)
  --description \                 # 生成描述 (默认启用)
  --no-description \              # 不生成描述
  --resize WIDTHxHEIGHT \        # 图片尺寸 (默认: 512x512)
  --output OUTPUT_FILE            # 报告输出路径 (默认: benchmark_report.json)
```

### 参数详解

#### --config
模型配置文件路径。如果不指定，将使用默认的Ollama配置。

#### --images
测试图片的路径，可以是：
- 目录路径: 自动从中选取前N张图片
- 文件路径: 测试单个图片

#### --count
从指定目录中选取的测试图片数量。建议:
- 快速测试: 5-10张
- 完整测试: 20-50张
- 准确评估: 100+张

#### --tag-count
每张图片生成的标签数量。影响因素:
- 较少标签(10-15): 速度快，但可能遗漏细节
- 中等标签(20): 推荐，平衡速度和质量
- 较多标签(30+): 更详细，但耗时更长

#### --language
标签和描述的语言，支持:
- `zh`: 中文 (推荐用于中文场景)
- `en`: 英文
- `ja`: 日语
- `ko`: 韩语
- 等其他语言

#### --description / --no-description
是否生成图片描述。描述会显著增加处理时间(约2x)，但提供更丰富的语义信息。

#### --resize
图片缩放尺寸。影响:
- 更小(256x256): 处理更快，但精度降低
- 中等(512x512): 推荐，平衡速度和质量
- 更大(768x768, 1024x1024): 更高精度，但更慢

#### --output
测试报告保存路径。报告为JSON格式，包含详细的性能数据和每张图片的结果。

---

## 使用示例

### 示例1: 快速测试Ollama

```bash
# 测试5张图片，使用默认Ollama配置
python src/benchmark_models.py \
  --images test_images \
  --count 5 \
  --language zh \
  --tag-count 20
```

### 示例2: 对比多个模型后端

创建配置文件 `benchmark_config.json`:
```json
{
  "models": [
    {
      "name": "Ollama-Qwen3-VL-4B",
      "model_name": "qwen3-vl:4b",
      "model_type": "ollama",
      "description": "Ollama本地服务"
    },
    {
      "name": "vLLM-Qwen3-VL-4B",
      "model_name": "Qwen/Qwen3-VL-4B",
      "model_type": "openai",
      "api_base": "http://localhost:8000/v1",
      "description": "vLLM高性能推理"
    },
    {
      "name": "Local-MiniCPM",
      "model_name": "minicpm-v-2.5",
      "model_type": "local",
      "model_path": "/path/to/models/MiniCPM-V-2_5",
      "description": "本地Transformers"
    }
  ]
}
```

运行测试:
```bash
python src/benchmark_models.py \
  --config benchmark_config.json \
  --images ~/Pictures/test_set \
  --count 10 \
  --language zh \
  --tag-count 20 \
  --description \
  --output comparison_report.json
```

### 示例3: 测试豆包在线API

配置文件 `doubao_config.json`:
```json
{
  "models": [
    {
      "name": "豆包多模态Pro",
      "model_name": "doubao-vision-pro",
      "model_type": "openai",
      "api_base": "https://ark.cn-beijing.volces.com/api/v3",
      "api_key": "YOUR_API_KEY",
      "description": "字节跳动豆包在线API"
    },
    {
      "name": "Qwen3-VL-4B本地",
      "model_name": "qwen3-vl:4b",
      "model_type": "ollama",
      "description": "本地对照组"
    }
  ]
}
```

运行:
```bash
python src/benchmark_models.py \
  --config doubao_config.json \
  --images test_images \
  --count 20 \
  --language zh \
  --output doubao_comparison.json
```

### 示例4: 大规模准确率测试

```bash
# 使用100张图片进行全面测试
python src/benchmark_models.py \
  --config full_comparison.json \
  --images /path/to/test_dataset \
  --count 100 \
  --tag-count 20 \
  --language zh \
  --description \
  --resize 512x512 \
  --output full_benchmark_report.json
```

### 示例5: 快速性能测试(不生成描述)

```bash
# 仅测试标签生成速度
python src/benchmark_models.py \
  --config benchmark_config.json \
  --images test_images \
  --count 50 \
  --tag-count 20 \
  --no-description \
  --output speed_test_report.json
```

---

## 报告解读

### 终端输出

测试完成后会在终端显示汇总报告:

```
================================================================================
基准测试报告
================================================================================

测试配置:
  图片数量: 10
  标签数量: 20
  生成描述: True
  语言: zh
  图片尺寸: 512x512

性能对比:
模型                      类型       成功率      平均耗时      平均标签数
--------------------------------------------------------------------------------
Ollama-Qwen3-VL-4B       ollama      100.0%      3245ms        19.8
vLLM-Qwen3-VL-4B         openai      100.0%      1876ms        20.0
Local-MiniCPM            local       100.0%      2912ms        18.5
豆包多模态Pro             openai       90.0%      5432ms        19.1

详细结果:
Ollama-Qwen3-VL-4B (ollama):
  成功: 10/10
  失败: 0/10
  平均耗时: 3245ms
  平均标签数: 19.8

vLLM-Qwen3-VL-4B (openai):
  成功: 10/10
  失败: 0/10
  平均耗时: 1876ms
  平均标签数: 20.0
```

### JSON报告结构

生成的JSON报告包含详细数据:

```json
{
  "test_config": {
    "num_images": 10,
    "tag_count": 20,
    "generate_description": true,
    "language": "zh",
    "image_size": "512x512"
  },
  "models": [
    {
      "name": "Ollama-Qwen3-VL-4B",
      "type": "ollama",
      "total_images": 10,
      "success_count": 10,
      "failed_count": 0,
      "success_rate": 100.0,
      "avg_processing_time_ms": 3245,
      "avg_tags_count": 19.8,
      "detailed_results": [
        {
          "model_name": "Ollama-Qwen3-VL-4B",
          "model_type": "ollama",
          "image_path": "/path/to/image1.jpg",
          "tags": ["标签1", "标签2", ...],
          "description": "图片描述...",
          "processing_time_ms": 3100,
          "status": "success"
        },
        ...
      ]
    }
  ]
}
```

---

## 性能指标分析

### 关键指标

1. **成功率 (Success Rate)**
   - 理想值: 100%
   - 如果低于95%，需要检查:
     - API密钥是否正确
     - 网络连接是否稳定
     - 模型配置是否正确

2. **平均处理时间 (Avg Processing Time)**
   - 优秀: < 2000ms
   - 良好: 2000-5000ms
   - 一般: 5000-10000ms
   - 需优化: > 10000ms

3. **平均标签数 (Avg Tags Count)**
   - 应接近设置的 `tag_count` 参数
   - 如果明显偏低，可能模型返回的标签较少

### 性能优化建议

根据测试结果，可以采取不同优化策略:

| 问题 | 可能原因 | 解决方案 |
|-----|---------|---------|
| 处理太慢 | 模型太大 | 使用更小的模型(2B-4B) |
| 处理太慢 | 网络延迟 | 使用本地部署 |
| 处理太慢 | 单线程 | 实现多进程并发 |
| 成功率低 | API限流 | 降低并发数或使用本地模型 |
| 标签质量差 | 模型不合适 | 更换更大或专业的模型 |
| 标签太少 | 模型限制 | 增加 `tag_count` 参数 |

---

## 常见模型API配置

### 1. 豆包(Doubao)多模态

```json
{
  "name": "豆包多模态",
  "model_name": "doubao-vision-pro",
  "model_type": "openai",
  "api_base": "https://ark.cn-beijing.volces.com/api/v3",
  "api_key": "YOUR_API_KEY"
}
```

获取API Key: https://console.volcengine.com/ark

### 2. 通义千问VL

```json
{
  "name": "通义千问VL",
  "model_name": "qwen-vl-plus",
  "model_type": "openai",
  "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "api_key": "YOUR_API_KEY"
}
```

获取API Key: https://dashscope.console.aliyun.com/

### 3. vLLM本地部署

启动vLLM服务:
```bash
python -m vllm.entrypoints.openai.api_server \
  --model openbmb/MiniCPM-V-2_5 \
  --port 8000
```

配置:
```json
{
  "name": "vLLM-MiniCPM",
  "model_name": "minicpm-v",
  "model_type": "openai",
  "api_base": "http://localhost:8000/v1"
}
```

### 4. Ollama本地

启动Ollama并拉取模型:
```bash
ollama pull qwen3-vl:4b
```

配置:
```json
{
  "name": "Ollama-Qwen3-VL",
  "model_name": "qwen3-vl:4b",
  "model_type": "ollama"
}
```

### 5. 本地Transformers

下载模型:
```bash
git lfs clone https://huggingface.co/openbmb/MiniCPM-V-2_5
```

配置:
```json
{
  "name": "本地MiniCPM",
  "model_name": "minicpm-v-2.5",
  "model_type": "local",
  "model_path": "/path/to/MiniCPM-V-2_5"
}
```

---

## 故障排除

### 问题1: 模型初始化失败

**错误信息**: `Model initialization failed`

**可能原因**:
- Ollama服务未启动
- 模型未下载
- API密钥错误
- 网络连接问题

**解决方法**:
```bash
# 检查Ollama服务
ollama list

# 启动模型
ollama pull qwen3-vl:4b

# 测试API连接
curl -X POST http://localhost:11434/api/generate -d '{"model":"qwen3-vl:4b","prompt":"test"}'
```

### 问题2: API调用失败

**错误信息**: `Failed to generate tags`

**可能原因**:
- API限流
- 余额不足
- 网络超时

**解决方法**:
- 检查API文档的限流策略
- 增加重试机制
- 检查账户余额

### 问题3: 本地模型加载失败

**错误信息**: `Failed to load model`

**可能原因**:
- 模型路径错误
- 依赖库未安装
- 显存不足

**解决方法**:
```bash
# 安装依赖
pip install transformers torch accelerate

# 检查显存
nvidia-smi

# 使用CPU运行
export CUDA_VISIBLE_DEVICES=""
```

### 问题4: 处理速度极慢

**可能原因**:
- 模型太大
- 未使用GPU
- 网络延迟高

**解决方法**:
- 使用更小的模型
- 确保GPU可用
- 使用本地部署
- 减小图片尺寸

---

## 最佳实践

1. **测试集准备**
   - 选择代表性图片
   - 包含不同场景和复杂度
   - 准备50-100张作为基准测试集

2. **多轮测试**
   - 第一轮: 快速测试5-10张，验证配置
   - 第二轮: 中等规模20-30张，初步对比
   - 第三轮: 大规模50-100张，准确评估

3. **公平对比**
   - 使用相同的测试图片
   - 使用相同的参数设置
   - 在相同的硬件环境下测试

4. **结果记录**
   - 保存每次测试的JSON报告
   - 记录测试环境和配置
   - 建立性能基线数据

5. **渐进优化**
   - 先测试基准性能
   - 识别瓶颈
   - 针对性优化
   - 再次测试验证

---

## 总结

使用 `benchmark_models.py` 可以系统地比较不同模型后端的性能:

1. **Ollama**: 最简单，适合快速开始
2. **本地模型**: 完全离线，适合无网络环境
3. **在线API**: 性能最好，适合生产环境

根据测试结果选择最适合你的方案，在速度、成本和质量之间找到最佳平衡点。
