# 使用说明

## 1. 快速开始

### 1.1 命令行方式

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行标注脚本
python src/main.py --image-path /path/to/your/images --model qwen-vl:4b --resize 512x512 --tag-count 10 --description
```

### 1.2 配置文件方式

创建 `config.yaml` 文件：

```yaml
model: "qwen-vl:4b"
image_path: "/path/to/your/images"
resize: "512x512"
tag_count: 10
generate_description: true
db_path: "./data/image_tags.db"
```

然后运行：

```bash
python src/main.py --config config.yaml
```

## 2. 命令参数说明

### 2.1 必选参数

| 参数                | 描述                          | 示例                          |
|---------------------|-------------------------------|-------------------------------|
| --image-path        | 图片路径（文件或目录）        | `/path/to/images`             |

### 2.2 可选参数

| 参数                | 描述                          | 示例                          | 默认值                        |
|---------------------|-------------------------------|-------------------------------|-------------------------------|
| --model             | 模型名称                      | `qwen-vl:4b`                  | `qwen-vl:4b`                  |
| --resize            | 图片缩放尺寸（宽×高）         | `512x512`                     | `512x512`                     |
| --tag-count         | 标注关键字数量                | `10`                          | `10`                          |
| --description       | 生成图片描述                  | -                             | `False`                       |
| --db-path           | 数据库路径                    | `./data/tags.db`              | `./data/image_tags.db`        |
| --max-workers       | 并行处理线程数                | `5`                           | `5`                           |
| --config            | 配置文件路径                  | `config.yaml`                 | -                             |
| --help              | 显示帮助信息                  | -                             | -                             |

## 3. 使用示例

### 3.1 标注单个图片

```bash
python src/main.py --image-path /path/to/single/image.jpg --model qwen-vl:4b
```

### 3.2 标注目录中的所有图片

```bash
python src/main.py --image-path /path/to/image/directory --model qwen-vl:4b --resize 768x768 --tag-count 15 --description
```

### 3.3 使用配置文件

创建 `config.yaml`：

```yaml
model: "llava-v1.6:3b"
image_path: "/path/to/images"
resize: "640x640"
tag_count: 12
generate_description: true
db_path: "./data/my_tags.db"
```

运行：

```bash
python src/main.py --config config.yaml
```

## 4. 输出说明

### 4.1 控制台输出

运行时会显示：

```
========================================
图片自动标注系统
========================================
Config:
  Model: qwen-vl:4b
  Image Path: /path/to/images
  Resize: 512x512
  Tag Count: 10
  Generate Description: True
  DB Path: ./data/image_tags.db
========================================
找到 5 个图片文件

处理进度: 100%|██████████| 5/5 [00:15<00:00,  3.12s/张]

========================================
处理完成
========================================
总文件数: 5
成功处理: 5
失败处理: 0
数据库位置: ~/.LocalImageSearch/data/image_tags.db
```

### 4.2 数据库存储

标注结果存储在 SQLite 数据库中，包含以下信息：

- 图片唯一ID
- 图片路径
- 标签（逗号分隔）
- 图片描述（可选）
- 使用的模型
- 图片尺寸
- 标签数量
- 生成时间

## 5. 查询标注结果

### 5.1 使用 SQLite 客户端

```bash
# 打开数据库
sqlite3 data/image_tags.db

# 查询所有记录
SELECT * FROM image_tags;

# 查询特定路径的图片
SELECT * FROM image_tags WHERE image_path LIKE '%example.jpg';

# 查询特定模型的结果
SELECT * FROM image_tags WHERE model_name = 'qwen-vl:4b';

# 统计标签数量
SELECT COUNT(*) FROM image_tags;
```

### 5.2 导出数据

```bash
# 导出为 CSV 文件
sqlite3 -header -csv data/image_tags.db "SELECT * FROM image_tags;" > tags.csv
```

## 6. 性能优化

### 6.1 图片尺寸优化

- 减小缩放尺寸（如 256x256）可提高处理速度
- 增大尺寸（如 1024x1024）可提高标注质量，但会增加处理时间

### 6.2 模型选择

- 使用较小参数的模型（如 llava-v1.6:3b）处理速度更快
- 使用较大参数的模型（如 qwen-vl:7b）标注质量更高

### 6.3 并发处理

系统支持并行处理，可通过 `--max-workers` 参数或环境变量 `MAX_WORKERS` 配置：

```bash
# 使用 5 个并行线程（默认）
python src/main.py --image-path /path/to/images --max-workers 5

# 使用 10 个并行线程（加快处理速度）
python src/main.py --image-path /path/to/images --max-workers 10

# 禁用并行处理（串行模式）
python src/main.py --image-path /path/to/images --max-workers 1
```

**注意事项：**
- 增加并行度可以加快处理速度，但也会增加 CPU 和内存使用
- 建议根据系统资源和模型性能调整并行度
- 对于资源有限的系统，建议使用较小的 `max-workers` 值（如 2-3）

## 7. 高级功能

### 7.1 增量标注

系统会自动跳过已标注的图片（基于图片唯一ID）。

### 7.2 支持的图片格式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- GIF (.gif) - 仅处理第一帧
- WEBP (.webp)

### 7.3 支持的模型

- qwen-vl:4b（默认）
- qwen-vl:7b
- llava-v1.6:3b
- llava-v1.6:7b
- 其他支持图片标注的 Ollama 模型

## 8. 问题排查

### 8.1 图片未被识别

**原因**：图片格式不支持或文件损坏

**解决方案**：
- 检查图片格式是否在支持列表中
- 尝试重新保存图片
- 验证文件完整性

### 8.2 标签质量低

**解决方案**：
- 使用较大参数的模型
- 增大图片缩放尺寸
- 调整标签数量参数
- 检查模型是否适合图片内容

### 8.3 处理速度慢

**解决方案**：
- 使用较小参数的模型
- 减小图片缩放尺寸
- 确保系统资源充足（内存、CPU、GPU）

## 9. 最佳实践

### 9.1 批处理建议

- 对于大量图片，考虑分批次处理
- 定期备份数据库
- 监控系统资源使用情况

### 9.2 模型选择

- 对于一般用途，推荐使用 qwen-vl:4b 或 llava-v1.6:3b
- 对于高质量要求，使用 qwen-vl:7b 或 llava-v1.6:7b
- 对于快速处理，使用更小参数的模型

### 9.3 图片预处理

- 确保图片光线充足，内容清晰
- 避免过大或过小的图片
- 对于文字识别，使用分辨率较高的图片