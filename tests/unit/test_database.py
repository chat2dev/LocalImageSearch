"""
数据库操作单元测试
"""
import pytest
import os
import sqlite3
from src.database.db import db_manager, get_image_tags, update_index_status, get_image_tags_by_ids
from src.models.image_tags import ImageTags
from src.config.settings import settings


class TestDatabaseOperations:
    """Testing database operations"""

    @pytest.fixture(scope="function")
    def temp_db_path(self, tmpdir):
        """创建临时数据库文件"""
        temp_db = os.path.join(tmpdir, "temp_image_tags.db")
        yield temp_db
        if os.path.exists(temp_db):
            os.remove(temp_db)

    def test_get_image_tags_basic(self):
        """测试基本查询功能"""
        session = db_manager.get_session()
        try:
            # 获取所有图像标签记录
            results = get_image_tags(session)
            assert isinstance(results, list)

            # 获取成功标注的图像标签记录
            success_results = get_image_tags(session, status="success")
            assert isinstance(success_results, list)

            for result in success_results:
                assert result.status == "success"

            print(f"Total images: {len(results)}, success: {len(success_results)}")
        finally:
            session.close()

    def test_get_image_tags_index_status(self):
        """测试按Index status value查询"""
        session = db_manager.get_session()
        try:
            # 获取未索引的图像标签记录
            not_indexed = get_image_tags(session, index_status="not_indexed")
            assert isinstance(not_indexed, list)
            for result in not_indexed:
                assert result.index_status == "not_indexed"

            # 获取已索引的图像标签记录
            indexed = get_image_tags(session, index_status="indexed")
            assert isinstance(indexed, list)
            for result in indexed:
                assert result.index_status == "indexed"

            print(f"Not indexed: {len(not_indexed)}, indexed: {len(indexed)}")
        finally:
            session.close()

    def test_update_index_status(self):
        """测试更新Index status value"""
        session = db_manager.get_session()
        try:
            # 获取一个测试记录
            test_records = get_image_tags(session, limit=1)
            if not test_records:
                pytest.skip("No test data available")

            test_record = test_records[0]
            original_status = test_record.index_status

            # 更新Index status value
            new_status = "indexing" if original_status != "indexing" else "indexed"
            update_index_status(session, test_record.image_unique_id, new_status)

            # 验证更新
            updated_record = get_image_tags_by_ids(session, [test_record.image_unique_id])
            assert updated_record
            assert updated_record[0].index_status == new_status

            # 恢复原始状态
            update_index_status(session, test_record.image_unique_id, original_status)

            print(f"Successfully updated index status from {original_status} to {new_status}")
        finally:
            session.close()

    def test_get_image_tags_by_ids(self):
        """测试根据图像唯一ID查询"""
        session = db_manager.get_session()
        try:
            # 获取一些测试记录
            test_records = get_image_tags(session, limit=2)
            if len(test_records) < 2:
                pytest.skip("Not enough test data available")

            # 提取图像唯一ID列表
            test_ids = [record.image_unique_id for record in test_records]

            # 根据ID查询
            results = get_image_tags_by_ids(session, test_ids)
            assert len(results) > 0

            # 验证结果
            result_ids = [record.image_unique_id for record in results]
            assert all(test_id in result_ids for test_id in test_ids)

            print(f"Found {len(results)} records by IDs")
        finally:
            session.close()

    def test_database_connection(self):
        """测试数据库连接"""
        session = db_manager.get_session()
        try:
            # 执行简单的查询
            from sqlalchemy.sql import text
            result = session.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1

            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            assert "image_tags" in inspector.get_table_names()

            print("Database connection test passed")
        finally:
            session.close()

    def test_table_schema(self):
        """测试表结构"""
        session = db_manager.get_session()
        try:
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            columns = inspector.get_columns("image_tags")

            # 验证必要的字段是否存在
            required_columns = ["id", "image_unique_id", "image_path", "tags", "model_name",
                                "status", "index_status"]

            for col_name in required_columns:
                assert any(col["name"] == col_name for col in columns), f"Column '{col_name}' not found"

            print("Table schema test passed")
        finally:
            session.close()
