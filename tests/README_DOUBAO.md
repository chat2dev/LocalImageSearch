# 豆包大模型测试指南

## 概述

本目录包含了用于测试豆包（Doubao）视觉大模型的脚本，可以评估豆包在图片自动标注任务上的表现。

## 前置条件

### 1. 环境变量配置

确保 `~/.bashrc` 中已配置：

```bash
export DOUBAO_API_KEY=your-api-key-here
export DOUBAO_BASE_URL="https://ark.cn-beijing.volces.com/api/v3/"
```

加载环境变量：
```bash
source ~/.bashrc
```

### 2. 获取豆包 Endpoint ID

豆包需要使用 endpoint ID（而不是模型名称）来调用 API。Endpoint ID 格式通常为：

```
ep-20250206174555-xxxxx
```

您需要：
1. 登录豆包控制台
2. 创建或找到您的视觉模型端点
3. 复制 endpoint ID

## 测试脚本说明

### test_doubao_api.py - API 连接测试

测试豆包 API 是否可访问：

```bash
uv run python tests/test_doubao_api.py
```

**输出示例：**
- ✓ API 配置正确
- ❌ 需要提供有效的 endpoint ID

### test_doubao.py - 图片标注测试

使用豆包模型测试图片自动标注：

```bash
# 测试默认图片（中文标签）
uv run python tests/test_doubao.py --model ep-xxxxx

# 测试指定图片（英文标签）
uv run python tests/test_doubao.py \
  --model ep-xxxxx \
  --images ~/Pictures/test1.jpg ~/Pictures/test2.jpg \
  --language en \
  --tag-count 15

# 测试默认图片（日文标签）
uv run python tests/test_doubao.py \
  --model ep-xxxxx \
  --language ja \
  --tag-count 20
```

**参数说明：**
- `--model`: （必需）豆包 endpoint ID
- `--images`: 测试图片路径（可选，默认使用 tests/prompt/test_images/ 下的图片）
- `--language`: 标签语言（zh/en/ja/ko，默认 zh）
- `--tag-count`: 生成标签数量（默认 10）

## 测试流程

### 步骤 1: 验证 API 连接

```bash
source ~/.bashrc
uv run python tests/test_doubao_api.py
```

### 步骤 2: 获取 Endpoint ID

从豆包控制台获取您的视觉模型 endpoint ID。

### 步骤 3: 运行标注测试

```bash
# 替换 ep-xxxxx 为您的实际 endpoint ID
uv run python tests/test_doubao.py --model ep-20250206174555-xxxxx
```

### 步骤 4: 查看测试结果

测试脚本会输出：
- 每张图片的标注结果
- 成功/失败统计
- 错误信息（如有）

## 输出示例

```
======================================================================
Test 1/3: test_colored_rectangles.jpg
======================================================================
Loading image...
✓ Image loaded (12345 bytes)
Generating 10 tags using Doubao...
✓ Successfully generated 10 tags:
  1. 几何图形
  2. 矩形
  3. 颜色鲜艳
  4. 红色方块
  5. 蓝色方块
  ...

======================================================================
Test Summary
======================================================================
Total: 3
✓ Success: 3
❌ Failed: 0
Success Rate: 3/3 (100.0%)
```

## 性能对比

您可以使用相同的测试图片对比豆包和 Ollama 的效果：

```bash
# 测试豆包
uv run python tests/test_doubao.py \
  --model ep-xxxxx \
  --images tests/prompt/test_images/test_colored_rectangles.jpg \
  --language zh

# 测试 Ollama (qwen3-vl:4b)
uv run python tests/prompt/test_tag_generation.py
```

## 在实际项目中使用豆包

测试通过后，可以在主程序中使用豆包：

```bash
# 使用 .env 配置
cat > .env << 'EOF'
MODEL_TYPE=openai
MODEL_NAME=ep-20250206174555-xxxxx
API_BASE=${DOUBAO_BASE_URL}
API_KEY=${DOUBAO_API_KEY}
LANGUAGE=zh
TAG_COUNT=10
MAX_WORKERS=5
EOF

# 运行标注
uv run python src/main.py --image-path ~/Pictures
```

或者直接使用 CLI 参数：

```bash
source ~/.bashrc

uv run python src/main.py \
  --image-path ~/Pictures \
  --model-type openai \
  --model ep-20250206174555-xxxxx \
  --api-base "$DOUBAO_BASE_URL" \
  --api-key "$DOUBAO_API_KEY" \
  --language zh \
  --tag-count 10
```

## 常见问题

### Q1: 报错 "InvalidEndpointOrModel.NotFound"

**原因：** Endpoint ID 不存在或无权访问

**解决：**
1. 检查 endpoint ID 是否正确
2. 确认该 endpoint 在您的账号下可用
3. 检查 API key 是否正确

### Q2: 报错 "Authentication failed"

**原因：** API key 无效

**解决：**
1. 检查 `DOUBAO_API_KEY` 是否正确设置
2. 运行 `source ~/.bashrc` 重新加载环境变量
3. 验证 API key 是否过期

### Q3: 标注结果质量不佳

**建议：**
1. 调整 `--tag-count` 参数
2. 尝试不同的 `--language` 选项
3. 检查测试图片质量和内容
4. 参考 `prompts.yaml` 优化提示词

### Q4: 如何修改提示词？

豆包使用与 OpenAI 兼容的接口，提示词配置在 `prompts.yaml` 文件中：

```yaml
system_prompts:
  zh: "你生成 {tag_count} 个逗号分隔的图片标签。"

tag_prompts:
  zh: |
    {tag_count} 个逗号分隔的标签：
```

修改后重新测试即可生效。

## 技术细节

- **API 格式：** OpenAI-compatible chat completions
  - 豆包 API 路径：`${DOUBAO_BASE_URL}/chat/completions`
  - 注意：豆包的 base_url 已包含版本号（/api/v3），无需额外添加 /v1
- **图片格式：** Base64 编码的 JPEG
- **图片尺寸：**
  - 默认：512x512（可配置）
  - 最小要求：14x14 像素（豆包限制）
- **超时时间：** 60 秒
- **Token 限制：** 512 tokens（可在代码中调整）
- **环境变量：**
  - `DOUBAO_API_KEY` - API 密钥
  - `DOUBAO_BASE_URL` - API 基础 URL（已包含版本号）
  - `DOUBAO_MODEL_NAME` - 模型 endpoint ID

## 相关文件

- `test_doubao_api.py` - API 连接测试脚本
- `test_doubao.py` - 图片标注测试脚本
- `../src/model_factory.py` - OpenAI 兼容模型实现
- `../prompts.yaml` - 提示词配置
- `../.env.example` - 环境变量配置示例
