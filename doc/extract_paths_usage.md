# 图片路径提取工具使用说明

## 功能概述

`extract_image_paths.py` 是一个用于从指定目录提取所有图片文件路径并保存到文本文件的工具。

## 基本用法

```bash
python src/extract_image_paths.py --directory <目录路径> --output <输出文件>
```

## 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--directory` | 是 | - | 要搜索图片的目录路径 |
| `--output` | 否 | `image_paths.txt` | 输出文件路径 |
| `--no-recursive` | 否 | False | 不递归搜索子目录 |
| `--relative` | 否 | False | 保存相对路径而不是绝对路径 |

## 支持的图片格式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- GIF (.gif)
- WEBP (.webp)

## 使用示例

### 示例 1: 提取目录下所有图片的绝对路径

```bash
python src/extract_image_paths.py --directory /Users/user/Pictures --output all_images.txt
```

输出示例：
```
/Users/user/Pictures/photo1.jpg
/Users/user/Pictures/photo2.png
/Users/user/Pictures/vacation/beach.jpg
/Users/user/Pictures/vacation/sunset.png
```

### 示例 2: 提取相对路径

```bash
python src/extract_image_paths.py --directory /Users/user/Pictures --output images.txt --relative
```

输出示例：
```
photo1.jpg
photo2.png
vacation/beach.jpg
vacation/sunset.png
```

### 示例 3: 只搜索当前目录（不递归）

```bash
python src/extract_image_paths.py --directory /Users/user/Pictures --output current_dir.txt --no-recursive
```

输出示例（不包含子目录中的图片）：
```
/Users/user/Pictures/photo1.jpg
/Users/user/Pictures/photo2.png
```

### 示例 4: 结合使用多个参数

```bash
python src/extract_image_paths.py \
  --directory /Users/user/Pictures \
  --output my_photos.txt \
  --relative \
  --no-recursive
```

## 典型应用场景

### 1. 批量处理前的准备

在使用图片标注系统处理大量图片之前，先提取所有图片路径：

```bash
# 提取所有图片路径
python src/extract_image_paths.py --directory /path/to/images --output image_list.txt

# 查看图片数量
wc -l image_list.txt

# 然后进行批量标注
python src/main.py --image-path /path/to/images --model qwen3-vl:4b --language zh
```

### 2. 图片库管理

创建图片库的索引：

```bash
python src/extract_image_paths.py \
  --directory ~/Pictures \
  --output ~/Documents/photo_index.txt \
  --relative
```

### 3. 备份验证

验证备份目录中的图片文件：

```bash
# 提取源目录图片列表
python src/extract_image_paths.py --directory /original --output original_list.txt

# 提取备份目录图片列表
python src/extract_image_paths.py --directory /backup --output backup_list.txt

# 比较两个列表
diff original_list.txt backup_list.txt
```

### 4. 与其他工具集成

提取图片路径后，可以使用其他工具处理：

```bash
# 提取路径
python src/extract_image_paths.py --directory /path/to/images --output images.txt

# 使用 xargs 进行批量操作
cat images.txt | xargs -I {} convert {} -resize 800x600 {}_resized.jpg

# 或者使用 Python 脚本处理
cat images.txt | xargs -I {} python my_script.py {}
```

## 输出格式

输出文件是一个纯文本文件，每行包含一个图片文件路径：

```
/path/to/image1.jpg
/path/to/image2.png
/path/to/subdir/image3.jpg
```

## 错误处理

### 目录不存在

```bash
$ python src/extract_image_paths.py --directory /nonexistent --output output.txt
错误: 目录不存在: /nonexistent
```

### 没有找到图片

```bash
$ python src/extract_image_paths.py --directory /empty_dir --output output.txt
未找到图片文件
```

### 无法写入输出文件

```bash
$ python src/extract_image_paths.py --directory /path --output /readonly/output.txt
错误: 无法写入文件 /readonly/output.txt: [Errno 13] Permission denied
```

## 性能说明

- 对于大型目录（10万+ 图片），提取过程可能需要几分钟
- 使用 `--no-recursive` 可以加快搜索速度
- 输出文件大小取决于路径长度和图片数量

## 高级用法

### 结合 grep 过滤结果

```bash
# 提取所有图片路径
python src/extract_image_paths.py --directory /path/to/images --output all_images.txt

# 只保留 PNG 图片
grep "\.png$" all_images.txt > png_images.txt

# 只保留特定目录的图片
grep "/vacation/" all_images.txt > vacation_images.txt
```

### 统计图片数量

```bash
# 按格式统计
python src/extract_image_paths.py --directory /path/to/images --output all.txt
echo "JPEG: $(grep -c '\.jpe\?g$' all.txt)"
echo "PNG: $(grep -c '\.png$' all.txt)"
echo "Total: $(wc -l < all.txt)"
```

### 创建图片清单报告

```bash
# 提取路径
python src/extract_image_paths.py --directory ~/Pictures --output images.txt

# 生成报告
echo "图片库报告 - $(date)" > report.txt
echo "总数: $(wc -l < images.txt)" >> report.txt
echo "" >> report.txt
echo "文件列表:" >> report.txt
cat images.txt >> report.txt
```

## 注意事项

1. 大小写敏感：脚本会同时搜索小写和大写扩展名（如 .jpg 和 .JPG）
2. 符号链接：脚本会跟随符号链接
3. 隐藏文件：隐藏文件（以 . 开头）会被包含在结果中
4. 路径格式：所有路径会被转换为绝对路径（除非使用 `--relative` 参数）

## 与主程序集成

提取的路径文件可以配合主程序使用：

```bash
# 1. 提取所有图片路径
python src/extract_image_paths.py --directory /path/to/images --output images.txt

# 2. 查看图片列表
head images.txt

# 3. 使用主程序处理这些图片
python src/main.py --image-path /path/to/images --model qwen3-vl:4b --language zh --tag-count 20 --description
```
