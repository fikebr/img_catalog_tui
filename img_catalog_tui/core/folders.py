from pathlib import Path
import logging

from img_catalog_tui.config import Config


class Folders:
    """
    Folder registry (DB-first).

    - **DB is authoritative** for reads/writes.
    - `img_catalog_tui/db/folders.toml` is **derived** and is exported after DB writes.
    - Manual TOML changes are imported only via explicit sync functions/commands.
    """

    def __init__(self, config: Config):
        self.config = config
        self.folders_toml_file = self._folders_toml_file()
        self.folders = self._load_from_db()
        
    def _folders_toml_file(self) -> Path:
        """Get the absolute path to the folders.toml file."""
        # Get the directory where this file is located
        current_dir = Path(__file__).parent
        # Navigate to the db directory and get the folders.toml file
        file = current_dir.parent / "db" / "folders.toml"
        absolute_path = file.resolve()  # Convert to absolute path
        
        # Validate that the file exists
        if not absolute_path.exists():
            raise FileNotFoundError(f"folders.toml file not found at: {absolute_path}")
        
        return absolute_path

    def _load_from_db(self) -> dict[str, str]:
        """Load folder registry from the database."""
        try:
            from img_catalog_tui.db.utils import init_database
            from img_catalog_tui.db.folders import FoldersTable

            init_database(self.config)
            folders_table = FoldersTable(self.config)
            folders = folders_table.get_all_dict()
            logging.debug("Loaded %s folders from database", len(folders))
            return folders
        except Exception as e:
            logging.error(f"Failed to load folders from database: {e}", exc_info=True)
            return {}

    def export_to_toml(self) -> bool:
        """Export folders from DB -> `folders.toml`."""
        try:
            from img_catalog_tui.db.sync import sync_folders_db_to_toml

            ok = sync_folders_db_to_toml(self.config)
            if not ok:
                logging.warning("folders DB->TOML export failed")
            return ok
        except Exception as e:
            logging.error(f"Failed to export folders to TOML: {e}", exc_info=True)
            return False

    def import_from_toml(self) -> bool:
        """Import folders from `folders.toml` -> DB (manual, explicit)."""
        try:
            from img_catalog_tui.db.sync import sync_folders_toml_to_db

            ok = sync_folders_toml_to_db(self.config)
            if ok:
                self.folders = self._load_from_db()
            return ok
        except Exception as e:
            logging.error(f"Failed to import folders from TOML: {e}", exc_info=True)
            return False
    
    def add(self, folder_full_path: str) -> bool:
        """Add a folder to the collection (DB-first) and export TOML."""
        try:
            from img_catalog_tui.db.folders import FoldersTable

            folder_path = Path(folder_full_path)
            folder_name = folder_path.name

            if not folder_path.exists():
                logging.error(f"Folder does not exist: {folder_full_path}")
                return False
            if not folder_path.is_dir():
                logging.error(f"Path is not a directory: {folder_full_path}")
                return False

            absolute_path = str(folder_path.resolve())

            folders_table = FoldersTable(self.config)
            existing = folders_table.get_by_name(folder_name)
            if existing:
                logging.warning(f"Folder '{folder_name}' already exists in DB")
                return False

            folder_id = folders_table.create(folder_name, absolute_path)
            if not folder_id:
                logging.error(f"Failed to create folder in DB: {folder_name}")
                return False

            self.folders = self._load_from_db()
            self.export_to_toml()
            logging.info(f"Added folder '{folder_name}' to DB (id={folder_id})")
            return True
        except Exception as e:
            logging.error(f"Error adding folder '{folder_full_path}': {e}", exc_info=True)
            return False
    
    def delete(self, folder_name: str) -> bool:
        """Remove a folder from the collection (DB-first) and export TOML."""
        try:
            from img_catalog_tui.db.folders import FoldersTable

            folders_table = FoldersTable(self.config)
            existing = folders_table.get_by_name(folder_name)
            if not existing:
                logging.warning(f"Folder '{folder_name}' not found in DB")
                return False

            ok = folders_table.delete(existing["id"])
            if not ok:
                logging.error(f"Failed to delete folder '{folder_name}' from DB")
                return False

            self.folders = self._load_from_db()
            self.export_to_toml()
            logging.info(f"Deleted folder '{folder_name}' from DB")
            return True
        except Exception as e:
            logging.error(f"Error deleting folder '{folder_name}': {e}", exc_info=True)
            return False
        
        
    