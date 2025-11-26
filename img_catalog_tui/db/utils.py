"""
Database utility functions for SQLite database initialization and connection management.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from img_catalog_tui.config import Config


def get_db_path(config: Config) -> str:
    """
    Get the database path from config.
    
    Args:
        config: Configuration object
        
    Returns:
        str: Full path to database file
    """
    db_path = config.config_data.get("storage", {}).get("db_path", "img_catalog_tui/db/catalog.db")
    
    # Convert to absolute path if relative
    if not os.path.isabs(db_path):
        # Get project root (assuming this file is in img_catalog_tui/db/)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        db_path = str(project_root / db_path)
    
    return db_path


def init_database(config: Config) -> bool:
    """
    Initialize the SQLite database with all tables and indexes.
    
    Args:
        config: Configuration object
        
    Returns:
        bool: True if successful, False otherwise
    """
    db_path = get_db_path(config)
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Create tables
        _create_folders_table(cursor)
        _create_imagesets_table(cursor)
        _create_imageset_sections_table(cursor)
        _create_interviews_table(cursor)
        _create_imagesetfiles_table(cursor)
        _create_imagesetfile_tags_table(cursor)
        
        # Create indexes
        _create_indexes(cursor)
        
        conn.commit()
        conn.close()
        
        logging.info(f"Database initialized successfully at: {db_path}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}", exc_info=True)
        return False


def _create_folders_table(cursor: sqlite3.Cursor) -> None:
    """Create the folders table."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _create_imagesets_table(cursor: sqlite3.Cursor) -> None:
    """Create the imagesets table."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imagesets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            folder_path TEXT NOT NULL,
            imageset_folder_path TEXT NOT NULL,
            status TEXT,
            edits TEXT,
            needs TEXT,
            good_for TEXT,
            source TEXT,
            prompt TEXT,
            cover_image_path TEXT,
            orig_image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
        )
    """)


def _create_imageset_sections_table(cursor: sqlite3.Cursor) -> None:
    """Create the imageset_sections table."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imageset_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imageset_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            section_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (imageset_id) REFERENCES imagesets(id) ON DELETE CASCADE,
            UNIQUE(imageset_id, section_name)
        )
    """)


def _create_interviews_table(cursor: sqlite3.Cursor) -> None:
    """Create the interviews table."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imageset_id INTEGER NOT NULL,
            interview_template TEXT NOT NULL,
            image_file_path TEXT NOT NULL,
            interview_response TEXT,
            interview_raw TEXT,
            interview_parsed TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (imageset_id) REFERENCES imagesets(id) ON DELETE CASCADE
        )
    """)


def _create_imagesetfiles_table(cursor: sqlite3.Cursor) -> None:
    """Create the imagesetfiles table."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imagesetfiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imageset_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            fullpath TEXT NOT NULL,
            extension TEXT,
            file_type TEXT,
            file_size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (imageset_id) REFERENCES imagesets(id) ON DELETE CASCADE,
            UNIQUE(imageset_id, filename)
        )
    """)


def _create_imagesetfile_tags_table(cursor: sqlite3.Cursor) -> None:
    """Create the imagesetfile_tags table."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imagesetfile_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imagesetfile_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (imagesetfile_id) REFERENCES imagesetfiles(id) ON DELETE CASCADE,
            UNIQUE(imagesetfile_id, tag)
        )
    """)


def _create_indexes(cursor: sqlite3.Cursor) -> None:
    """Create all indexes."""
    indexes = [
        # Folders indexes
        "CREATE INDEX IF NOT EXISTS idx_folders_name ON folders(name)",
        "CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path)",
        
        # Imagesets indexes
        "CREATE INDEX IF NOT EXISTS idx_imagesets_folder_id ON imagesets(folder_id)",
        "CREATE INDEX IF NOT EXISTS idx_imagesets_name ON imagesets(name)",
        "CREATE INDEX IF NOT EXISTS idx_imagesets_status ON imagesets(status)",
        "CREATE INDEX IF NOT EXISTS idx_imagesets_source ON imagesets(source)",
        "CREATE INDEX IF NOT EXISTS idx_imagesets_folder_name ON imagesets(folder_id, name)",
        
        # Imageset sections indexes
        "CREATE INDEX IF NOT EXISTS idx_imageset_sections_imageset_id ON imageset_sections(imageset_id)",
        "CREATE INDEX IF NOT EXISTS idx_imageset_sections_name ON imageset_sections(section_name)",
        
        # Interviews indexes
        "CREATE INDEX IF NOT EXISTS idx_interviews_imageset_id ON interviews(imageset_id)",
        "CREATE INDEX IF NOT EXISTS idx_interviews_template ON interviews(interview_template)",
        "CREATE INDEX IF NOT EXISTS idx_interviews_created_at ON interviews(created_at)",
        
        # Imagesetfiles indexes
        "CREATE INDEX IF NOT EXISTS idx_imagesetfiles_imageset_id ON imagesetfiles(imageset_id)",
        "CREATE INDEX IF NOT EXISTS idx_imagesetfiles_filename ON imagesetfiles(filename)",
        "CREATE INDEX IF NOT EXISTS idx_imagesetfiles_file_type ON imagesetfiles(file_type)",
        
        # Imagesetfile tags indexes
        "CREATE INDEX IF NOT EXISTS idx_imagesetfile_tags_file_id ON imagesetfile_tags(imagesetfile_id)",
        "CREATE INDEX IF NOT EXISTS idx_imagesetfile_tags_tag ON imagesetfile_tags(tag)",
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)


@contextmanager
def get_connection(config: Config):
    """
    Get a database connection with proper error handling.
    
    Usage:
        with get_connection(config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM folders")
    
    Args:
        config: Configuration object
        
    Yields:
        sqlite3.Connection: Database connection
    """
    db_path = get_db_path(config)
    conn = None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def close_connection(conn: Optional[sqlite3.Connection]) -> None:
    """
    Close a database connection.
    
    Args:
        conn: Database connection to close
    """
    if conn:
        try:
            conn.close()
        except Exception as e:
            logging.error(f"Error closing database connection: {e}", exc_info=True)


if __name__ == "__main__":
    """
    Entry point for running database initialization as a module.
    
    Usage:
        uv run -m img_catalog_tui.db.utils
    """
    import sys
    
    # Set up logging
    from img_catalog_tui.logger import setup_logging
    setup_logging()
    
    # Load configuration
    from img_catalog_tui.config import Config
    
    try:
        logging.info("Initializing database...")
        config = Config()
        success = init_database(config)
        
        if success:
            db_path = get_db_path(config)
            logging.info(f"Database initialized successfully at: {db_path}")
            print(f"✓ Database initialized successfully at: {db_path}")
            sys.exit(0)
        else:
            logging.error("Failed to initialize database")
            print("✗ Failed to initialize database. Check logs for details.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logging.error(f"Configuration file not found: {e}", exc_info=True)
        print(f"✗ Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error initializing database: {e}", exc_info=True)
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)

