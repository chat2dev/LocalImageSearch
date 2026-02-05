"""
Image Annotation Data Model
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ImageTags(Base):
    """
    Image annotation table model
    Corresponds to the image_tags table, containing image annotation results and index status
    """
    __tablename__ = "image_tags"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Auto-increment primary key")
    image_unique_id = Column(String(64), unique=True, nullable=False, comment="Image unique identifier (SHA-256 hash based on path)")
    image_path = Column(String(1024), nullable=False, comment="Image file path")
    tags = Column(String(1024), nullable=False, comment="Annotation tags (comma-separated string)")
    description = Column(Text, nullable=True, comment="Image description (optional, JSON format or plain text)")
    model_name = Column(String(128), nullable=False, comment="Model name used for annotation")
    image_size = Column(String(32), nullable=False, comment="Image size at processing time (format: width x height)")
    tag_count = Column(Integer, nullable=False, comment="Number of tags")
    generated_at = Column(TIMESTAMP, default=datetime.utcnow, comment="Annotation generation timestamp")
    original_width = Column(Integer, nullable=True, comment="Original width")
    original_height = Column(Integer, nullable=True, comment="Original height")
    image_format = Column(String(32), nullable=True, comment="Image format (JPEG/PNG/BMP etc.)")
    status = Column(
        String(32),
        default="success",
        comment="Annotation status (success/failed/processing)",
        server_default="success",
        info={"check": "status IN ('success', 'failed', 'processing')"}
    )
    error_message = Column(Text, nullable=True, comment="Error message (recorded on failure)")
    processing_time = Column(Integer, nullable=True, comment="Processing time (milliseconds)")
    index_status = Column(
        String(32),
        default="not_indexed",
        comment="Index status (not_indexed/indexing/indexed/failed)",
        server_default="not_indexed",
        info={"check": "index_status IN ('not_indexed', 'indexing', 'indexed', 'failed')"}
    )

    __table_args__ = (
        CheckConstraint(tag_count > 0, name="ck_tag_count_positive"),
    )

    def __repr__(self):
        return f"<ImageTags(image_unique_id='{self.image_unique_id}', tags='{self.tags}')>"

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            "id": self.id,
            "image_unique_id": self.image_unique_id,
            "image_path": self.image_path,
            "tags": self.tags,
            "description": self.description,
            "model_name": self.model_name,
            "image_size": self.image_size,
            "tag_count": self.tag_count,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "original_width": self.original_width,
            "original_height": self.original_height,
            "image_format": self.image_format,
            "status": self.status,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            "index_status": self.index_status
        }

    @property
    def tag_list(self):
        """Get list of tags (convert comma-separated string to list)"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
