#!/usr/bin/env python3
"""
测试图片自动标注系统的功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_import_modules():
    """Testing module imports"""
    print("=" * 60)
    print("Testing module imports")
    print("=" * 60)

    modules = [
        "src.config",
        "src.utils",
        "src.database",
        "src.image_processor",
        "src.models",
        "src.tagging",
        "src.main"
    ]

    for module in modules:
        try:
            __import__(module)
            print(f"✅ Successfully imported: {module}")
        except Exception as e:
            print(f"❌ Import failed: {module} - {e}")
            return False

    print()
    return True


def test_database_operations():
    """Testing database operations"""
    print("=" * 60)
    print("Testing database operations")
    print("=" * 60)

    try:
        from src.database import Database
        from src.utils import generate_unique_id
        import tempfile
        import os

        # 创建临时数据库
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            temp_db_path = temp_db.name

        # 测试数据库连接
        db = Database(temp_db_path)
        print("✅ 数据库连接成功")

        # 测试创建表
        print("✅ 数据库表创建成功")

        # 测试插入数据
        test_id = generate_unique_id("/test/image/path.jpg")
        db.insert_tag(
            image_unique_id=test_id,
            image_path="/test/image/path.jpg",
            tags="风景,山脉,天空",
            description="一张美丽的山景图片",
            model_name="qwen-vl:4b",
            image_size="512x512",
            tag_count=3,
            original_width=1920,
            original_height=1080,
            image_format="JPEG",
            status="success",
            processing_time=3200
        )
        print("✅ 数据插入成功")

        # 测试查询数据
        result = db.get_tags_by_image_id(test_id)
        if result:
            print("✅ 数据查询成功")
            print(f"   记录ID: {result[0]}")
            print(f"   图片路径: {result[2]}")
            print(f"   标签: {result[3]}")
            print(f"   Model: {result[5]}")

        # 测试统计数据
        count = db.count_tags()
        print(f"✅ 记录数: {count}")

        db.close()

        # 清理临时文件
        os.unlink(temp_db_path)
        print("✅ 临时数据库清理成功")

        print()
        return True

    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        return False


def test_image_processor():
    """Testing image processor"""
    print("=" * 60)
    print("Testing image processor")
    print("=" * 60)

    try:
        from PIL import Image
        from io import BytesIO
        from src.image_processor import load_and_preprocess_image, get_image_info

        # 创建临时图片
        temp_image = Image.new('RGB', (100, 100), color='red')
        temp_image_path = "/tmp/test_image.jpg"
        temp_image.save(temp_image_path)

        # 测试获取Image info
        info = get_image_info(temp_image_path)
        print(f"✅ Image info: {info}")

        # 测试图片预处理
        processed = load_and_preprocess_image(temp_image_path, 256, 256)
        if processed:
            print(f"✅ Image preprocessing successful")
            print(f"   Original size: 100x100")
            print(f"   Processed size: 256x256")
            print(f"   Data size: {len(processed)} bytes")

        # 清理临时文件
        import os
        os.unlink(temp_image_path)

        print()
        return True

    except Exception as e:
        print(f"❌ 图片处理失败: {e}")
        return False


def test_utils():
    """Testing utility functions"""
    print("=" * 60)
    print("Testing utility functions")
    print("=" * 60)

    try:
        from src.utils import generate_unique_id

        # 测试唯一ID生成
        test_path1 = "/test/image1.jpg"
        id1 = generate_unique_id(test_path1)
        id2 = generate_unique_id(test_path1)  # 相同路径应该生成相同ID
        test_path2 = "/test/image2.jpg"
        id3 = generate_unique_id(test_path2)

        print(f"✅ 唯一ID生成:")
        print(f"   路径1: {test_path1}")
        print(f"   ID1: {id1}")
        print(f"   ID2: {id2}")
        print(f"   路径2: {test_path2}")
        print(f"   ID3: {id3}")

        assert id1 == id2, "相同路径应该生成相同ID"
        assert id1 != id3, "不同路径应该生成不同ID"
        print("✅ ID唯一性验证成功")

        print()
        return True

    except Exception as e:
        print(f"❌ Utility function test failed: {e}")
        return False


def test_config():
    """Testing configuration management"""
    print("=" * 60)
    print("Testing configuration management")
    print("=" * 60)

    try:
        from src.cli_config import Config
        config = Config()

        print("✅ Config class initialized successfully")

        # 测试Default configuration
        default_model = config.model
        default_resize = config.resize
        default_tag_count = config.tag_count
        default_db = config.db_path

        print(f"Default configuration:")
        print(f"  Model: {default_model}")
        print(f"  Resize: {default_resize}")
        print(f"  Tag Count: {default_tag_count}")
        print(f"  DB Path: {default_db}")

        # Test resize parsing
        width, height = config.get_resize_dimensions()
        assert width == 512 and height == 512, "Default resize parsing failed"
        print("✅ Size parsing successful")

        # Test invalid resize
        config.resize = "invalid"
        width, height = config.get_resize_dimensions()
        assert width == 512 and height == 512, "Invalid resize parsing failed"
        print("✅ Invalid size parsing successful")

        print()
        return True

    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("图片自动标注系统 - 功能测试")
    print("=" * 60)
    print()

    test_results = []

    test_results.append(test_import_modules())
    test_results.append(test_config())
    test_results.append(test_utils())
    test_results.append(test_image_processor())
    test_results.append(test_database_operations())

    print("=" * 60)
    print("测试结果")
    print("=" * 60)

    passed = sum(test_results)
    failed = len(test_results) - passed

    print(f"通过测试: {passed}/{len(test_results)}")
    print(f"失败测试: {failed}/{len(test_results)}")

    print()

    if failed > 0:
        print("❌ 系统测试失败")
        sys.exit(1)
    else:
        print("✅ 系统测试成功")
        sys.exit(0)


if __name__ == "__main__":
    main()