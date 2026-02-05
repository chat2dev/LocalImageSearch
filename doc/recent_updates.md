# 最近更新

## 更新日期: 2026-01-30

### 新增功能

#### 1. 多语言支持

现在系统支持8种语言的图片标注和描述生成：

- **en** - 英文 (默认)
- **zh** - 中文
- **ja** - 日文
- **ko** - 韩文
- **es** - 西班牙文
- **fr** - 法文
- **de** - 德文
- **ru** - 俄文

**使用方法：**

```bash
# 生成中文标注和描述
python src/main.py --image-path /path/to/images --model qwen3-vl:4b --language zh --description

# 生成日文标注
python src/main.py --image-path /path/to/images --model qwen3-vl:4b --language ja
```

**配置文件示例：**

```yaml
model: "qwen3-vl:4b"
image_path: "/path/to/your/images"
resize: "512x512"
tag_count: 20
generate_description: true
db_path: "./data/image_tags.db"
language: "zh"
```

#### 2. 图片路径提取工具

新增 `extract_image_paths.py` 脚本，用于从指定目录提取所有图片文件路径。

**主要功能：**
- 递归或非递归搜索图片文件
- 支持绝对路径或相对路径输出
- 支持所有常见图片格式 (JPEG, PNG, BMP, GIF, WEBP)
- 结果保存到文本文件

**使用方法：**

```bash
# 基本用法
python src/extract_image_paths.py --directory /path/to/images --output image_paths.txt

# 使用相对路径
python src/extract_image_paths.py --directory /path/to/images --output image_paths.txt --relative

# 不递归搜索子目录
python src/extract_image_paths.py --directory /path/to/images --output image_paths.txt --no-recursive
```

**应用场景：**
- 批量处理前查看图片列表
- 创建图片库索引
- 备份验证
- 与其他工具集成

### 核心改进

#### 1. 配置管理 (src/config.py)
- 新增 `language` 参数，默认值为 "en"
- 命令行参数支持 `--language` 选项
- YAML 配置文件支持 `language` 字段

#### 2. 模型接口 (src/models.py)
- `BaseModel` 和 `OllamaModel` 现在接受 `language` 参数
- 提示词根据语言自动调整
- 增强的响应解析，支持多语言字符集：
  - 英文：字母字符匹配
  - 中文：Unicode 范围 U+4E00-U+9FFF
  - 日文：平假名、片假名和汉字
  - 韩文：谚文 Unicode 范围 U+AC00-U+D7AF
  - 欧洲语言：扩展拉丁字符和西里尔字符

#### 3. 数据库架构 (src/database.py)
- `image_tags` 表新增 `language` 字段
- 所有插入操作现在包含语言信息
- 可以按语言查询标注结果

#### 4. 处理流程 (src/tagging.py, src/main.py)
- `process_image()` 函数现在接受 `language` 参数
- 语言参数在整个处理流程中传递
- 所有数据库记录都包含语言信息

### 文档更新

- **CLAUDE.md**: 添加了语言配置说明和使用示例
- **doc/extract_paths_usage.md**: 新增图片路径提取工具的完整使用文档
- **doc/recent_updates.md**: 本文档，总结所有最近的更新

### 示例用法

#### 示例 1: 处理中文标注

```bash
python src/main.py \
  --image-path /Users/user/Pictures \
  --model qwen3-vl:4b \
  --language zh \
  --tag-count 20 \
  --description
```

#### 示例 2: 提取图片路径

```bash
# 提取所有图片路径
python src/extract_image_paths.py \
  --directory /Users/user/Pictures \
  --output my_images.txt

# 查看结果
head my_images.txt
```

#### 示例 3: 使用配置文件

创建 `config.yaml`:

```yaml
model: "qwen3-vl:4b"
image_path: "/Users/user/Pictures"
resize: "512x512"
tag_count: 20
generate_description: true
db_path: "./data/image_tags.db"
language: "zh"
```

运行：

```bash
python src/main.py --config config.yaml
```

### 数据库查询示例

查询不同语言的标注结果：

```sql
-- 查询所有中文标注
SELECT * FROM image_tags WHERE language = 'zh';

-- 查询所有英文标注
SELECT * FROM image_tags WHERE language = 'en';

-- 统计各语言标注数量
SELECT language, COUNT(*) as count
FROM image_tags
GROUP BY language;

-- 查询特定模型的中文标注
SELECT * FROM image_tags
WHERE language = 'zh' AND model_name = 'qwen3-vl:4b';
```

### 兼容性

- 所有现有功能保持向后兼容
- 默认语言为英文 (en)
- 旧数据库会自动添加 `language` 字段（默认值为 'en'）

### 性能

- 多语言支持不影响处理速度
- 响应解析针对不同语言优化
- 数据库索引已优化，支持按语言查询

### 已知限制

1. 模型质量取决于所选的 Ollama 模型对特定语言的支持
2. 某些模型可能在某些语言上表现更好
3. 推荐使用支持多语言的模型，如 qwen3-vl

### 下一步计划

- [ ] 添加批量导出功能（按语言导出）
- [ ] 支持更多语言
- [ ] 添加语言检测功能
- [ ] 优化非英语语言的标签解析算法
- [ ] 添加语言统计和分析工具

### 反馈

如果您在使用过程中遇到任何问题或有改进建议，请提交 Issue 或 Pull Request。
