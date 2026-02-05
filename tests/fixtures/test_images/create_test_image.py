#!/usr/bin/env python3
"""
创建测试图片
"""
from PIL import Image, ImageDraw, ImageFont
import os


def create_test_image():
    """创建测试图片"""
    # 创建红色背景图片
    width, height = 400, 300
    img = Image.new('RGB', (width, height), color='red')
    draw = ImageDraw.Draw(img)

    # 添加文字
    try:
        # 使用默认字体
        font = ImageFont.truetype("Arial.ttf", 48)
    except IOError:
        # 如果 Arial 字体不可用，使用默认字体
        font = ImageFont.load_default()

    text = "Test Image"
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), text, fill='white', font=font)

    # 保存图片
    output_path = "test_images/test_image_1.jpg"
    img.save(output_path, "JPEG")
    print(f"Created test image at: {output_path}")

    # 创建另一张测试图片（蓝色背景）
    img2 = Image.new('RGB', (width, height), color='blue')
    draw2 = ImageDraw.Draw(img2)
    text2 = "Second Test"
    text2_width, text2_height = draw2.textbbox((0, 0), text2, font=font)[2:]
    x2 = (width - text2_width) // 2
    y2 = (height - text2_height) // 2
    draw2.text((x2, y2), text2, fill='white', font=font)
    output_path2 = "test_images/test_image_2.jpg"
    img2.save(output_path2, "JPEG")
    print(f"Created test image at: {output_path2}")

    return output_path, output_path2


if __name__ == "__main__":
    # 创建测试目录
    os.makedirs("test_images", exist_ok=True)
    create_test_image()