"""
Application configuration module
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Database configuration
    # SQLite database file path for storing image annotation results
    _data_dir = Path.home() / ".LocalImageSearch" / "data"
    DATABASE_URL: str = f"sqlite:///{_data_dir / 'image_tags.db'}"

    # FAISS index configuration
    # Directory for storing FAISS index files
    FAISS_INDEX_DIR: str = str(_data_dir / "faiss" / "indexes")
    # Directory for storing FAISS configuration and metadata
    FAISS_CONFIG_DIR: str = str(_data_dir / "faiss" / "config")
    FAISS_INDEX_TYPE: str = "IVFPQ"
    FAISS_DIMENSION: int = 384  # Matches all-MiniLM-L6-v2 model output
    FAISS_NLIST: int = 100
    FAISS_M: int = 8
    FAISS_NBITS_PER_IDX: int = 8
    FAISS_METRIC: str = "L2"

    # Search configuration
    SEARCH_NPROBE: int = 5
    SEARCH_DEFAULT_K: int = 10
    SEARCH_MAX_K: int = 100
    SEARCH_SIMILARITY_THRESHOLD: float = 0.5

    # Vectorizer configuration
    VECTORIZER_MODEL: str = "all-MiniLM-L6-v2"  # 384-dimensional embeddings

    # Index status field values
    INDEX_STATUS_NOT_INDEXED: str = "not_indexed"
    INDEX_STATUS_INDEXING: str = "indexing"
    INDEX_STATUS_INDEXED: str = "indexed"
    INDEX_STATUS_FAILED: str = "failed"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()


def ensure_directories():
    """Ensure required directories exist"""
    data_dir = Path.home() / ".LocalImageSearch" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.FAISS_INDEX_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.FAISS_CONFIG_DIR).mkdir(parents=True, exist_ok=True)
