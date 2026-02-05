"""Database access layer for image tags storage."""
from .db import (
    db_manager,
    DatabaseManager,
    get_image_tags,
    update_index_status,
    batch_update_index_status,
    get_image_tags_by_ids,
)

__all__ = [
    "db_manager",
    "DatabaseManager",
    "get_image_tags",
    "update_index_status",
    "batch_update_index_status",
    "get_image_tags_by_ids",
]
