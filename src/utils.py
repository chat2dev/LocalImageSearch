"""
工具函数模块
"""
import hashlib
from pathlib import Path


def generate_unique_id(image_path):
    """
    根据图片全路径生成唯一ID

    Args:
        image_path (str): 图片路径

    Returns:
        str: 唯一ID（SHA-256哈希值）
    """
    path_str = str(Path(image_path).resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()


def get_image_files(directory):
    """
    获取目录中的所有图片文件

    Args:
        directory (str): 目录路径

    Returns:
        list: 图片文件路径列表
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
    directory_path = Path(directory)
    image_files = []

    if directory_path.is_dir():
        for ext in image_extensions:
            image_files.extend(directory_path.rglob(f"*{ext}"))
            image_files.extend(directory_path.rglob(f"*{ext.upper()}"))
    elif directory_path.is_file() and directory_path.suffix.lower() in image_extensions:
        image_files.append(directory_path)

    return sorted([str(file) for file in image_files])