"""
File utility functions for the Image Catalog TUI application.
"""

import logging
import os
import shutil
from typing import List, Optional, Tuple


def parse_file_parts(file_path: str) -> Tuple[str, str]:
    """
    Parse a file path into base name and extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple containing (base_name, extension)
    """
    file_name = os.path.basename(file_path)
    base_name, ext = os.path.splitext(file_name)
    return base_name, ext


def is_image_file(file_path: str) -> bool:
    """
    Check if a file is an image based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is an image, False otherwise
    """
    _, ext = parse_file_parts(file_path)
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    return ext.lower() in image_extensions


def create_folder(folder_path: str) -> bool:
    """
    Create a folder if it doesn't exist.
    
    Args:
        folder_path: Path to the folder to create
        
    Returns:
        True if the folder was created or already exists, False otherwise
    """
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            logging.info(f"Created folder: {folder_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating folder {folder_path}: {e}", exc_info=True)
        return False


def move_files(pattern: str, source_folder: str, dest_folder: str) -> List[str]:
    """
    Move files matching a pattern from source to destination folder.
    
    Args:
        pattern: Pattern to match in filenames
        source_folder: Source folder path
        dest_folder: Destination folder path
        
    Returns:
        List of moved file paths
    """
    moved_files = []
    
    try:
        # Create destination folder if it doesn't exist
        if not create_folder(dest_folder):
            return moved_files
            
        # Get files matching pattern
        for file_name in os.listdir(source_folder):
            file_path = os.path.join(source_folder, file_name)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            # Check if file matches pattern
            if pattern in file_name:
                dest_path = os.path.join(dest_folder, file_name)
                shutil.move(file_path, dest_path)
                moved_files.append(dest_path)
                logging.info(f"Moved file: {file_path} -> {dest_path}")
                
        return moved_files
        
    except Exception as e:
        logging.error(f"Error moving files: {e}", exc_info=True)
        return moved_files


def get_imageset_from_filename(file_name: str, file_tags: List[str]) -> Tuple[str, str, List[str]]:
    """
    Extract imageset name and tags from a filename.
    
    Args:
        file_name: Name of the file
        file_tags: List of recognized file tags
        
    Returns:
        Tuple containing (imageset_name, extension, tags)
    """
    base_name, ext = parse_file_parts(file_name)
    found_tags = []
    
    # Check for tags in the filename
    for tag in file_tags:
        tag_pattern = f"_{tag}"
        if tag_pattern in base_name:
            found_tags.append(tag)
            # Remove tag from base name
            base_name = base_name.replace(tag_pattern, "")
    
    return base_name, ext, found_tags


def delete_folder(folder_path: str) -> bool:
    """
    Delete a folder and all its contents.
    
    Args:
        folder_path: Path to the folder to delete
        
    Returns:
        True if the folder was deleted, False otherwise
    """
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            logging.info(f"Deleted folder: {folder_path}")
            return True
        return False
    except Exception as e:
        logging.error(f"Error deleting folder {folder_path}: {e}", exc_info=True)
        return False


def find_file_with_tag(folder_path: str, tag: str) -> Optional[str]:
    """
    Find a file with a specific tag in a folder.
    
    Args:
        folder_path: Path to the folder to search in
        tag: Tag to search for
        
    Returns:
        Path to the file if found, None otherwise
    """
    try:
        tag_pattern = f"_{tag}"
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path) and tag_pattern in file_name:
                return file_path
        return None
    except Exception as e:
        logging.error(f"Error finding file with tag {tag} in {folder_path}: {e}", exc_info=True)
        return None
