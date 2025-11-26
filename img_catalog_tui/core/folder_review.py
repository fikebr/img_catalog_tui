import logging
from pathlib import Path


from img_catalog_tui.config import Config
from img_catalog_tui.logger import setup_logging

from img_catalog_tui.core.imageset import Imageset
from img_catalog_tui.core.folder import ImagesetFolder
from img_catalog_tui.core.folders import Folders


# self.config.config_data["status"]
# status = ["new", "keep", "edit", "working", "posted", "archive"]
# edits = ["creative", "photoshop", "rmbg"]
# needs = ["upscale", "vector", "orig", "thumbnail", "interview", "creativeup"]
# good_for = ["stock", "rb", "poster"]

class FolderReview:
    
    def __init__(self, config: Config, folder_name: str, states: list[str], review_type: str, options: list[str], append: bool = False):
        """Initialize FolderReview with validation and filtering.
        
        Args:
            config: Configuration object
            folder_name: Folder basename (for registry lookup) or full path to folder
            states: List of imageset states to include in review
            review_type: Type of review (status, edits, needs, good_for, posted_to)
            options: List of valid options for the review type
            append: Whether to append to existing values during updates
        """
        logging.info(f"Initializing FolderReview for folder: {folder_name}, states: {states}, review_type: {review_type}")
        
        try:
            self.config = config
            self.foldername = self._validate_folder(folder_name)
            self.states = self._validate_states(states)
            self.review_type = self._validate_review_type(review_type)
            self.options = self._get_options(options)
            self.append = append 
            self.imagesets: dict[str, Imageset] = self._get_imagesets(self.foldername, self.states)
            
            logging.info(f"FolderReview initialized successfully. Found {len(self.imagesets)} imagesets matching criteria")
        except Exception as e:
            logging.error(f"Failed to initialize FolderReview: {e}")
            raise
        
    def _validate_folder(self, folder_name: str) -> str:
        """Validate that folder exists on filesystem and optionally in folders registry."""
        logging.debug(f"Validating folder: {folder_name}")
        
        try:
            folder_path = Path(folder_name)
            
            if folder_path.is_absolute():
                # Full path provided - validate it directly and optionally check registry
                logging.debug(f"Full path provided: {folder_name}")
                
                # Check if folder exists on the filesystem
                if not folder_path.exists():
                    logging.error(f"Folder does not exist on filesystem: {folder_name}")
                    raise FileNotFoundError(f"Folder does not exist on filesystem: {folder_name}")
                
                if not folder_path.is_dir():
                    logging.error(f"Path is not a directory: {folder_name}")
                    raise NotADirectoryError(f"Path is not a directory: {folder_name}")
                
                # Optional: Check if this folder is registered (for consistency but not required)
                try:
                    folders = Folders(config=self.config)
                    basename = folder_path.name
                    if basename in folders.folders:
                        registry_path = folders.folders[basename]
                        if str(folder_path) != registry_path:
                            logging.warning(f"Full path '{folder_name}' differs from registry path '{registry_path}' for basename '{basename}'")
                    else:
                        logging.warning(f"Folder basename '{basename}' not found in registry, but full path validation successful")
                except Exception as registry_error:
                    logging.warning(f"Could not check folder registry: {registry_error}")
                
                logging.info(f"Full path validation successful: {folder_name}")
                return str(folder_path)
                
            else:
                # Basename provided - look up in registry
                logging.debug(f"Basename provided: '{folder_name}'")
                
                # Initialize folders object to check registry
                folders = Folders(config=self.config)
                logging.debug(f"Folders registry loaded with {len(folders.folders)} entries")
                
                # Check if folder exists in the folders registry using basename
                if folder_name not in folders.folders:
                    logging.error(f"Folder '{folder_name}' not found in folders registry. Available folders: {list(folders.folders.keys())}")
                    raise ValueError(f"Folder '{folder_name}' not found in folders registry")
                
                # Get the full path from the folders registry
                full_path = folders.folders[folder_name]
                logging.debug(f"Folder registry lookup successful. Full path: {full_path}")
                
                # Check if folder exists on the filesystem
                validated_folder_path = Path(full_path)
                if not validated_folder_path.exists():
                    logging.error(f"Folder does not exist on filesystem: {full_path}")
                    raise FileNotFoundError(f"Folder does not exist on filesystem: {full_path}")
                
                if not validated_folder_path.is_dir():
                    logging.error(f"Path is not a directory: {full_path}")
                    raise NotADirectoryError(f"Path is not a directory: {full_path}")
                
                logging.info(f"Registry-based validation successful: {full_path}")
                return full_path
            
        except Exception as e:
            logging.error(f"Folder validation failed for '{folder_name}': {e}")
            raise
    
    def _validate_review_type(self, review_type: str) -> str:
        """Validate that review_type is supported."""
        logging.debug(f"Validating review type: {review_type}")
        
        try:
            # Get the review types from the config
            review_types = self.config.config_data.get("review_types", [])
            logging.debug(f"Available review types from config: {review_types}")
            
            # Check if review_type is in the valid list
            if review_type not in review_types:
                logging.error(f"Invalid review_type '{review_type}'. Valid options: {review_types}")
                raise ValueError(f"Invalid review_type '{review_type}'. Valid options: {review_types}")
            
            logging.info(f"Review type validation successful: {review_type}")
            return review_type
            
        except Exception as e:
            logging.error(f"Review type validation failed for '{review_type}': {e}")
            raise
    
    def _validate_states(self, states: list[str]) -> list[str]:
        """Validate states against config status values and handle 'all' special case."""
        logging.debug(f"Validating states: {states}")
        
        try:
            # Get the possible status values from config
            valid_statuses = self.config.config_data.get("status", [])
            logging.debug(f"Available statuses from config: {valid_statuses}")
            
            # Handle "all" special case - return all possible status values
            if "all" in states:
                logging.info(f"'all' detected in states, expanding to all valid statuses: {valid_statuses}")
                return valid_statuses
            
            # Validate each state in the list
            for state in states:
                if state not in valid_statuses:
                    logging.error(f"Invalid state '{state}'. Valid options: {valid_statuses + ['all']}")
                    raise ValueError(f"Invalid state '{state}'. Valid options: {valid_statuses + ['all']}")
            
            logging.info(f"States validation successful: {states}")
            return states
            
        except Exception as e:
            logging.error(f"States validation failed for {states}: {e}")
            raise
    
    def _get_options(self, options: list[str]) -> list[str]:
        """Get and validate options based on review type, handle 'all' special case."""
        logging.debug(f"Getting options for review type '{self.review_type}': {options}")
        
        try:
            # Check if review_type exists in config_data
            if self.review_type not in self.config.config_data:
                available_keys = list(self.config.config_data.keys())
                logging.error(f"Review type '{self.review_type}' not found in config_data. Available keys: {available_keys}")
                raise ValueError(f"Review type '{self.review_type}' not found in config_data. Available keys: {available_keys}")
            
            # Get the possible options for the review type from config
            valid_options = self.config.config_data[self.review_type]
            logging.debug(f"Valid options for '{self.review_type}': {valid_options}")
            
            # Handle "all" special case - return all possible options
            if "all" in options:
                logging.info(f"'all' detected in options, expanding to all valid options: {valid_options}")
                return valid_options
            
            # Validate each option in the list
            for option in options:
                if option not in valid_options:
                    logging.error(f"Invalid option '{option}' for review_type '{self.review_type}'. Valid options: {valid_options + ['all']}")
                    raise ValueError(f"Invalid option '{option}' for review_type '{self.review_type}'. Valid options: {valid_options + ['all']}")
            
            logging.info(f"Options validation successful for '{self.review_type}': {options}")
            return options
            
        except Exception as e:
            logging.error(f"Options validation failed for '{self.review_type}' with options {options}: {e}")
            raise
    
    def _get_imagesets(self, foldername: str, states: list[str]) -> dict[str, Imageset]:
        """Create folder object and return imagesets that match the specified states."""
        logging.debug(f"Loading imagesets from folder: {foldername} with states filter: {states}")
        
        try:
            # Create a folder object for foldername
            logging.debug(f"Creating ImagesetFolder object for: {foldername}")
            folder = ImagesetFolder(config=self.config, foldername=foldername)
            logging.info(f"Successfully loaded folder with {len(folder.imagesets)} total imagesets")
            
            # Loop through the folder.imagesets and save if the status is in states
            filtered_imagesets: dict[str, Imageset] = {}
            logging.debug(f"Filtering imagesets by states: {states}")
            
            for imageset_name, imageset in folder.imagesets.items():
                if imageset.status in states:
                    filtered_imagesets[imageset_name] = imageset
                    logging.debug(f"Included imageset '{imageset_name}' with status '{imageset.status}'")
                else:
                    logging.debug(f"Excluded imageset '{imageset_name}' with status '{imageset.status}'")
            
            logging.info(f"Filtered {len(filtered_imagesets)} imagesets from {len(folder.imagesets)} total imagesets")
            
            # Log summary of filtered imagesets by status
            status_counts = {}
            for imageset in filtered_imagesets.values():
                status_counts[imageset.status] = status_counts.get(imageset.status, 0) + 1
            logging.info(f"Imageset status distribution: {status_counts}")
            
            # Return the saved imagesets
            return filtered_imagesets
            
        except Exception as e:
            logging.error(f"Failed to load and filter imagesets from '{foldername}': {e}")
            raise


