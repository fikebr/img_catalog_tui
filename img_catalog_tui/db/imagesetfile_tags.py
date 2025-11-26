"""
CRUD operations for the imagesetfile_tags table.
"""

import logging
from typing import Optional, List

from img_catalog_tui.config import Config
from img_catalog_tui.db.utils import get_connection


class ImagesetFileTagsTable:
    """CRUD operations for imagesetfile_tags table."""
    
    def __init__(self, config: Config):
        """
        Initialize ImagesetFileTagsTable.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def create(self, imagesetfile_id: int, tag: str) -> Optional[int]:
        """
        Create a new tag record.
        
        Args:
            imagesetfile_id: Foreign key to imagesetfiles.id
            tag: Tag name
            
        Returns:
            int: ID of created tag, or None if failed
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO imagesetfile_tags (imagesetfile_id, tag)
                    VALUES (?, ?)
                """, (imagesetfile_id, tag))
                tag_id = cursor.lastrowid
                logging.debug(f"Created tag '{tag}' for file {imagesetfile_id}")
                return tag_id
        except Exception as e:
            logging.error(f"Failed to create tag '{tag}' for file {imagesetfile_id}: {e}", exc_info=True)
            return None
    
    def get_by_id(self, tag_id: int) -> Optional[dict]:
        """
        Get tag by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            dict: Tag record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM imagesetfile_tags WHERE id = ?", (tag_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get tag by id {tag_id}: {e}", exc_info=True)
            return None
    
    def get_tags_by_file_id(self, imagesetfile_id: int) -> List[str]:
        """
        Get all tags for a file.
        
        Args:
            imagesetfile_id: File ID
            
        Returns:
            list: List of tag names
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT tag FROM imagesetfile_tags WHERE imagesetfile_id = ? ORDER BY tag",
                    (imagesetfile_id,)
                )
                return [row['tag'] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get tags for file {imagesetfile_id}: {e}", exc_info=True)
            return []
    
    def get_files_by_tag(self, tag: str) -> List[dict]:
        """
        Get all files with a specific tag.
        
        Args:
            tag: Tag name
            
        Returns:
            list: List of file records
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT f.* FROM imagesetfiles f
                    INNER JOIN imagesetfile_tags t ON f.id = t.imagesetfile_id
                    WHERE t.tag = ?
                    ORDER BY f.filename
                """, (tag,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get files by tag '{tag}': {e}", exc_info=True)
            return []
    
    def set_tags_for_file(self, imagesetfile_id: int, tags: List[str]) -> bool:
        """
        Set tags for a file (replaces existing tags).
        
        Args:
            imagesetfile_id: File ID
            tags: List of tag names
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                
                # Delete existing tags
                cursor.execute(
                    "DELETE FROM imagesetfile_tags WHERE imagesetfile_id = ?",
                    (imagesetfile_id,)
                )
                
                # Insert new tags
                for tag in tags:
                    cursor.execute("""
                        INSERT INTO imagesetfile_tags (imagesetfile_id, tag)
                        VALUES (?, ?)
                    """, (imagesetfile_id, tag))
                
                logging.debug(f"Set {len(tags)} tags for file {imagesetfile_id}")
                return True
        except Exception as e:
            logging.error(f"Failed to set tags for file {imagesetfile_id}: {e}", exc_info=True)
            return False
    
    def add_tag(self, imagesetfile_id: int, tag: str) -> bool:
        """
        Add a tag to a file (if not already present).
        
        Args:
            imagesetfile_id: File ID
            tag: Tag name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if tag already exists
            existing_tags = self.get_tags_by_file_id(imagesetfile_id)
            if tag in existing_tags:
                return True
            
            return self.create(imagesetfile_id, tag) is not None
        except Exception as e:
            logging.error(f"Failed to add tag '{tag}' to file {imagesetfile_id}: {e}", exc_info=True)
            return False
    
    def remove_tag(self, imagesetfile_id: int, tag: str) -> bool:
        """
        Remove a tag from a file.
        
        Args:
            imagesetfile_id: File ID
            tag: Tag name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM imagesetfile_tags WHERE imagesetfile_id = ? AND tag = ?",
                    (imagesetfile_id, tag)
                )
                deleted = cursor.rowcount > 0
                if deleted:
                    logging.debug(f"Removed tag '{tag}' from file {imagesetfile_id}")
                return deleted
        except Exception as e:
            logging.error(f"Failed to remove tag '{tag}' from file {imagesetfile_id}: {e}", exc_info=True)
            return False
    
    def delete_by_file_id(self, imagesetfile_id: int) -> bool:
        """
        Delete all tags for a file.
        
        Args:
            imagesetfile_id: File ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM imagesetfile_tags WHERE imagesetfile_id = ?",
                    (imagesetfile_id,)
                )
                logging.debug(f"Deleted all tags for file {imagesetfile_id}")
                return True
        except Exception as e:
            logging.error(f"Failed to delete tags for file {imagesetfile_id}: {e}", exc_info=True)
            return False

