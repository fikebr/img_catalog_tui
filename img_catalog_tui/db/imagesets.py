"""
CRUD operations for the imagesets table.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime

from img_catalog_tui.config import Config
from img_catalog_tui.db.utils import get_connection


class ImagesetsTable:
    """CRUD operations for imagesets table."""
    
    def __init__(self, config: Config):
        """
        Initialize ImagesetsTable.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def create(
        self,
        folder_id: int,
        name: str,
        folder_path: str,
        imageset_folder_path: str,
        status: Optional[str] = None,
        edits: Optional[str] = None,
        needs: Optional[str] = None,
        good_for: Optional[str] = None,
        source: Optional[str] = None,
        prompt: Optional[str] = None,
        cover_image_path: Optional[str] = None,
        orig_image_path: Optional[str] = None
    ) -> Optional[int]:
        """
        Create a new imageset record.
        
        Args:
            folder_id: Foreign key to folders.id
            name: Imageset name
            folder_path: Full path to parent folder
            imageset_folder_path: Full path to imageset folder
            status: Status value
            edits: Comma-separated edits
            needs: Comma-separated needs
            good_for: Comma-separated good_for values
            source: Image source
            prompt: Prompt text
            cover_image_path: Path to cover image
            orig_image_path: Path to original image
            
        Returns:
            int: ID of created imageset, or None if failed
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO imagesets (
                        folder_id, name, folder_path, imageset_folder_path,
                        status, edits, needs, good_for, source, prompt,
                        cover_image_path, orig_image_path, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    folder_id, name, folder_path, imageset_folder_path,
                    status, edits, needs, good_for, source, prompt,
                    cover_image_path, orig_image_path, datetime.now().isoformat()
                ))
                imageset_id = cursor.lastrowid
                logging.debug(f"Created imageset: {name} (id: {imageset_id})")
                return imageset_id
        except Exception as e:
            logging.error(f"Failed to create imageset '{name}': {e}", exc_info=True)
            return None
    
    def get_by_id(self, imageset_id: int) -> Optional[Dict]:
        """
        Get imageset by ID.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            dict: Imageset record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM imagesets WHERE id = ?", (imageset_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get imageset by id {imageset_id}: {e}", exc_info=True)
            return None
    
    def get_by_folder_and_name(self, folder_id: int, name: str) -> Optional[Dict]:
        """
        Get imageset by folder ID and name.
        
        Args:
            folder_id: Folder ID
            name: Imageset name
            
        Returns:
            dict: Imageset record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imagesets WHERE folder_id = ? AND name = ?",
                    (folder_id, name)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get imageset by folder_id {folder_id} and name '{name}': {e}", exc_info=True)
            return None
    
    def get_by_folder_path_and_name(self, folder_path: str, name: str) -> Optional[Dict]:
        """
        Get imageset by folder path and name.
        
        Args:
            folder_path: Full path to parent folder
            name: Imageset name
            
        Returns:
            dict: Imageset record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imagesets WHERE folder_path = ? AND name = ?",
                    (folder_path, name)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get imageset by folder_path '{folder_path}' and name '{name}': {e}", exc_info=True)
            return None
    
    def get_by_folder_id(self, folder_id: int) -> List[Dict]:
        """
        Get all imagesets for a folder.
        
        Args:
            folder_id: Folder ID
            
        Returns:
            list: List of imageset records
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imagesets WHERE folder_id = ? ORDER BY name",
                    (folder_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get imagesets by folder_id {folder_id}: {e}", exc_info=True)
            return []
    
    def get_by_status(self, status: str) -> List[Dict]:
        """
        Get all imagesets with a specific status.
        
        Args:
            status: Status value
            
        Returns:
            list: List of imageset records
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imagesets WHERE status = ? ORDER BY name",
                    (status,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get imagesets by status '{status}': {e}", exc_info=True)
            return []
    
    def update_field(self, imageset_id: int, field_name: str, value: Optional[str]) -> bool:
        """
        Update a single field of an imageset.
        
        Args:
            imageset_id: Imageset ID
            field_name: Field name to update
            value: New value (can be None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE imagesets SET {field_name} = ?, updated_at = ? WHERE id = ?",
                    (value, datetime.now().isoformat(), imageset_id)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Failed to update imageset {imageset_id} field {field_name}: {e}", exc_info=True)
            return False
    
    def update(
        self,
        imageset_id: int,
        status: Optional[str] = None,
        edits: Optional[str] = None,
        needs: Optional[str] = None,
        good_for: Optional[str] = None,
        source: Optional[str] = None,
        prompt: Optional[str] = None,
        cover_image_path: Optional[str] = None,
        orig_image_path: Optional[str] = None,
        folder_path: Optional[str] = None,
        imageset_folder_path: Optional[str] = None
    ) -> bool:
        """
        Update imageset record.
        
        Args:
            imageset_id: Imageset ID
            status: Status value
            edits: Comma-separated edits
            needs: Comma-separated needs
            good_for: Comma-separated good_for values
            source: Image source
            prompt: Prompt text
            cover_image_path: Path to cover image
            orig_image_path: Path to original image
            folder_path: Full path to parent folder
            imageset_folder_path: Full path to imageset folder
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if edits is not None:
                updates.append("edits = ?")
                params.append(edits)
            if needs is not None:
                updates.append("needs = ?")
                params.append(needs)
            if good_for is not None:
                updates.append("good_for = ?")
                params.append(good_for)
            if source is not None:
                updates.append("source = ?")
                params.append(source)
            if prompt is not None:
                updates.append("prompt = ?")
                params.append(prompt)
            if cover_image_path is not None:
                updates.append("cover_image_path = ?")
                params.append(cover_image_path)
            if orig_image_path is not None:
                updates.append("orig_image_path = ?")
                params.append(orig_image_path)
            if folder_path is not None:
                updates.append("folder_path = ?")
                params.append(folder_path)
            if imageset_folder_path is not None:
                updates.append("imageset_folder_path = ?")
                params.append(imageset_folder_path)
            
            if not updates:
                return True
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(imageset_id)
            
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE imagesets SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                logging.debug(f"Updated imageset id {imageset_id}")
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Failed to update imageset id {imageset_id}: {e}", exc_info=True)
            return False
    
    def delete(self, imageset_id: int) -> bool:
        """
        Delete imageset record (cascade deletes related records).
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM imagesets WHERE id = ?", (imageset_id,))
                deleted = cursor.rowcount > 0
                if deleted:
                    logging.debug(f"Deleted imageset id {imageset_id}")
                return deleted
        except Exception as e:
            logging.error(f"Failed to delete imageset id {imageset_id}: {e}", exc_info=True)
            return False

