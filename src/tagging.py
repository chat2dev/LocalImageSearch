"""
标注核心模块
"""
from typing import List, Optional, Tuple
from .image_processor import load_and_preprocess_image, get_image_info
from .model_factory import create_model, ModelAPIError
from .utils import generate_unique_id
from .db_manager import Database
import time


def process_image(
    image_path: str,
    model_name: str,
    resize_width: int,
    resize_height: int,
    tag_count: int,
    generate_description: bool,
    db: Database,
    language: str = "en",
    model_type: str = "ollama",
    api_base: str = "",
    api_key: str = "",
    force_reprocess: bool = False,
    prompt_config_path: str = ""
) -> bool:
    """
    处理单个图片的标注流程

    Args:
        image_path: 图片路径
        model_name: Model name
        resize_width: 缩放宽度
        resize_height: 缩放高度
        tag_count: Tag Count
        generate_description: 是否生成描述
        db: 数据库实例
        language: 标签和描述的语言
        force_reprocess: 是否强制重新处理已处理过的图片

    Returns:
        是否处理成功
    """
    start_time = time.time()

    # 生成图片唯一 ID
    image_unique_id = generate_unique_id(image_path)

    # 检查是否已处理过（force_reprocess模式跳过）
    if not force_reprocess:
        existing_tags = db.get_tags_by_image_id(image_unique_id)
        if existing_tags:
            print(f"Image already processed: {image_path}")
            return False

    print(f"Processing image: {image_path}")

    # 获取Image info
    image_info = get_image_info(image_path)

    # 加载和预处理图片
    image_bytes = load_and_preprocess_image(
        image_path,
        resize_width,
        resize_height
    )

    if not image_bytes:
        db.insert_tag(
            image_unique_id=image_unique_id,
            image_path=image_path,
            tags="",
            description=None,
            model_name=model_name,
            image_size=f"{resize_width}x{resize_height}",
            tag_count=0,
            original_width=image_info.get("width"),
            original_height=image_info.get("height"),
            image_format=image_info.get("format"),
            status='failed',
            error_message="Failed to load or process image",
            processing_time=int((time.time() - start_time) * 1000),
            language=language
        )
        return False

    # 创建Model
    model = create_model(model_name, language, model_type, api_base, api_key, prompt_config_path)

    # Generate tags
    try:
        raw_tags = model.generate_tags(image_bytes, tag_count)
    except ModelAPIError as e:
        db.insert_tag(
            image_unique_id=image_unique_id,
            image_path=image_path,
            tags="",
            description=None,
            model_name=model_name,
            image_size=f"{resize_width}x{resize_height}",
            tag_count=0,
            original_width=image_info.get("width"),
            original_height=image_info.get("height"),
            image_format=image_info.get("format"),
            status='failed',
            error_message=e.to_error_message(),
            processing_time=int((time.time() - start_time) * 1000),
            language=language
        )
        print(f"Failed [{e.error_type}]: {image_path} - {str(e)}")
        return False

    if not raw_tags:
        db.insert_tag(
            image_unique_id=image_unique_id,
            image_path=image_path,
            tags="",
            description=None,
            model_name=model_name,
            image_size=f"{resize_width}x{resize_height}",
            tag_count=0,
            original_width=image_info.get("width"),
            original_height=image_info.get("height"),
            image_format=image_info.get("format"),
            status='failed',
            error_message="标签为空(未知原因)",
            processing_time=int((time.time() - start_time) * 1000),
            language=language
        )
        print(f"Failed: {image_path} - 标签为空")
        return False

    tags = parse_tags(raw_tags, tag_count)

    # 生成描述（可选）
    description = None
    if generate_description:
        description = model.generate_description(image_bytes)
        if description:
            description = description.strip()

    # 保存到数据库
    db.insert_tag(
        image_unique_id=image_unique_id,
        image_path=image_path,
        tags=",".join(tags),
        description=description,
        model_name=model_name,
        image_size=f"{resize_width}x{resize_height}",
        tag_count=len(tags),
        original_width=image_info.get("width"),
        original_height=image_info.get("height"),
        image_format=image_info.get("format"),
        status='success',
        processing_time=int((time.time() - start_time) * 1000),
        language=language
    )

    print(f"Successfully processed: {image_path}")
    print(f"Tags: {', '.join(tags)}")
    if description:
        print(f"Description: {description}")
    print()

    return True


def parse_tags(tag_text: str, expected_count: int) -> List[str]:
    """
    解析Model返回的标签文本

    Args:
        tag_text: 原始标签文本
        expected_count: 期望的Tag Count

    Returns:
        List of tags
    """
    if not tag_text:
        return []

    # 移除多余字符
    tag_text = tag_text.strip()

    # 使用多种分隔符分割
    separators = [",", "，", "、", ";", "；", " "]
    for sep in separators:
        if sep in tag_text:
            tags = [t.strip() for t in tag_text.split(sep) if t.strip()]
            if tags:
                return tags[:expected_count]

    # 如果没有分隔符，尝试按空格分割或返回整段文本
    if len(tag_text) > 0:
        if " " in tag_text:
            tags = tag_text.split()
            return [t.strip() for t in tags if t.strip()][:expected_count]
        return [tag_text][:expected_count]

    return []