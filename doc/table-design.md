# 图片自动标注系统表结构设计

## 1. 数据库选择

本系统选择 **SQLite** 数据库，原因如下：

### 优势

- 轻量级，无需独立数据库服务器
- 文件型数据库，易于部署和管理
- Python 内置支持，无需额外依赖
- 足够满足图片标注系统的性能需求
- 适合单机应用场景

### 适用场景

- 图片数量在 10万以内
- 并发访问量较低（单用户或少量用户）
- 数据完整性要求高
- 需要简单的部署和维护

## 2. 表结构设计

### 2.1 核心表：图片标注表 (image_tags)

这是系统的主要数据表，用于存储图片的标注结果。

```sql
CREATE TABLE IF NOT EXISTS image_tags (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 图片唯一标识符（基于路径的SHA-256哈希）
    image_unique_id TEXT UNIQUE NOT NULL,

    -- 图片文件路径
    image_path TEXT NOT NULL,

    -- 标注标签（逗号分隔的字符串）
    tags TEXT NOT NULL,

    -- 图片描述（可选，JSON格式或纯文本）
    description TEXT,

    -- 使用的模型名称
    model_name TEXT NOT NULL,

    -- 处理时的图片尺寸（格式：width×height）
    image_size TEXT NOT NULL,

    -- 标签数量
    tag_count INTEGER NOT NULL,

    -- 标注生成时间
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 图片原始尺寸
    original_width INTEGER,
    original_height INTEGER,

    -- 图片格式（JPEG/PNG/BMP等）
    image_format TEXT,

    -- 标注状态（成功/失败/处理中）
    status TEXT DEFAULT 'success',

    -- 错误信息（失败时记录）
    error_message TEXT,

    -- 处理时间（毫秒）
    processing_time INTEGER
);
```

### 2.2 字段说明

| 字段名                | 类型          | 是否必填 | 说明                          |
|-----------------------|---------------|----------|-------------------------------|
| id                    | INTEGER       | 是       | 自增主键                      |
| image_unique_id       | TEXT          | 是       | 图片唯一ID（基于路径的SHA-256哈希） |
| image_path            | TEXT          | 是       | 图片文件路径                  |
| tags                  | TEXT          | 是       | 标注标签（逗号分隔）          |
| description           | TEXT          | 否       | 图片描述（可选）              |
| model_name            | TEXT          | 是       | 使用的模型名称                |
| image_size            | TEXT          | 是       | 处理时的图片尺寸              |
| tag_count             | INTEGER       | 是       | 标签数量                      |
| generated_at          | TIMESTAMP     | 是       | 标注时间                      |
| original_width        | INTEGER       | 否       | 原始宽度                      |
| original_height       | INTEGER       | 否       | 原始高度                      |
| image_format          | TEXT          | 否       | 图片格式                      |
| status                | TEXT          | 否       | 标注状态                      |
| error_message         | TEXT          | 否       | 错误信息                      |
| processing_time       | INTEGER       | 否       | 处理时间（毫秒）              |

### 2.3 索引设计

为了提高查询效率，建议创建以下索引：

```sql
-- 按图片唯一ID查询（常用场景）
CREATE INDEX IF NOT EXISTS idx_image_unique_id ON image_tags(image_unique_id);

-- 按图片路径查询
CREATE INDEX IF NOT EXISTS idx_image_path ON image_tags(image_path);

-- 按模型名称查询
CREATE INDEX IF NOT EXISTS idx_model_name ON image_tags(model_name);

-- 按时间查询
CREATE INDEX IF NOT EXISTS idx_generated_at ON image_tags(generated_at);

-- 按状态查询
CREATE INDEX IF NOT EXISTS idx_status ON image_tags(status);

-- 复合索引：按模型和时间查询
CREATE INDEX IF NOT EXISTS idx_model_time ON image_tags(model_name, generated_at);
```

## 3. 数据完整性约束

### 3.1 唯一性约束

```sql
-- 图片唯一ID必须唯一
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_image ON image_tags(image_unique_id);
```

### 3.2 非空约束

```sql
-- 确保关键字段不为空
CREATE TABLE IF NOT EXISTS image_tags (
    -- ...
    image_unique_id TEXT UNIQUE NOT NULL,
    image_path TEXT NOT NULL,
    tags TEXT NOT NULL,
    model_name TEXT NOT NULL,
    image_size TEXT NOT NULL,
    tag_count INTEGER NOT NULL,
    -- ...
);
```

### 3.3 检查约束

```sql
-- 标签数量必须大于0
CREATE TABLE IF NOT EXISTS image_tags (
    -- ...
    tag_count INTEGER NOT NULL CHECK (tag_count > 0),
    -- ...
);

-- 状态字段值约束
CREATE TABLE IF NOT EXISTS image_tags (
    -- ...
    status TEXT DEFAULT 'success' CHECK (status IN ('success', 'failed', 'processing')),
    -- ...
);
```

