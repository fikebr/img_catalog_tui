
from pathlib import Path
import toml


class Folders:
    
    def __init__(self):
        self.folders_toml_file = self._folders_toml_file()
        self.toml = self._parse_toml()
        self.folders = self.toml["folders"]
        
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
        
    