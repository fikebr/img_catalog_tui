import os
import logging
from typing import Literal

from img_catalog_tui.config import Config
from img_catalog_tui.core.folders import Folders
from img_catalog_tui.core.imageset import Imageset

# Define the update type selection data structure
UpdateType = Literal[
    "status", 
    "edits",
    "needs",
    "good_for", 
    "posted_to"
]

class ImagesetBatch:
    
    def __init__(self, config: Config, folder: str, update_type: UpdateType, imagesets: list[str], value: str, append: bool = False) -> None:
        """Initialize ImagesetBatch for bulk updating imagesets."""
        self.config = config
        self.folder = self._validate_folder(folder)
        self.update_type = update_type
        self.value = self._validate_value(value)
        self.append = self._validate_append(append)
        self.imagesets: dict[str, Imageset] = self._validate_imagesets(imagesets)
        
        # Log initialization
        logging.info(f"Initializing ImagesetBatch for folder: {folder}, update_type: {update_type}")
        
    def _validate_append(self, append: bool) -> bool:
        
        if self.update_type == "status":
            return False
        
        return append
        
    def _validate_value(self, value: str) -> str:
        """Validate that value is a valid option for the given update_type."""
        try:
            # Get valid options for this update_type from config
            valid_options = self.config.config_data.get(self.update_type)
            
            if valid_options is None:
                logging.error(f"No valid options found for update_type: {self.update_type}")
                raise ValueError(f"No valid options found for update_type: {self.update_type}")
            
            if not isinstance(valid_options, list):
                logging.error(f"Invalid config format for {self.update_type}, expected list but got {type(valid_options)}")
                raise ValueError(f"Invalid config format for {self.update_type}, expected list")
            
            # Check if value is in the list of valid options
            if value not in valid_options:
                logging.error(f"Invalid value '{value}' for update_type '{self.update_type}'. Valid options: {valid_options}")
                raise ValueError(f"Invalid value '{value}' for update_type '{self.update_type}'. Valid options: {valid_options}")
            
            logging.info(f"Value validation successful: {self.update_type} = {value}")
            return value
            
        except Exception as e:
            logging.error(f"Error validating value '{value}' for update_type '{self.update_type}': {e}", exc_info=True)
            raise
        
    def _validate_folder(self, folder: str) -> str:
        """Validate that folder exists in Folders object and on filesystem."""
        try:
            # Initialize Folders object to check registered folders
            folders_obj = Folders(config=self.config)
            
            # Check if folder exists in Folders object (search in values, not keys)
            if folder not in folders_obj.folders.values():
                logging.error(f"Folder '{folder}' not found in Folders registry")
                raise ValueError(f"Folder '{folder}' not found in Folders registry")
            
            # The folder parameter is already the full path
            full_path = folder
            
            # Validate that the folder exists on the OS
            if not os.path.exists(full_path):
                logging.error(f"Folder path does not exist on filesystem: {full_path}")
                raise FileNotFoundError(f"Folder path does not exist on filesystem: {full_path}")
            
            if not os.path.isdir(full_path):
                logging.error(f"Path is not a directory: {full_path}")
                raise NotADirectoryError(f"Path is not a directory: {full_path}")
            
            logging.info(f"Folder validation successful: {folder} -> {full_path}")
            return full_path
            
        except Exception as e:
            logging.error(f"Error validating folder '{folder}': {e}", exc_info=True)
            raise
    
    def _validate_imagesets(self, imagesets: list[str]) -> dict[str, Imageset]:
        """Validate imagesets and create Imageset objects for each one."""
        validated_imagesets: dict[str, Imageset] = {}
        
        try:
            for imageset_name in imagesets:
                # Construct imageset folder path
                imageset_path = os.path.join(self.folder, imageset_name)
                
                # Validate that the imageset folder exists
                if not os.path.exists(imageset_path):
                    logging.error(f"Imageset folder does not exist: {imageset_path}")
                    raise FileNotFoundError(f"Imageset folder does not exist: {imageset_path}")
                
                if not os.path.isdir(imageset_path):
                    logging.error(f"Imageset path is not a directory: {imageset_path}")
                    raise NotADirectoryError(f"Imageset path is not a directory: {imageset_path}")
                
                # Create Imageset object
                try:
                    imageset_obj = Imageset(
                        config=self.config,
                        folder_name=self.folder,
                        imageset_name=imageset_name
                    )
                    validated_imagesets[imageset_name] = imageset_obj
                    logging.info(f"Successfully created Imageset object for: {imageset_name}")
                    
                except Exception as e:
                    logging.error(f"Error creating Imageset object for '{imageset_name}': {e}", exc_info=True)
                    raise RuntimeError(f"Error creating Imageset object for '{imageset_name}': {e}")
            
            logging.info(f"Successfully validated {len(validated_imagesets)} imagesets")
            return validated_imagesets
            
        except Exception as e:
            logging.error(f"Error validating imagesets: {e}", exc_info=True)
            raise
    
    def _get_current_property_value(self, imageset_obj: Imageset, property_name: str) -> str:
        """Get the current value of a property from an imageset object."""
        try:
            if property_name == "status":
                return imageset_obj.status or ""
            elif property_name == "edits":
                return imageset_obj.edits or ""
            elif property_name == "needs":
                return imageset_obj.needs or ""
            elif property_name == "good_for":
                return imageset_obj.good_for or ""
            elif property_name == "posted_to":
                return imageset_obj.posted_to or ""
            else:
                raise ValueError(f"Unsupported property: {property_name}")
        except Exception as e:
            logging.warning(f"Error getting current value for {property_name}: {e}")
            return ""
    
    def _get_appended_value(self, current_value: str, new_value: str) -> str:
        """Handle appending a value to a comma-delimited string if it doesn't already exist."""
        if not current_value:
            return new_value
        
        # Convert comma-delimited string to list, strip whitespace
        current_items = [item.strip() for item in current_value.split(',') if item.strip()]
        
        # Check if new value already exists
        if new_value in current_items:
            logging.debug(f"Value '{new_value}' already exists in '{current_value}', no change needed")
            return current_value
        
        # Append new value
        current_items.append(new_value)
        result = ', '.join(current_items)
        logging.debug(f"Appended '{new_value}' to '{current_value}' -> '{result}'")
        return result
        
    def update_now(self) -> list[str]:
        """Update all imagesets with the specified value and return error statistics."""
        
        error_imagesets = []
        
        logging.info(f"Starting batch update of {len(self.imagesets)} imagesets with {self.update_type}={self.value} (append={self.append})")
        
        for imageset_name, imageset_obj in self.imagesets.items():
            
            try:
                # Determine the value to set based on append mode
                if self.append:
                    current_value = self._get_current_property_value(imageset_obj, self.update_type)
                    final_value = self._get_appended_value(current_value, self.value)
                else:
                    final_value = self.value
                
                # Set the property with the final value
                if self.update_type == "status":
                    imageset_obj.status = final_value
                elif self.update_type == "edits":
                    imageset_obj.edits = final_value
                elif self.update_type == "needs":
                    imageset_obj.needs = final_value
                elif self.update_type == "good_for":
                    imageset_obj.good_for = final_value
                elif self.update_type == "posted_to":
                    imageset_obj.posted_to = final_value
                else:
                    raise ValueError(f"Unsupported update_type: {self.update_type}")
                
                logging.debug(f"Successfully updated {imageset_name}: {self.update_type}={final_value} (append={self.append})")
                
            except Exception as e:
                error_imagesets.append(imageset_name)
                logging.error(f"Failed to update {imageset_name}: {e}", exc_info=True)
        
        # Log completion summary
        logging.info(f"Batch update completed: {len(self.imagesets) - len(error_imagesets)} successful, {len(error_imagesets)} failed")
        
        return error_imagesets
        
        
if __name__ == "__main__":
    
    from img_catalog_tui.logger import setup_logging
    
    config = Config()
    setup_logging()
    
    # status = ["new", "keep", "edit", "working", "posted", "archive"]
    # edits = ["creative", "photoshop", "rmbg"]
    # needs = ["upscale", "vector", "orig", "thumbnail", "interview"]
    # good_for = ["stock", "rb", "poster"]
    # posted_to = ["stock", "rb", "tp", "faa", "etsy"]
   
    folder = r"E:\fooocus\images\new\2024-08-14"
    imagesets = ["2024-08-14_13-19-21_8049"]
    update_type = "status"
    value = "bullshit"
    
    imageset_batch = ImagesetBatch(config=config, folder=folder, update_type=update_type, imagesets=imagesets, value=value)
    
    errors = imageset_batch.update_now()
    
    if errors:
        print(f"these imagesets failed: {", ".join(errors)}")
    else:
        print("Update Succeeded!")
    