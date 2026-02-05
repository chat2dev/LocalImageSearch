#!/usr/bin/env python3
"""
Script to translate Chinese comments and docstrings to English
"""

import os
import re
from pathlib import Path

# Translation mappings for common Chinese terms
TRANSLATIONS = {
    # Module/file level
    "文本向量化服务模块": "Text vectorization service module",
    "数据库连接和操作模块": "Database connection and operations module",
    "FAISS索引服务模块": "FAISS indexing service module",
    "搜索引擎服务模块": "Search engine service module",
    "图像爬虫服务模块": "Image crawler service module",
    "图像标注服务模块": "Image annotation service module",

    # Class level
    "数据库管理器": "Database manager",
    "使用 Sentence-BERT 模型进行文本向量化": "Text vectorization using Sentence-BERT model",
    "FAISS 索引管理器": "FAISS index manager",
    "搜索引擎": "Search engine",
    "图像爬虫": "Image crawler",
    "图像标注器": "Image annotator",
    "测试 Sentence-BERT 向量化器": "Test Sentence-BERT vectorizer",
    "测试数据库操作": "Test database operations",

    # Method level
    "初始化数据库连接": "Initialize database connection",
    "确保表存在并包含所需字段": "Ensure tables exist and contain required fields",
    "检查并添加 index_status 字段": "Check and add index_status field if it doesn't exist",
    "获取数据库会话": "Get database session",
    "获取数据库会话（直接使用）": "Get database session (for direct use)",
    "获取图像标注记录": "Get image annotation records",
    "更新图像的索引状态": "Update the index status of an image",
    "批量更新图像的索引状态": "Batch update the index status of multiple images",
    "根据图像唯一标识符列表获取记录": "Get records by a list of image unique identifiers",

    "初始化 Sentence-BERT 向量化器": "Initialize Sentence-BERT vectorizer",
    "加载 Sentence-BERT 模型": "Load Sentence-BERT model",
    "将单个文本转换为向量": "Convert a single text into a vector",
    "批量将文本转换为向量": "Convert multiple texts into vectors in batch",
    "将标签列表转换为向量": "Convert a list of tags into a vector",

    "初始化 FAISS 索引": "Initialize FAISS index",
    "构建索引": "Build index",
    "添加向量到索引": "Add vectors to index",
    "搜索相似向量": "Search for similar vectors",
    "保存索引": "Save index",
    "加载索引": "Load index",

    "初始化搜索引擎": "Initialize search engine",
    "搜索": "Search",
    "文本搜索": "Text search",
    "标签搜索": "Tag search",

    "初始化图像爬虫": "Initialize image crawler",
    "爬取图像": "Crawl images",
    "扫描目录": "Scan directory",
    "处理图像": "Process image",

    "初始化图像标注器": "Initialize image annotator",
    "标注图像": "Annotate image",
    "生成标签": "Generate tags",

    # Common parameters
    "模型名称": "Model name",
    "默认使用配置中的模型": "defaults to configured model",
    "数据库会话": "Database session",
    "图像唯一标识符": "Unique identifier for the image",
    "图像唯一标识符列表": "List of unique identifiers for images",
    "索引状态": "Index status value",
    "标注状态过滤": "Filter by annotation status",
    "索引状态过滤": "Filter by index status",
    "返回数量限制": "Maximum number of records to return",
    "错误信息（失败时提供）": "Error message (if status is failed)",
    "输入文本": "Input text",
    "文本列表": "List of texts",
    "标签列表": "List of tags",

    # Comments
    "检查 image_tags 表是否存在": "Check if image_tags table exists",
    "检查 index_status 字段是否存在": "Check if index_status field exists",
    "检查字段是否存在": "Check if field exists",
    "添加 index_status 字段": "Add index_status field",
    "将标签合并成一个文本进行向量化": "Merge tags into a single text for vectorization",
    "单例实例": "Singleton instance",

    # Returns
    "图像标注记录列表": "List of image annotation records",
    "文本向量": "Text vector",
    "文本向量数组，形状为 (n, dimension)": "Array of text vectors with shape (n, dimension)",
    "标签向量": "Tag vector",

    # Test messages
    "测试模块导入": "Testing module imports",
    "成功导入": "Successfully imported",
    "导入失败": "Import failed",
    "测试数据库操作": "Testing database operations",
    "数据库操作失败": "Database operation failed",
    "测试图片处理": "Testing image processor",
    "图片信息": "Image info",
    "图片预处理成功": "Image preprocessing successful",
    "原始大小": "Original size",
    "处理后大小": "Processed size",
    "数据大小": "Data size",
    "测试工具函数": "Testing utility functions",
    "工具函数测试失败": "Utility function test failed",
    "测试配置管理": "Testing configuration management",
    "配置类初始化成功": "Config class initialized successfully",
    "默认配置": "Default configuration",
    "模型": "Model",
    "尺寸": "Resize",
    "标签数量": "Tag Count",
    "数据库路径": "DB Path",
    "尺寸解析成功": "Size parsing successful",
    "无效尺寸解析成功": "Invalid size parsing successful",
    "测试基本文本向量化功能": "Test basic text vectorization",
    "测试空文本向量化": "Test empty text vectorization",
    "测试空白文本向量化": "Test whitespace text vectorization",
    "测试基本标签向量化": "Test basic tag vectorization",
    "测试空标签向量化": "Test empty tag vectorization",
    "测试单个标签向量化": "Test single tag vectorization",
    "测试批量文本向量化": "Test batch text vectorization",
    "测试包含空文本的批量向量化": "Test batch vectorization with empty texts",
    "测试相似文本的向量相似度": "Test vector similarity for similar texts",
}


def translate_chinese_in_file(file_path: Path) -> bool:
    """
    Translate Chinese comments and docstrings in a Python file

    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply translations
        for chinese, english in TRANSLATIONS.items():
            content = content.replace(chinese, english)

        # If content changed, write it back
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files"""
    project_root = Path(__file__).parent.parent

    # Directories to process
    dirs_to_process = [
        project_root / "src",
        project_root / "tests",
    ]

    total_files = 0
    modified_files = 0

    for directory in dirs_to_process:
        if not directory.exists():
            continue

        for py_file in directory.rglob("*.py"):
            # Skip this script itself
            if py_file == Path(__file__):
                continue

            total_files += 1
            if translate_chinese_in_file(py_file):
                modified_files += 1

    print(f"\n{'='*60}")
    print(f"Translation complete!")
    print(f"Total files processed: {total_files}")
    print(f"Files modified: {modified_files}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
