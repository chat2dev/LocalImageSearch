"""
Database operations module
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple


class Database:
    """SQLite database operations class"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connect()
        self._create_table()

    def _connect(self):
        """Establish database connection"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def _create_table(self):
        """Create table"""
        sql = """
        CREATE TABLE IF NOT EXISTS image_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_unique_id TEXT UNIQUE NOT NULL,
            image_path TEXT NOT NULL,
            tags TEXT NOT NULL,
            description TEXT,
            model_name TEXT NOT NULL,
            image_size TEXT NOT NULL,
            tag_count INTEGER NOT NULL CHECK (tag_count > 0),
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            original_width INTEGER,
            original_height INTEGER,
            image_format TEXT,
            status TEXT DEFAULT 'success',
            error_message TEXT,
            processing_time INTEGER,
            index_status TEXT DEFAULT 'not_indexed',
            language TEXT DEFAULT 'en'
        );
        """
        self.cursor.execute(sql)
        self.conn.commit()

        # Create indexes
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_image_unique_id ON image_tags(image_unique_id)",
            "CREATE INDEX IF NOT EXISTS idx_image_path ON image_tags(image_path)",
            "CREATE INDEX IF NOT EXISTS idx_model_name ON image_tags(model_name)",
            "CREATE INDEX IF NOT EXISTS idx_generated_at ON image_tags(generated_at)",
            "CREATE INDEX IF NOT EXISTS idx_status ON image_tags(status)",
            "CREATE INDEX IF NOT EXISTS idx_model_time ON image_tags(model_name, generated_at)"
        ]

        for idx_sql in indexes:
            self.cursor.execute(idx_sql)
        self.conn.commit()

    def insert_tag(
        self,
        image_unique_id: str,
        image_path: str,
        tags: str,
        description: Optional[str],
        model_name: str,
        image_size: str,
        tag_count: int,
        original_width: Optional[int] = None,
        original_height: Optional[int] = None,
        image_format: Optional[str] = None,
        status: str = 'success',
        error_message: Optional[str] = None,
        processing_time: Optional[int] = None,
        language: str = 'en'
    ):
        """Insert tag record"""
        try:
            sql = """
            INSERT OR REPLACE INTO image_tags (
                image_unique_id, image_path, tags, description,
                model_name, image_size, tag_count, original_width,
                original_height, image_format, status, error_message,
                processing_time, language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (
                image_unique_id, image_path, tags, description,
                model_name, image_size, tag_count, original_width,
                original_height, image_format, status, error_message,
                processing_time, language
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting tag: {e}")
            self.conn.rollback()
            return False

    def get_tags_by_image_id(self, image_unique_id: str) -> Optional[Tuple]:
        """Get tags by unique image ID"""
        sql = "SELECT * FROM image_tags WHERE image_unique_id = ?"
        self.cursor.execute(sql, (image_unique_id,))
        return self.cursor.fetchone()

    def get_all_tags(self) -> List[Tuple]:
        """Get all tag records"""
        sql = "SELECT * FROM image_tags"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def get_tags_by_path(self, image_path: str) -> List[Tuple]:
        """Get tags by image path"""
        sql = "SELECT * FROM image_tags WHERE image_path LIKE ?"
        self.cursor.execute(sql, (f"%{image_path}%",))
        return self.cursor.fetchall()

    def get_tags_by_model(self, model_name: str) -> List[Tuple]:
        """Get tags by model name"""
        sql = "SELECT * FROM image_tags WHERE model_name = ?"
        self.cursor.execute(sql, (model_name,))
        return self.cursor.fetchall()

    def count_tags(self) -> int:
        """Count total tags"""
        sql = "SELECT COUNT(*) FROM image_tags"
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close()