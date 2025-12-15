"""
Folder utility functions for the Image Catalog TUI application.
"""

import logging


def get_folder_path(foldername: str) -> str | None:
    """
    Get folder path for a foldername (DB-first).

    DB is authoritative. This helper avoids loading the full `Folders` manager.
    
    Args:
        foldername: Name of the folder to look up
        
    Returns:
        Full path to the folder if found, None otherwise
    """
    try:
        from img_catalog_tui.config import Config
        from img_catalog_tui.db.utils import init_database
        from img_catalog_tui.db.folders import FoldersTable

        config = Config()
        init_database(config)
        folders_table = FoldersTable(config)
        row = folders_table.get_by_name(foldername)
        return row["path"] if row else None
    except Exception as e:
        logging.error(f"Error looking up folder '{foldername}' in database: {e}", exc_info=True)
        return None
