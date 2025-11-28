"""
CRUD operations for the folders table.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime

from img_catalog_tui.config import Config
from img_catalog_tui.db.utils import get_connection


class FoldersTable:
    """CRUD operations for folders table."""
    
    def __init__(self, config: Config):
        """
        Initialize FoldersTable.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def create(self, name: str, path: str) -> Optional[int]:
        """
        Create a new folder record.
        
        Args:
            name: Folder basename
            path: Full filesystem path
            
        Returns:
            int: ID of created folder, or None if failed
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO folders (name, path, updated_at)
                    VALUES (?, ?, ?)
                """, (name, path, datetime.now().isoformat()))
                folder_id = cursor.lastrowid
                logging.debug(f"Created folder: {name} (id: {folder_id})")
                return folder_id
        except Exception as e:
            logging.error(f"Failed to create folder '{name}': {e}", exc_info=True)
            return None
    
    def get_by_id(self, folder_id: int) -> Optional[Dict]:
        """
        Get folder by ID.
        
        Args:
            folder_id: Folder ID
            
        Returns:
            dict: Folder record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get folder by id {folder_id}: {e}", exc_info=True)
            return None
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """
        Get folder by name.
        
        Args:
            name: Folder basename
            
        Returns:
            dict: Folder record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM folders WHERE name = ?", (name,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get folder by name '{name}': {e}", exc_info=True)
            return None
    
    def get_by_path(self, path: str) -> Optional[Dict]:
        """
        Get folder by path.
        
        Args:
            path: Full filesystem path
            
        Returns:
            dict: Folder record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM folders WHERE path = ?", (path,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get folder by path '{path}': {e}", exc_info=True)
            return None
    
    def get_all(self) -> List[Dict]:
        """
        Get all folders.
        
        Returns:
            list: List of folder records
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM folders ORDER BY name")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get all folders: {e}", exc_info=True)
            return []
    
    def get_all_dict(self) -> Dict[str, str]:
        """
        Get all folders as a dictionary mapping name -> path.
        
        Returns:
            dict: Dictionary mapping folder name to path
        """
        folders = self.get_all()
        return {folder['name']: folder['path'] for folder in folders}
    
    def update(self, folder_id: int, name: Optional[str] = None, path: Optional[str] = None) -> bool:
        """
        Update folder record.
        
        Args:
            folder_id: Folder ID
            name: New folder name (optional)
            path: New folder path (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if path is not None:
                updates.append("path = ?")
                params.append(path)
            
            if not updates:
                return True
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(folder_id)
            
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE folders SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                logging.debug(f"Updated folder id {folder_id}")
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Failed to update folder id {folder_id}: {e}", exc_info=True)
            return False
    
    def delete(self, folder_id: int) -> bool:
        """
        Delete folder record (cascade deletes related imagesets).
        
        Args:
            folder_id: Folder ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
                deleted = cursor.rowcount > 0
                if deleted:
                    logging.debug(f"Deleted folder id {folder_id}")
                return deleted
        except Exception as e:
            logging.error(f"Failed to delete folder id {folder_id}: {e}", exc_info=True)
            return False
    
    def delete_by_name(self, name: str) -> bool:
        """
        Delete folder by name.
        
        Args:
            name: Folder basename
            
        Returns:
            bool: True if successful, False otherwise
        """
        folder = self.get_by_name(name)
        if folder:
            return self.delete(folder['id'])
        return False

