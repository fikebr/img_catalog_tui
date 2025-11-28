"""
Database package for Image Catalog TUI.

This package provides database access layers for SQLite storage,
including CRUD operations for all tables and synchronization utilities.
"""

# Lazy imports to avoid RuntimeWarning when running utils as a module
# Import only when accessed, not at package level

__all__ = [
    'get_db_path',
    'init_database',
    'get_connection',
    'close_connection',
    'FoldersTable',
    'ImagesetsTable',
    'ImagesetSectionsTable',
    'InterviewsTable',
    'ImagesetFilesTable',
    'ImagesetFileTagsTable',
]


def __getattr__(name):
    """Lazy import module attributes."""
    if name == 'get_db_path':
        from img_catalog_tui.db.utils import get_db_path
        return get_db_path
    elif name == 'init_database':
        from img_catalog_tui.db.utils import init_database
        return init_database
    elif name == 'get_connection':
        from img_catalog_tui.db.utils import get_connection
        return get_connection
    elif name == 'close_connection':
        from img_catalog_tui.db.utils import close_connection
        return close_connection
    elif name == 'FoldersTable':
        from img_catalog_tui.db.folders import FoldersTable
        return FoldersTable
    elif name == 'ImagesetsTable':
        from img_catalog_tui.db.imagesets import ImagesetsTable
        return ImagesetsTable
    elif name == 'ImagesetSectionsTable':
        from img_catalog_tui.db.imageset_sections import ImagesetSectionsTable
        return ImagesetSectionsTable
    elif name == 'InterviewsTable':
        from img_catalog_tui.db.interviews import InterviewsTable
        return InterviewsTable
    elif name == 'ImagesetFilesTable':
        from img_catalog_tui.db.imagesetfiles import ImagesetFilesTable
        return ImagesetFilesTable
    elif name == 'ImagesetFileTagsTable':
        from img_catalog_tui.db.imagesetfile_tags import ImagesetFileTagsTable
        return ImagesetFileTagsTable
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