## 4. 表关系设计

本系统采用单表设计，因为：

1. **简单性**：图片标注结果是独立的实体
2. **性能**：单表查询更高效
3. **维护**：单表结构更易于维护
4. **扩展性**：未来可以根据需求添加关联表

## 5. 数据存储策略

### 5.1 数据压缩

- 图片路径使用绝对路径存储，便于定位
- 标签使用逗号分隔的字符串存储，节省空间
- 状态字段使用枚举类型，减少存储开销

### 5.2 数据清理

- 定期清理失败的标注记录（可选）
- 提供删除重复记录的功能
- 支持数据导出和备份

### 5.3 数据迁移

- 版本升级时提供数据迁移脚本
- 支持从其他标注系统导入数据

## 6. 查询优化建议

### 6.1 常用查询场景

```sql
-- 查询所有成功标注的图片
SELECT * FROM image_tags WHERE status = 'success';

-- 查询使用特定模型的标注结果
SELECT * FROM image_tags WHERE model_name = 'qwen-vl:4b';

-- 查询最近一周的标注结果
SELECT * FROM image_tags WHERE generated_at >= date('now', '-7 days');

-- 查询标签包含特定关键词的图片
SELECT * FROM image_tags WHERE tags LIKE '%风景%';

-- 查询处理时间超过5秒的图片
SELECT * FROM image_tags WHERE processing_time > 5000;
```

### 6.2 查询优化

1. **索引覆盖**：创建包含常用查询字段的复合索引
2. **分页查询**：使用 LIMIT 进行分页查询
3. **避免 SELECT ***：只查询需要的字段
4. **使用 LIKE 优化**：避免在大型数据集上使用前导通配符

## 7. 备份与恢复

### 7.1 备份方法

```bash
# 直接复制数据库文件
cp data/image_tags.db data/image_tags.db.backup

# 使用 SQLite 命令备份
sqlite3 data/image_tags.db ".backup data/image_tags.db.backup"
```

### 7.2 恢复方法

```bash
# 直接替换数据库文件
cp data/image_tags.db.backup data/image_tags.db

# 使用 SQLite 命令恢复
sqlite3 data/image_tags.db ".restore data/image_tags.db.backup"
```

### 7.3 自动备份

可以添加定时任务定期备份数据库：

```bash
# 每天凌晨2点备份
0 2 * * * cp /path/to/image_tags.db /path/to/image_tags.db.$(date +\%Y\%m\%d)
```

## 8. 扩展方案

### 8.1 分表设计

如果图片数量大量增长，可以考虑分表策略：

```sql
-- 按月份分表
CREATE TABLE IF NOT EXISTS image_tags_202401 AS SELECT * FROM image_tags WHERE strftime('%Y%m', generated_at) = '202401';
CREATE TABLE IF NOT EXISTS image_tags_202402 AS SELECT * FROM image_tags WHERE strftime('%Y%m', generated_at) = '202402';
-- ...
```

### 8.2 数据库迁移

如果需要更高的性能和可扩展性，可以考虑迁移到其他数据库：

- PostgreSQL：支持高级查询和并发访问
- MySQL：适合大规模数据存储
- MongoDB：适合非结构化数据存储

## 9. 安全性设计

### 9.1 访问控制

- 数据库文件权限控制
- 避免 SQL 注入
- 使用参数化查询

### 9.2 数据加密

- 敏感信息加密存储
- 传输过程加密
- 数据库连接加密

## 10. 测试数据

### 10.1 插入测试数据

```sql
INSERT INTO image_tags (
    image_unique_id, image_path, tags, description, model_name, image_size, tag_count,
    original_width, original_height, image_format, processing_time
) VALUES (
    '5d41402abc4b2a76b9719d911017c592',
    '/path/to/image1.jpg',
    '风景,山脉,天空,树木',
    '一张美丽的山景图片，蓝天、白云和绿色的树木',
    'qwen-vl:4b',
    '512x512',
    4,
    1920,
    1080,
    'JPEG',
    3200
);
```

### 10.2 验证查询

```sql
-- 查询测试数据
SELECT * FROM image_tags WHERE image_unique_id = '5d41402abc4b2a76b9719d911017c592';

-- 验证标签数量
SELECT COUNT(*) FROM image_tags;
```

---

## 11. 总结

本系统的数据库设计具有以下特点：

1. **简单而强大**：单表设计满足所有核心需求
2. **高效查询**：合理的索引设计提高查询效率
3. **数据完整性**：严格的约束确保数据质量
4. **扩展性**：支持分表和数据库迁移
5. **易用性**：简单的查询接口和备份方案

整体设计考虑了系统的性能、可靠性和可维护性，为图片自动标注系统提供了坚实的数据存储基础。