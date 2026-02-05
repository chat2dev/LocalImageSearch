# 安装说明

## 1. 系统要求

### 1.1 硬件要求

- **CPU**：至少 2 核
- **内存**：至少 8 GB（推荐 16 GB 或更高）
- **存储**：至少 10 GB 可用空间（用于存储模型和数据库）
- **GPU**：可选（推荐 NVIDIA GPU，支持 CUDA）

### 1.2 软件要求

- **操作系统**：
  - macOS 10.15 或更高版本
  - Linux（推荐 Ubuntu 18.04 或更高版本）
  - Windows 10 或更高版本

- **Python**：3.8 或更高版本
- **Ollama**：用于本地模型部署（如果使用本地模型）

## 2. 安装步骤

### 2.1 克隆项目

```bash
git clone <项目地址>
cd project-scripts-tag
```

### 2.2 安装 Python 依赖

#### 方法一：使用 uv（推荐）

```bash
# 初始化虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或者在 Windows 上
# .venv\Scripts\activate

# 安装依赖
uv pip install -r doc/requirements.txt
```

#### 方法二：使用 pip

```bash
pip install -r doc/requirements.txt
```

#### 方法三：使用 Poetry

```bash
poetry install
```

### 2.3 安装 Ollama（如果使用本地模型）

#### macOS 安装

```bash
brew install ollama
```

#### Linux 安装

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Windows 安装

下载并安装：https://ollama.com/download

### 2.4 启动 Ollama 服务

```bash
ollama serve
```

### 2.5 下载模型（可选）

如果使用 Ollama 提供的模型，可以提前下载：

```bash
# 下载 Qwen VL 模型（4B 参数）
ollama pull qwen-vl:4b

# 或下载 Llava 模型（3B 参数）
ollama pull llava-v1.6:3b
```

## 3. 验证安装

### 3.1 检查 Python 依赖

```bash
python -m pip list | grep -E "pillow|requests|PyYAML|tqdm"
```

### 3.2 检查 Ollama 服务

```bash
curl http://localhost:11434/api/tags
```

### 3.3 运行系统测试

```bash
python src/main.py --help
```

## 4. 配置系统

### 4.1 创建配置文件

在项目根目录下创建 `config.yaml` 文件：

```yaml
# config.yaml
model: "qwen-vl:4b"
image_path: "/path/to/your/images"
resize: "512x512"
tag_count: 10
generate_description: true
db_path: "./data/image_tags.db"
```

### 4.2 配置说明

| 配置项                | 说明                          |
|-----------------------|-------------------------------|
| model                 | 模型名称（如 qwen-vl:4b）      |
| image_path            | 图片路径（文件或目录）        |
| resize                | 图片缩放尺寸（宽×高）         |
| tag_count             | 标注关键字数量                |
| generate_description  | 是否生成图片描述              |
| db_path               | 数据库文件路径                |

## 5. 常见问题

### 5.1 模型加载失败

**问题**：运行时出现 `Error calling model` 错误

**解决方案**：
1. 确保 Ollama 服务正在运行
2. 检查模型是否已正确下载
3. 验证模型名称是否正确
4. 检查网络连接

### 5.2 图片处理错误

**问题**：图片无法加载或处理

**解决方案**：
1. 检查图片路径是否正确
2. 确保图片格式被支持（JPEG、PNG、BMP 等）
3. 检查文件权限
4. 确保有足够的磁盘空间

### 5.3 数据库连接问题

**问题**：无法连接到 SQLite 数据库

**解决方案**：
1. 检查数据库文件路径是否可写
2. 确保所在目录有写入权限
3. 检查磁盘空间
4. 尝试删除数据库文件并重新运行

### 5.4 内存不足

**问题**：运行时出现内存不足错误

**解决方案**：
1. 减小图片缩放尺寸
2. 减少并发处理数
3. 使用更小参数的模型
4. 增加系统内存

## 6. 卸载

### 6.1 卸载依赖

```bash
# 使用 uv
uv pip uninstall -r doc/requirements.txt

# 或使用 pip
pip uninstall -r doc/requirements.txt
```

### 6.2 删除项目

```bash
rm -rf project-scripts-tag
```

### 6.3 卸载 Ollama

```bash
# macOS
brew uninstall ollama

# Linux
rm /usr/local/bin/ollama
rm -rf ~/.ollama

# Windows
# 使用控制面板卸载
```