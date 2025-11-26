
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
            config: Optional Config object (unused, kept for backward compatibility)
        """
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
                return True
            else:
                # Rollback on TOML update failure
                self.folders[folder_name] = removed_path
                logging.error(f"Failed to update TOML file, rolled back deletion of '{folder_name}'")
                return False
                
        except Exception as e:
            logging.error(f"Error deleting folder '{folder_name}': {e}", exc_info=True)
            return False
        
        
    