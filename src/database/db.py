"""
Database connection and operations module
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from src.config.settings import settings
from src.models.image_tags import Base, ImageTags


class DatabaseManager:
    """Database manager"""

    def __init__(self):
        """Initialize database connection"""
        self.engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure tables exist and contain required fields"""
        try:
            # Check if image_tags table exists
            if not self.engine.dialect.has_table(self.engine.connect(), "image_tags"):
                Base.metadata.create_all(bind=self.engine)
            else:
                # Check if index_status field exists
                self._check_and_add_index_status_column()
        except SQLAlchemyError as e:
            print(f"Error checking/updating database schema: {e}")

    def _check_and_add_index_status_column(self):
        """Check and add index_status field if it doesn't exist"""
        from sqlalchemy import text
        conn = self.engine.connect()
        try:
            # Check if field exists
            result = conn.execute(text("PRAGMA table_info(image_tags)"))
            columns = [column[1] for column in result.fetchall()]

            if "index_status" not in columns:
                # Add index_status field
                conn.execute(text("""
                    ALTER TABLE image_tags
                    ADD COLUMN index_status TEXT DEFAULT 'not_indexed'
                    CHECK (index_status IN ('not_indexed', 'indexing', 'indexed', 'failed'))
                """))
                conn.commit()
                print("Successfully added index_status column to image_tags table")
        except SQLAlchemyError as e:
            print(f"Error adding index_status column: {e}")
            try:
                conn.rollback()
            except:
                pass
        finally:
            conn.close()

    def get_db(self):
        """Get database session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_session(self):
        """Get database session (for direct use)"""
        return self.SessionLocal()


# Singleton instance
db_manager = DatabaseManager()


def get_image_tags(session, status: str = None, index_status: str = None, limit: int = None):
    """
    Get image annotation records

    Args:
        session: Database session
        status: Filter by annotation status
        index_status: Filter by index status
        limit: Maximum number of records to return

    Returns:
        List[ImageTags]: List of image annotation records
    """
    query = session.query(ImageTags)

    if status:
        query = query.filter(ImageTags.status == status)

    if index_status:
        query = query.filter(ImageTags.index_status == index_status)

    if limit:
        query = query.limit(limit)

    return query.all()


def update_index_status(session, image_unique_id: str, index_status: str, error_message: str = None):
    """
    Update the index status of an image

    Args:
        session: Database session
        image_unique_id: Unique identifier for the image
        index_status: Index status value
        error_message: Error message (if status is failed)
    """
    try:
        session.query(ImageTags)\
            .filter(ImageTags.image_unique_id == image_unique_id)\
            .update({
                ImageTags.index_status: index_status,
                ImageTags.error_message: error_message
            })
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise e


def batch_update_index_status(session, image_unique_ids: list, index_status: str):
    """
    Batch update the index status of multiple images

    Args:
        session: Database session
        image_unique_ids: List of unique identifiers for images
        index_status: Index status value
    """
    try:
        session.query(ImageTags)\
            .filter(ImageTags.image_unique_id.in_(image_unique_ids))\
            .update({
                ImageTags.index_status: index_status
            }, synchronize_session=False)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise e


def get_image_tags_by_ids(session, image_unique_ids: list):
    """
    Get records by a list of image unique identifiers

    Args:
        session: Database session
        image_unique_ids: List of unique identifiers for images

    Returns:
        List[ImageTags]: List of image annotation records
    """
    return session.query(ImageTags)\
        .filter(ImageTags.image_unique_id.in_(image_unique_ids))\
        .all()
