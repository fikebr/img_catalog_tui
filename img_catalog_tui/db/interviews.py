"""
CRUD operations for the interviews table.
"""

import json
import logging
from typing import Optional, Dict, List
from datetime import datetime

from img_catalog_tui.config import Config
from img_catalog_tui.db.utils import get_connection


class InterviewsTable:
    """CRUD operations for interviews table."""
    
    def __init__(self, config: Config):
        """
        Initialize InterviewsTable.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def create(
        self,
        imageset_id: int,
        interview_template: str,
        image_file_path: str,
        interview_response: Optional[str] = None,
        interview_raw: Optional[Dict] = None,
        interview_parsed: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Create a new interview record.
        
        Args:
            imageset_id: Foreign key to imagesets.id
            interview_template: Template name used
            image_file_path: Full path to image file used
            interview_response: Full text response
            interview_raw: Raw JSON response (will be serialized)
            interview_parsed: Parsed JSON results (will be serialized)
            
        Returns:
            int: ID of created interview, or None if failed
        """
        try:
            interview_raw_json = json.dumps(interview_raw) if interview_raw else None
            interview_parsed_json = json.dumps(interview_parsed) if interview_parsed else None
            
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO interviews (
                        imageset_id, interview_template, image_file_path,
                        interview_response, interview_raw, interview_parsed, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    imageset_id, interview_template, image_file_path,
                    interview_response, interview_raw_json, interview_parsed_json,
                    datetime.now().isoformat()
                ))
                interview_id = cursor.lastrowid
                logging.debug(f"Created interview for imageset {imageset_id} (id: {interview_id})")
                return interview_id
        except Exception as e:
            logging.error(f"Failed to create interview for imageset {imageset_id}: {e}", exc_info=True)
            return None
    
    def get_by_id(self, interview_id: int) -> Optional[Dict]:
        """
        Get interview by ID.
        
        Args:
            interview_id: Interview ID
            
        Returns:
            dict: Interview record with parsed JSON fields, or None if not found
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    if result['interview_raw']:
                        result['interview_raw'] = json.loads(result['interview_raw'])
                    if result['interview_parsed']:
                        result['interview_parsed'] = json.loads(result['interview_parsed'])
                    return result
                return None
        except Exception as e:
            logging.error(f"Failed to get interview by id {interview_id}: {e}", exc_info=True)
            return None
    
    def get_by_imageset_id(self, imageset_id: int) -> List[Dict]:
        """
        Get all interviews for an imageset.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            list: List of interview records with parsed JSON fields
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM interviews WHERE imageset_id = ? ORDER BY created_at DESC",
                    (imageset_id,)
                )
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    if result['interview_raw']:
                        result['interview_raw'] = json.loads(result['interview_raw'])
                    if result['interview_parsed']:
                        result['interview_parsed'] = json.loads(result['interview_parsed'])
                    results.append(result)
                return results
        except Exception as e:
            logging.error(f"Failed to get interviews for imageset {imageset_id}: {e}", exc_info=True)
            return []
    
    def get_latest_by_imageset_id(self, imageset_id: int) -> Optional[Dict]:
        """
        Get the latest interview for an imageset.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            dict: Latest interview record with parsed JSON fields, or None if not found
        """
        interviews = self.get_by_imageset_id(imageset_id)
        return interviews[0] if interviews else None
    
    def get_by_template(self, interview_template: str) -> List[Dict]:
        """
        Get all interviews using a specific template.
        
        Args:
            interview_template: Template name
            
        Returns:
            list: List of interview records with parsed JSON fields
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM interviews WHERE interview_template = ? ORDER BY created_at DESC",
                    (interview_template,)
                )
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    if result['interview_raw']:
                        result['interview_raw'] = json.loads(result['interview_raw'])
                    if result['interview_parsed']:
                        result['interview_parsed'] = json.loads(result['interview_parsed'])
                    results.append(result)
                return results
        except Exception as e:
            logging.error(f"Failed to get interviews by template '{interview_template}': {e}", exc_info=True)
            return []
    
    def update(
        self,
        interview_id: int,
        interview_response: Optional[str] = None,
        interview_raw: Optional[Dict] = None,
        interview_parsed: Optional[Dict] = None
    ) -> bool:
        """
        Update interview record.
        
        Args:
            interview_id: Interview ID
            interview_response: Full text response
            interview_raw: Raw JSON response (will be serialized)
            interview_parsed: Parsed JSON results (will be serialized)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if interview_response is not None:
                updates.append("interview_response = ?")
                params.append(interview_response)
            
            if interview_raw is not None:
                updates.append("interview_raw = ?")
                params.append(json.dumps(interview_raw))
            
            if interview_parsed is not None:
                updates.append("interview_parsed = ?")
                params.append(json.dumps(interview_parsed))
            
            if not updates:
                return True
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(interview_id)
            
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE interviews SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                logging.debug(f"Updated interview id {interview_id}")
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Failed to update interview id {interview_id}: {e}", exc_info=True)
            return False
    
    def delete(self, interview_id: int) -> bool:
        """
        Delete interview record.
        
        Args:
            interview_id: Interview ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM interviews WHERE id = ?", (interview_id,))
                deleted = cursor.rowcount > 0
                if deleted:
                    logging.debug(f"Deleted interview id {interview_id}")
                return deleted
        except Exception as e:
            logging.error(f"Failed to delete interview id {interview_id}: {e}", exc_info=True)
            return False
    
    def delete_by_imageset_id(self, imageset_id: int) -> bool:
        """
        Delete all interviews for an imageset.
        
        Args:
            imageset_id: Imageset ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM interviews WHERE imageset_id = ?", (imageset_id,))
                logging.debug(f"Deleted all interviews for imageset {imageset_id}")
                return True
        except Exception as e:
            logging.error(f"Failed to delete interviews for imageset {imageset_id}: {e}", exc_info=True)
            return False

