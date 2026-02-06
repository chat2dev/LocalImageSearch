#!/bin/bash
#
# Doubao 大模型测试便捷脚本
# 使用方法: ./tests/run_doubao_test.sh [endpoint_id]
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "豆包大模型测试工具"
echo "======================================================================"
echo

# 加载环境变量
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# 检查环境变量
if [ -z "$DOUBAO_API_KEY" ]; then
    echo -e "${RED}❌ 错误: DOUBAO_API_KEY 未设置${NC}"
    echo "   请在 ~/.bashrc 中添加: export DOUBAO_API_KEY=your-key"
    exit 1
fi

if [ -z "$DOUBAO_BASE_URL" ]; then
    echo -e "${RED}❌ 错误: DOUBAO_BASE_URL 未设置${NC}"
    echo "   请在 ~/.bashrc 中添加: export DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/"
    exit 1
fi

echo -e "${GREEN}✓${NC} API Base URL: $DOUBAO_BASE_URL"
echo -e "${GREEN}✓${NC} API Key: ${DOUBAO_API_KEY:0:10}...${DOUBAO_API_KEY: -4}"
echo

# 获取 endpoint ID
ENDPOINT_ID="$1"

if [ -z "$ENDPOINT_ID" ]; then
    echo -e "${YELLOW}请提供豆包 endpoint ID:${NC}"
    echo "  用法: ./tests/run_doubao_test.sh ep-20250206174555-xxxxx"
    echo
    echo "  endpoint ID 格式示例: ep-20250206174555-xxxxx"
    echo "  可在豆包控制台获取"
    echo
    echo -e "${YELLOW}现在进行 API 连接测试...${NC}"
    echo
    uv run python tests/test_doubao_api.py
    exit 0
fi

echo -e "${GREEN}✓${NC} Endpoint ID: $ENDPOINT_ID"
echo

# 检查测试图片
TEST_DIR="tests/prompt/test_images"
if [ ! -d "$TEST_DIR" ]; then
    echo -e "${RED}❌ 测试图片目录不存在: $TEST_DIR${NC}"
    exit 1
fi

# 统计测试图片数量
IMAGE_COUNT=$(find "$TEST_DIR" -name "*.jpg" -o -name "*.png" | wc -l | xargs)
echo -e "${GREEN}✓${NC} 找到 $IMAGE_COUNT 张测试图片"
echo

# 询问测试语言
echo "选择测试语言:"
echo "  1) 中文 (zh)"
echo "  2) 英文 (en)"
echo "  3) 日文 (ja)"
echo "  4) 韩文 (ko)"
read -p "请选择 (1-4, 默认 1): " LANG_CHOICE

case $LANG_CHOICE in
    2) LANGUAGE="en" ;;
    3) LANGUAGE="ja" ;;
    4) LANGUAGE="ko" ;;
    *) LANGUAGE="zh" ;;
esac

echo -e "${GREEN}✓${NC} 测试语言: $LANGUAGE"
echo

# 询问标签数量
read -p "生成标签数量 (默认 10): " TAG_COUNT
TAG_COUNT=${TAG_COUNT:-10}

echo -e "${GREEN}✓${NC} 标签数量: $TAG_COUNT"
echo

# 运行测试
echo "======================================================================"
echo "开始测试豆包大模型..."
echo "======================================================================"
echo

uv run python tests/test_doubao.py \
    --model "$ENDPOINT_ID" \
    --language "$LANGUAGE" \
    --tag-count "$TAG_COUNT"

# 显示测试完成信息
echo
echo "======================================================================"
echo -e "${GREEN}测试完成!${NC}"
echo "======================================================================"
echo
echo "如需在实际项目中使用豆包，请参考:"
echo "  tests/README_DOUBAO.md"
echo
