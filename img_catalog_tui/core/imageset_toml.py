import os
import tomllib
import tomli_w
import logging

class ImagesetToml:
    
    def __init__(
        self,
        imageset_folder: str
        
    ):
        
        self.imageset_folder = self._validate_folder(imageset_folder)
        self.toml_file = self._set_toml_filename()
        self._data  = {}
        self._validate_toml_file()
        
    def _validate_folder(self, imageset_folder: str) -> str:
        """Validates that the imageset folder exists and is a directory."""
        if not os.path.exists(imageset_folder):
            raise FileNotFoundError(f"Imageset folder does not exist: {imageset_folder}")
        if not os.path.isdir(imageset_folder):
            raise NotADirectoryError(f"Path is not a directory: {imageset_folder}")
        return imageset_folder
    
    def _set_toml_filename(self) -> str:
        """Derives the TOML filename from the imageset folder path."""
        self.imageset_name = os.path.basename(self.imageset_folder)
        return os.path.join(self.imageset_folder, f"{self.imageset_name}.toml")
    
    def _validate_toml_file(self) -> bool:
        """Loads existing TOML file or creates a new one with default data."""
        try:
            if os.path.exists(self.toml_file):
                # Read existing TOML file
                with open(self.toml_file, 'rb') as f:
                    self._data = tomllib.load(f)
                logging.debug(f"Loaded existing TOML file: {self.toml_file}")
            else:
                # Create new TOML file with default data
                self._data = {"imageset": self.imageset_name}
                with open(self.toml_file, 'wb') as f:
                    tomli_w.dump(self._data, f)
                logging.info(f"Created new TOML file: {self.toml_file}")
            return True
        except Exception as e:
            logging.error(f"Error validating TOML file {self.toml_file}: {e}")
            raise
    
    def get(self, section: str="") -> dict:
        """Retrieves data from a specific section or returns all data."""
        try:
            if section:
                if section in self._data:
                    return self._data[section]
                else:
                    return {}
            else:
                return self._data
        except Exception as e:
            logging.error(f"Error getting section '{section}': {e}")
            raise
    
    def set(self, section: str="", key: str="", value="") -> bool:
        """Sets data in the TOML structure and saves the file."""
        try:
            # Scenario 1: section only, value must be dict
            if section and not key:
                if not isinstance(value, dict):
                    raise ValueError("When setting a section without a key, value must be a dict")
                self._data[section] = value
                
            # Scenario 2: section and key, value can be str, int, or bool
            elif section and key:
                if not isinstance(value, (str, int, bool)):
                    raise ValueError("When setting a section key, value must be str, int, or bool")
                if section not in self._data:
                    self._data[section] = {}
                if not isinstance(self._data[section], dict):
                    raise ValueError(f"Section '{section}' exists but is not a dict")
                self._data[section][key] = value
                
            # Scenario 3: no section, key and value at top level
            elif not section and key:
                self._data[key] = value
                
            else:
                raise ValueError("Invalid arguments: must provide either (section only with dict value), (section and key with any value), or (key and value only)")
            
            # Save the TOML file
            with open(self.toml_file, 'wb') as f:
                tomli_w.dump(self._data, f)
            logging.info(f"Updated TOML file: {self.toml_file}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting data in TOML file: {e}")
            raise
    
if __name__ == "__main__":
    
    imageset_folder = r"E:\fooocus\images\new\2025-08-05\2025-08-05_00-29-53_7332\test imageset"
    
    imageset_toml = ImagesetToml(imageset_folder=imageset_folder)
    
    data = {"key1": "value1", "key2": "value2"}
    
    
    imageset_toml.set(section="section1", value=data)
    imageset_toml.set(key="source", value="fooocus")
    
    print(imageset_toml.get())
    