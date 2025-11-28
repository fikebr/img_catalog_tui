"""
CRUD operations for the imagesetfiles table.
"""

import os
import logging
from typing import Optional, Dict, List
from datetime import datetime

from img_catalog_tui.config import Config
from img_catalog_tui.db.utils import get_connection


class ImagesetFilesTable:
    """CRUD operations for imagesetfiles table."""
    
    def __init__(self, config: Config):
        """
        Initialize ImagesetFilesTable.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def create(
        self,
        imageset_id: int,
        filename: str,
        fullpath: str,
        extension: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> Optional[int]:
        """
        Create a new imagesetfile record.
        
        Args:
            imageset_id: Foreign key to imagesets.id
            filename: Filename (basename only)
            fullpath: Full filesystem path to file
            extension: File extension
            file_type: Type classification
            file_size: File size in bytes (will be calculated if None)
            
        Returns:
            int: ID of created file record, or None if failed
        """
        try:
            # Calculate file size if not provided
            if file_size is None and os.path.exists(fullpath):
                try:
                    file_size = os.path.getsize(fullpath)
                except OSError:
                    file_size = None
            
            # Extract extension if not provided
            if extension is None:
                _, ext = os.path.splitext(filename)
                extension = ext
            
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO imagesetfiles (
                        imageset_id, filename, fullpath, extension,
                        file_type, file_size, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    imageset_id, filename, fullpath, extension,
                    file_type, file_size, datetime.now().isoformat()
                ))
                file_id = cursor.lastrowid
                logging.debug(f"Created file record: {filename} (id: {file_id})")
                return file_id
        except Exception as e:
            logging.error(f"Failed to create file record '{filename}': {e}", exc_info=True)
            return None
    
    def get_by_id(self, file_id: int) -> Optional[Dict]:
        """
        Get file record by ID.
        
        Args:
            file_id: File ID
            
        Returns:
            dict: File record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM imagesetfiles WHERE id = ?", (file_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get file by id {file_id}: {e}", exc_info=True)
            return None
    
    def get_by_imageset_and_filename(self, imageset_id: int, filename: str) -> Optional[Dict]:
        """
        Get file record by imageset ID and filename.
        
        Args:
            imageset_id: Imageset ID
            filename: Filename
            
        Returns:
            dict: File record, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imagesetfiles WHERE imageset_id = ? AND filename = ?",
                    (imageset_id, filename)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Failed to get file '{filename}' for imageset {imageset_id}: {e}", exc_info=True)
            return None
    
    def get_by_imageset_id(self, imageset_id: int) -> List[Dict]:
        """
        Get all files for an imageset.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            list: List of file records
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imagesetfiles WHERE imageset_id = ? ORDER BY filename",
                    (imageset_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get files for imageset {imageset_id}: {e}", exc_info=True)
            return []
    
    def get_by_file_type(self, imageset_id: int, file_type: str) -> List[Dict]:
        """
        Get files of a specific type for an imageset.
        
        Args:
            imageset_id: Imageset ID
            file_type: File type (e.g., "image", "toml", "text")
            
        Returns:
            list: List of file records
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imagesetfiles WHERE imageset_id = ? AND file_type = ? ORDER BY filename",
                    (imageset_id, file_type)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get files of type '{file_type}' for imageset {imageset_id}: {e}", exc_info=True)
            return []
    
    def get_files_dict(self, imageset_id: int) -> Dict[str, Dict]:
        """
        Get all files as a dictionary mapping filename -> file info.
        Similar to the in-memory structure used by Imageset class.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            dict: Dictionary mapping filename to file info dict
        """
        files = self.get_by_imageset_id(imageset_id)
        result = {}
        
        # Import here to avoid circular imports
        from img_catalog_tui.db.imagesetfile_tags import ImagesetFileTagsTable
        tags_table = ImagesetFileTagsTable(self.config)
        
        for file_record in files:
            file_id = file_record['id']
            tags = tags_table.get_tags_by_file_id(file_id)
            
            result[file_record['filename']] = {
                'fullpath': file_record['fullpath'],
                'ext': file_record['extension'] or '',
                'tags': tags,
                'file_type': file_record['file_type'] or 'other'
            }
        
        return result
    
    def update(
        self,
        file_id: int,
        filename: Optional[str] = None,
        fullpath: Optional[str] = None,
        extension: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> bool:
        """
        Update file record.
        
        Args:
            file_id: File ID
            filename: New filename
            fullpath: New fullpath
            extension: New extension
            file_type: New file type
            file_size: New file size
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if filename is not None:
                updates.append("filename = ?")
                params.append(filename)
            if fullpath is not None:
                updates.append("fullpath = ?")
                params.append(fullpath)
                # Recalculate file size if fullpath changed
                if file_size is None and os.path.exists(fullpath):
                    try:
                        file_size = os.path.getsize(fullpath)
                    except OSError:
                        pass
            if extension is not None:
                updates.append("extension = ?")
                params.append(extension)
            if file_type is not None:
                updates.append("file_type = ?")
                params.append(file_type)
            if file_size is not None:
                updates.append("file_size = ?")
                params.append(file_size)
            
            if not updates:
                return True
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(file_id)
            
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE imagesetfiles SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                logging.debug(f"Updated file id {file_id}")
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Failed to update file id {file_id}: {e}", exc_info=True)
            return False
    
    def delete(self, file_id: int) -> bool:
        """
        Delete file record (cascade deletes related tags).
        
        Args:
            file_id: File ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM imagesetfiles WHERE id = ?", (file_id,))
                deleted = cursor.rowcount > 0
                if deleted:
                    logging.debug(f"Deleted file id {file_id}")
                return deleted
        except Exception as e:
            logging.error(f"Failed to delete file id {file_id}: {e}", exc_info=True)
            return False
    
    def delete_by_imageset_id(self, imageset_id: int) -> bool:
        """
        Delete all files for an imageset.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM imagesetfiles WHERE imageset_id = ?", (imageset_id,))
                logging.debug(f"Deleted all files for imageset {imageset_id}")
                return True
        except Exception as e:
            logging.error(f"Failed to delete files for imageset {imageset_id}: {e}", exc_info=True)
            return False
    
    def sync_from_filesystem(self, imageset_id: int, imageset_folder_path: str, config: Config) -> bool:
        """
        Sync file records from filesystem.
        Scans the imageset folder and updates the database.
        
        Args:
            imageset_id: Imageset ID
            imageset_folder_path: Full path to imageset folder
            config: Configuration object (for file tags)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(imageset_folder_path):
                logging.warning(f"Imageset folder does not exist: {imageset_folder_path}")
                return False
            
            # Get file tags from config
            tags = config.get_file_tags()
            img_file_ext = config.config_data.get("img_file_ext", [])
            
            # Get existing files from database
            existing_files = {f['filename']: f for f in self.get_by_imageset_id(imageset_id)}
            
            # Scan filesystem
            files_found = set()
            
            for file_name in os.listdir(imageset_folder_path):
                file_path = os.path.join(imageset_folder_path, file_name)
                
                # Skip directories
                if not os.path.isfile(file_path):
                    continue
                
                files_found.add(file_name)
                
                # Determine file type
                _, ext = os.path.splitext(file_name)
                ext_lower = ext.lower().lstrip('.')
                
                file_type = "other"
                if ext == ".toml":
                    file_type = "toml"
                elif ext == ".txt":
                    file_type = "text"
                elif "interview" in file_name:
                    file_type = "interview"
                elif ext_lower in img_file_ext:
                    file_type = "image"
                
                # Check if file exists in database
                if file_name in existing_files:
                    # Update if path changed
                    existing_file = existing_files[file_name]
                    if existing_file['fullpath'] != file_path:
                        self.update(
                            existing_file['id'],
                            fullpath=file_path,
                            file_type=file_type
                        )
                else:
                    # Create new record
                    self.create(
                        imageset_id=imageset_id,
                        filename=file_name,
                        fullpath=file_path,
                        extension=ext,
                        file_type=file_type
                    )
            
            # Delete files that no longer exist
            for filename, file_record in existing_files.items():
                if filename not in files_found:
                    self.delete(file_record['id'])
            
            logging.info(f"Synced {len(files_found)} files for imageset {imageset_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to sync filesystem for imageset {imageset_id}: {e}", exc_info=True)
            return False

