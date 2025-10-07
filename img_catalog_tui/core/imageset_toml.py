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
        
    def _find_key_case_insensitive(self, data: dict, key: str) -> str | None:
        """Finds the actual key in a dict matching case-insensitively."""
        if not isinstance(key, str):
            return None
        lowered = key.lower()
        for existing_key in data.keys():
            if isinstance(existing_key, str) and existing_key.lower() == lowered:
                return existing_key
        return None
    
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
                # Read existing TOML file with encoding fallback
                try:
                    with open(self.toml_file, 'rb') as f:
                        self._data = tomllib.load(f)
                    logging.debug(f"Loaded existing TOML file: {self.toml_file}")
                    
                    # Ensure all required keys exist with default values
                    self._ensure_required_keys()
                    
                except UnicodeDecodeError as ude:
                    logging.warning(f"UTF-8 decode error in {self.toml_file}: {ude}")
                    # Try to read with different encodings
                    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                    content_loaded = False
                    
                    for encoding in encodings_to_try:
                        try:
                            with open(self.toml_file, 'r', encoding=encoding) as f:
                                content = f.read()
                            # Try to clean up problematic characters
                            content = content.replace('\x92', "'")  # Replace smart quote
                            content = content.replace('\x93', '"')  # Replace left double quote
                            content = content.replace('\x94', '"')  # Replace right double quote
                            
                            # Parse the cleaned content
                            self._data = tomllib.loads(content)
                            logging.info(f"Successfully loaded TOML file with {encoding} encoding after cleanup: {self.toml_file}")
                            
                            # Ensure all required keys exist with default values
                            self._ensure_required_keys()
                            
                            # Rewrite the file with proper UTF-8 encoding
                            with open(self.toml_file, 'wb') as f:
                                tomli_w.dump(self._data, f)
                            logging.info(f"Rewrote TOML file with proper UTF-8 encoding: {self.toml_file}")
                            content_loaded = True
                            break
                        except (UnicodeDecodeError, tomllib.TOMLDecodeError):
                            continue
                    
                    if not content_loaded:
                        logging.error(f"Could not read TOML file with any encoding: {self.toml_file}")
                        # Create backup and reinitialize
                        backup_file = f"{self.toml_file}.backup"
                        os.rename(self.toml_file, backup_file)
                        logging.info(f"Backed up corrupted file to: {backup_file}")
                        self._data = {
                            "imageset": self.imageset_name,
                            "status": "new",
                            "edits": "",
                            "needs": ""
                        }
                        with open(self.toml_file, 'wb') as f:
                            tomli_w.dump(self._data, f)
                        logging.info(f"Created new TOML file with default data: {self.toml_file}")
            else:
                # Create new TOML file with default data
                self._data = {
                    "imageset": self.imageset_name,
                    "status": "new",
                    "edits": "",
                    "needs": ""
                }
                
                with open(self.toml_file, 'wb') as f:
                    tomli_w.dump(self._data, f)
                logging.info(f"Created new TOML file: {self.toml_file}")
            return True
        except Exception as e:
            logging.error(f"Error validating TOML file {self.toml_file}: {e}")
            raise
    
    def _ensure_required_keys(self) -> None:
        """Ensures all required keys exist in the TOML data with default values."""
        try:
            default_values = {
                "imageset": self.imageset_name,
                "status": "new",
                "edits": "",
                "needs": ""
            }
            
            keys_added = []
            source_updated = False
            
            # Add missing default keys
            for key, default_value in default_values.items():
                if key not in self._data:
                    self._data[key] = default_value
                    keys_added.append(key)
            
            # Handle source detection based on sections
            if "source" not in self._data:
                self._data["source"] = "unknown"
                keys_added.append("source")
            
            # Auto-detect source from existing sections
            detected_source = self._detect_source_from_sections()
            if detected_source and self._data.get("source") == "unknown":
                self._data["source"] = detected_source
                source_updated = True
                logging.info(f"Auto-detected source as '{detected_source}' in: {self.toml_file}")
            
            # Save the file if any changes were made
            if keys_added or source_updated:
                self._save_toml_file()
                if keys_added:
                    logging.info(f"Added missing keys {keys_added} to TOML file: {self.toml_file}")
                    
        except Exception as e:
            logging.error(f"Error ensuring required keys in {self.toml_file}: {e}")
            raise
    
    def _detect_source_from_sections(self) -> str | None:
        """Detects the source type based on existing sections in the TOML data."""
        if "fooocus" in self._data:
            return "fooocus"
        elif "midjourney" in self._data:
            return "midjourney"
        return None
    
    def _save_toml_file(self) -> None:
        """Saves the TOML data to file with error handling."""
        try:
            with open(self.toml_file, 'wb') as f:
                tomli_w.dump(self._data, f)
        except Exception as e:
            logging.error(f"Failed to save TOML file {self.toml_file}: {e}")
            raise
    
    def get(self, section: str="", key: str="") -> dict | str:
        """Retrieves data from a specific section or returns all data."""
        try:
            # If section is null and key is provided, get top-level item
            if not section and key:
                actual_top_key = self._find_key_case_insensitive(self._data, key)
                if actual_top_key is not None:
                    return str(self._data[actual_top_key])
                else:
                    return ""
            
            # If both section and key are provided, get item from section
            elif section and key:
                actual_section = self._find_key_case_insensitive(self._data, section)
                if actual_section is None:
                    return ""
                section_data = self._data[actual_section]
                if not isinstance(section_data, dict):
                    return ""
                actual_key = self._find_key_case_insensitive(section_data, key)
                if actual_key is None:
                    return ""
                return str(section_data[actual_key])
            
            # If only section is provided, return section data
            elif section:
                actual_section = self._find_key_case_insensitive(self._data, section)
                if actual_section is not None:
                    return self._data[actual_section]
                return {}
            
            # If neither section nor key provided, return all data
            else:
                return self._data
        except Exception as e:
            logging.error(f"Error getting section '{section}', key '{key}': {e}")
            raise
    
    def set(self, section: str="", key: str="", value="") -> bool:
        """Sets data in the TOML structure and saves the file."""
        try:
            # Scenario 1: section only, value must be dict
            if section and not key:
                if not isinstance(value, dict):
                    raise ValueError("When setting a section without a key, value must be a dict")
                existing_section = self._find_key_case_insensitive(self._data, section)
                target_section_key = existing_section if existing_section is not None else section
                self._data[target_section_key] = value
                
            # Scenario 2: section and key, value can be str, int, or bool
            elif section and key:
                if not isinstance(value, (str, int, bool)):
                    raise ValueError("When setting a section key, value must be str, int, or bool")
                existing_section = self._find_key_case_insensitive(self._data, section)
                target_section_key = existing_section if existing_section is not None else section
                if target_section_key not in self._data:
                    self._data[target_section_key] = {}
                if not isinstance(self._data[target_section_key], dict):
                    raise ValueError(f"Section '{section}' exists but is not a dict")
                section_dict = self._data[target_section_key]
                existing_key = self._find_key_case_insensitive(section_dict, key)
                target_key = existing_key if existing_key is not None else key
                section_dict[target_key] = value
                
            # Scenario 3: no section, key and value at top level
            elif not section and key:
                existing_top_key = self._find_key_case_insensitive(self._data, key)
                target_key = existing_top_key if existing_top_key is not None else key
                self._data[target_key] = value
                
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
    