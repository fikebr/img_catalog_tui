
from pathlib import Path
import toml
import logging

from img_catalog_tui.config import Config


class Folders:
    
    def __init__(self, config: Config | None = None):
        """
        Initialize Folders manager.
        
        Uses TOML files for storage. Database synchronization is handled separately
        via the sync module.
        
        Args:
            config: Optional Config object for database operations
        """
        self.config = config
        self.folders_toml_file = self._folders_toml_file()
        self.toml = self._parse_toml()
        self.folders: dict[str, str] = self.toml["folders"]
        
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
    
    def _parse_toml(self) -> dict:
        """Parse the folders.toml file and return its contents as a dictionary."""
        try:
            with open(self.folders_toml_file, 'r', encoding='utf-8') as file:
                return toml.load(file)
        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML format in {self.folders_toml_file}: {e}")
        except Exception as e:
            raise IOError(f"Error reading {self.folders_toml_file}: {e}")
        
    def _update_toml(self) -> bool:
        """Update the TOML file with current folders data."""
        try:
            # Update the toml dict with current folders
            self.toml["folders"] = self.folders
            
            # Write to file
            with open(self.folders_toml_file, 'w', encoding='utf-8') as file:
                toml.dump(self.toml, file)
            
            logging.info(f"Successfully updated TOML file: {self.folders_toml_file}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update TOML file {self.folders_toml_file}: {e}")
            return False
    
    def _sync_folder_to_db(self, folder_name: str, folder_path: str) -> None:
        """Sync folder addition/update to the database.
        
        This method attempts to sync folder changes to the database.
        Errors are logged but don't interrupt execution (graceful degradation).
        
        Args:
            folder_name: The folder name (basename)
            folder_path: The full folder path
        """
        try:
            # Skip sync if no config provided
            if not self.config:
                logging.debug("Database sync skipped: no config provided to Folders")
                return
            
            from img_catalog_tui.db.folders import FoldersTable
            
            folders_table = FoldersTable(self.config)
            existing = folders_table.get_by_name(folder_name)
            
            if existing:
                # Update if path changed
                if existing['path'] != folder_path:
                    folders_table.update(existing['id'], path=folder_path)
                    logging.debug(f"Updated folder in database: {folder_name}")
                else:
                    logging.debug(f"Folder already up to date in database: {folder_name}")
            else:
                # Create new
                folder_id = folders_table.create(folder_name, folder_path)
                if folder_id:
                    logging.debug(f"Created folder in database: {folder_name} (ID: {folder_id})")
                else:
                    logging.warning(f"Database sync returned no ID for folder '{folder_name}'")
                    
        except ImportError:
            # Database module not available, skip sync
            logging.debug("Database sync skipped: db.folders module not available")
        except Exception as e:
            # Log error but continue - graceful degradation
            logging.warning(f"Failed to sync folder '{folder_name}' to database: {e}")
    
    def _sync_folder_deletion_to_db(self, folder_name: str) -> None:
        """Sync folder deletion to the database.
        
        This method attempts to delete folder from the database.
        Errors are logged but don't interrupt execution (graceful degradation).
        
        Args:
            folder_name: The folder name to delete
        """
        try:
            # Skip sync if no config provided
            if not self.config:
                logging.debug("Database sync skipped: no config provided to Folders")
                return
            
            from img_catalog_tui.db.folders import FoldersTable
            
            folders_table = FoldersTable(self.config)
            existing = folders_table.get_by_name(folder_name)
            
            if existing:
                success = folders_table.delete(existing['id'])
                if success:
                    logging.debug(f"Deleted folder from database: {folder_name}")
                else:
                    logging.warning(f"Failed to delete folder from database: {folder_name}")
            else:
                logging.debug(f"Folder not found in database (already deleted?): {folder_name}")
                    
        except ImportError:
            # Database module not available, skip sync
            logging.debug("Database sync skipped: db.folders module not available")
        except Exception as e:
            # Log error but continue - graceful degradation
            logging.warning(f"Failed to delete folder '{folder_name}' from database: {e}")
    
    def add(self, folder_full_path: str) -> bool:
        """Add a folder to the collection if it exists and is not already present."""
        try:
            # Get the basename from the full path to use as the key
            folder_path = Path(folder_full_path)
            folder_name = folder_path.name
            
            # Check if folder is already in the list
            if folder_name in self.folders:
                logging.warning(f"Folder '{folder_name}' is already in the list")
                return False
            
            # Check if the folder exists on the filesystem
            if not folder_path.exists():
                logging.error(f"Folder does not exist: {folder_full_path}")
                return False
            
            if not folder_path.is_dir():
                logging.error(f"Path is not a directory: {folder_full_path}")
                return False
            
            # Add folder to the collection using absolute path
            absolute_path = str(folder_path.resolve())
            self.folders[folder_name] = absolute_path
            
            if self._update_toml():
                logging.info(f"Successfully added folder '{folder_name}': {absolute_path}")
                
                # Sync to database
                self._sync_folder_to_db(folder_name, absolute_path)
                
                return True
            else:
                # Rollback on TOML update failure
                del self.folders[folder_name]
                logging.error(f"Failed to update TOML file, rolled back addition of '{folder_name}'")
                return False
                
        except Exception as e:
            logging.error(f"Error adding folder '{folder_full_path}': {e}", exc_info=True)
            return False
    
    def delete(self, folder_name: str) -> bool:
        """Remove a folder from the collection."""
        try:
            # Check if folder exists in the collection
            if folder_name not in self.folders:
                logging.warning(f"Folder '{folder_name}' not found in collection")
                return False
            
            removed_path = self.folders[folder_name]
            del self.folders[folder_name]
            
            if self._update_toml():
                logging.info(f"Successfully removed folder '{folder_name}' from collection")
                
                # Sync deletion to database
                self._sync_folder_deletion_to_db(folder_name)
                
                return True
            else:
                # Rollback on TOML update failure
                self.folders[folder_name] = removed_path
                logging.error(f"Failed to update TOML file, rolled back deletion of '{folder_name}'")
                return False
                
        except Exception as e:
            logging.error(f"Error deleting folder '{folder_name}': {e}", exc_info=True)
            return False
        
        
    