def create_folder_review(config: Config, folder_name: str, review_name: str) -> FolderReview:
    """Factory function to create FolderReview objects using predefined review configurations.
    
    Args:
        config: Configuration object
        folder_name: Name or path of the folder to review
        review_name: Name of the predefined review configuration
        append: Whether to append to existing values
        
    Returns:
        Configured FolderReview object
        
    Raises:
        ValueError: If review_name is not found in configuration
        KeyError: If required configuration keys are missing
    """
    logging.info(f"Creating FolderReview using factory with review_name: {review_name}")
    
    try:
        # Check if review_presets section exists in config
        if "review_presets" not in config.config_data:
            logging.error("No 'review_presets' section found in configuration")
            raise ValueError("No 'review_presets' section found in configuration. Please add review presets to config.toml")
        
        review_presets = config.config_data["review_presets"]
        
        # Check if the specific review_name exists
        if review_name not in review_presets:
            available_reviews = list(review_presets.keys())
            logging.error(f"Review '{review_name}' not found in presets. Available: {available_reviews}")
            raise ValueError(f"Review '{review_name}' not found in presets. Available reviews: {available_reviews}")
        
        # Get the preset configuration
        preset = review_presets[review_name]
        logging.debug(f"Found preset configuration for '{review_name}': {preset}")
        
        # Extract required parameters from preset
        try:
            states = preset["states"]
            review_type = preset["review_type"]
            options = preset["options"]
            append = preset.get("append", False)
            
            logging.info(f"Extracted parameters - states: {states}, review_type: {review_type}, options: {options}")
            
        except KeyError as e:
            missing_key = str(e).strip("'")
            logging.error(f"Missing required key '{missing_key}' in preset '{review_name}'")
            raise KeyError(f"Missing required key '{missing_key}' in preset '{review_name}'. Required keys: states, review_type, options")
        
        # Create and return FolderReview object
        logging.info("Creating FolderReview object with factory parameters")
        review = FolderReview(
            config=config,
            folder_name=folder_name,
            states=states,
            review_type=review_type,
            options=options,
            append=append
        )
        
        logging.info(f"Successfully created FolderReview using preset '{review_name}'")
        return review
        
    except Exception as e:
        logging.error(f"Failed to create FolderReview using factory with review_name '{review_name}': {e}")
        raise


if __name__ == "__main__":

    setup_logging()
    logging.info("Starting FolderReview main execution")

    try:
        # Load configuration
        logging.info("Loading configuration from ./config/config.toml")
        config = Config("./config/config.toml")  # Adjust path as needed
        logging.info("Configuration loaded successfully")

        folder_name = r"2025-08-17"  # Use basename - the key in folders registry
        review_name = "new_status_review"
        
        review = create_folder_review(config=config, folder_name=folder_name, review_name=review_name)
        # states = ["new"]
        # review_type = "status"
        # options = ["keep", "archive"]
        
        # logging.info(f"Creating FolderReview with parameters: folder={folder_name}, states={states}, review_type={review_type}, options={options}")
        
        # review = FolderReview(
        #     config=config,
        #     folder_name=folder_name,
        #     states=states,
        #     review_type=review_type,
        #     options=options
        # )
        
        logging.info(f"FolderReview created successfully. Found imagesets: {list(review.imagesets.keys())}")
        print(review.options)
        
    except Exception as e:
        logging.error(f"Main execution failed: {e}")
        raise