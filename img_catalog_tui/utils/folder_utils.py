"""
Folder utility functions for the Image Catalog TUI application.
"""

import logging
import toml
from pathlib import Path
from typing import Optional


def get_folder_path(foldername: str) -> Optional[str]:
    """
    Get folder path for a foldername without loading full Folders object.
    
    Args:
        foldername: Name of the folder to look up
        
    Returns:
        Full path to the folder if found, None otherwise
    """
    try:
        # Get path to folders.toml file
        current_dir = Path(__file__).parent
        folders_toml_path = current_dir.parent / "db" / "folders.toml"
        
        # Read and parse TOML file
        with open(folders_toml_path, 'r', encoding='utf-8') as file:
            toml_data = toml.load(file)
        
        # Return the folder path if found
        return toml_data.get("folders", {}).get(foldername)
        
    except Exception as e:
        logging.error(f"Error reading folders.toml for foldername '{foldername}': {e}")
        return None
