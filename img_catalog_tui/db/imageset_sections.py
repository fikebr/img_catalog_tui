"""
CRUD operations for the imageset_sections table.
"""

import json
import logging
from typing import Optional, Dict, List
from datetime import datetime

from img_catalog_tui.config import Config
from img_catalog_tui.db.utils import get_connection


class ImagesetSectionsTable:
    """CRUD operations for imageset_sections table."""
    
    def __init__(self, config: Config):
        """
        Initialize ImagesetSectionsTable.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def create(self, imageset_id: int, section_name: str, section_data: Dict) -> Optional[int]:
        """
        Create a new imageset section record.
        
        Args:
            imageset_id: Foreign key to imagesets.id
            section_name: Section name (e.g., "biz", "midjourney", "fooocus")
            section_data: Dictionary of key-value pairs for the section
            
        Returns:
            int: ID of created section, or None if failed
        """
        try:
            section_data_json = json.dumps(section_data) if section_data else None
            
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO imageset_sections (
                        imageset_id, section_name, section_data, updated_at
                    )
                    VALUES (?, ?, ?, ?)
                """, (imageset_id, section_name, section_data_json, datetime.now().isoformat()))
                section_id = cursor.lastrowid
                logging.debug(f"Created section '{section_name}' for imageset {imageset_id}")
                return section_id
        except Exception as e:
            logging.error(f"Failed to create section '{section_name}' for imageset {imageset_id}: {e}", exc_info=True)
            return None
    
    def get_by_id(self, section_id: int) -> Optional[Dict]:
        """
        Get section by ID.
        
        Args:
            section_id: Section ID
            
        Returns:
            dict: Section record with parsed JSON data, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM imageset_sections WHERE id = ?", (section_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    if result['section_data']:
                        result['section_data'] = json.loads(result['section_data'])
                    return result
                return None
        except Exception as e:
            logging.error(f"Failed to get section by id {section_id}: {e}", exc_info=True)
            return None
    
    def get_by_imageset_and_section(self, imageset_id: int, section_name: str) -> Optional[Dict]:
        """
        Get section by imageset ID and section name.
        
        Args:
            imageset_id: Imageset ID
            section_name: Section name
            
        Returns:
            dict: Section record with parsed JSON data, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imageset_sections WHERE imageset_id = ? AND section_name = ?",
                    (imageset_id, section_name)
                )
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    if result['section_data']:
                        result['section_data'] = json.loads(result['section_data'])
                    return result
                return None
        except Exception as e:
            logging.error(f"Failed to get section '{section_name}' for imageset {imageset_id}: {e}", exc_info=True)
            return None
    
    def get_by_imageset_id(self, imageset_id: int) -> List[Dict]:
        """
        Get all sections for an imageset.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            list: List of section records with parsed JSON data
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM imageset_sections WHERE imageset_id = ? ORDER BY section_name",
                    (imageset_id,)
                )
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    if result['section_data']:
                        result['section_data'] = json.loads(result['section_data'])
                    results.append(result)
                return results
        except Exception as e:
            logging.error(f"Failed to get sections for imageset {imageset_id}: {e}", exc_info=True)
            return []
    
    def get_section_dict(self, imageset_id: int, section_name: str) -> Optional[Dict]:
        """
        Get section data as a dictionary (convenience method).
        
        Args:
            imageset_id: Imageset ID
            section_name: Section name
            
        Returns:
            dict: Section data dictionary, or None if not found
        """
        section = self.get_by_imageset_and_section(imageset_id, section_name)
        return section['section_data'] if section else None
    
    def get_field(self, imageset_id: int, section_name: str, field_name: str) -> Optional[str]:
        """
        Get a specific field from a section.
        
        Args:
            imageset_id: Imageset ID
            section_name: Section name
            field_name: Field name within the section
            
        Returns:
            str: Field value, or None if not found
        """
        section_data = self.get_section_dict(imageset_id, section_name)
        if section_data and isinstance(section_data, dict):
            return section_data.get(field_name)
        return None
    
    def update(self, imageset_id: int, section_name: str, section_data: Dict) -> bool:
        """
        Update or create a section.
        
        Args:
            imageset_id: Imageset ID
            section_name: Section name
            section_data: Dictionary of key-value pairs for the section
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            section_data_json = json.dumps(section_data) if section_data else None
            
            # Check if section exists
            existing = self.get_by_imageset_and_section(imageset_id, section_name)
            
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                if existing:
                    # Update existing
                    cursor.execute("""
                        UPDATE imageset_sections
                        SET section_data = ?, updated_at = ?
                        WHERE imageset_id = ? AND section_name = ?
                    """, (section_data_json, datetime.now().isoformat(), imageset_id, section_name))
                else:
                    # Create new
                    cursor.execute("""
                        INSERT INTO imageset_sections (
                            imageset_id, section_name, section_data, updated_at
                        )
                        VALUES (?, ?, ?, ?)
                    """, (imageset_id, section_name, section_data_json, datetime.now().isoformat()))
                
                logging.debug(f"Updated section '{section_name}' for imageset {imageset_id}")
                return True
        except Exception as e:
            logging.error(f"Failed to update section '{section_name}' for imageset {imageset_id}: {e}", exc_info=True)
            return False
    
    def set_field(self, imageset_id: int, section_name: str, field_name: str, value: str) -> bool:
        """
        Set a specific field in a section.
        
        Args:
            imageset_id: Imageset ID
            section_name: Section name
            field_name: Field name within the section
            value: Field value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get existing section data
            section = self.get_by_imageset_and_section(imageset_id, section_name)
            if section:
                section_data = section['section_data'] or {}
            else:
                section_data = {}
            
            # Update the field
            section_data[field_name] = value
            
            # Save back
            return self.update(imageset_id, section_name, section_data)
        except Exception as e:
            logging.error(f"Failed to set field '{field_name}' in section '{section_name}' for imageset {imageset_id}: {e}", exc_info=True)
            return False
    
    def delete(self, imageset_id: int, section_name: str) -> bool:
        """
        Delete a section.
        
        Args:
            imageset_id: Imageset ID
            section_name: Section name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM imageset_sections WHERE imageset_id = ? AND section_name = ?",
                    (imageset_id, section_name)
                )
                deleted = cursor.rowcount > 0
                if deleted:
                    logging.debug(f"Deleted section '{section_name}' for imageset {imageset_id}")
                return deleted
        except Exception as e:
            logging.error(f"Failed to delete section '{section_name}' for imageset {imageset_id}: {e}", exc_info=True)
            return False
    
    def delete_by_imageset_id(self, imageset_id: int) -> bool:
        """
        Delete all sections for an imageset.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM imageset_sections WHERE imageset_id = ?", (imageset_id,))
                logging.debug(f"Deleted all sections for imageset {imageset_id}")
                return True
        except Exception as e:
            logging.error(f"Failed to delete sections for imageset {imageset_id}: {e}", exc_info=True)
            return False

