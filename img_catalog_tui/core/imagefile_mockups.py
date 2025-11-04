import json
import logging
import os
import re

from PIL import Image

from img_catalog_tui.config import Config
from img_catalog_tui.utils.file_utils import get_imageset_from_filename

class ImageMockups:
    
    def __init__(self, config: Config, image_file_path: str, mockup_folder_name: str):
        
        self.config = config
        self.mockup_cfg: dict = self.config.config_data.get("mockups", {})
        self.image_file_path = self._validate_image_file(image_file_path)
        self.mockup_folder_name = mockup_folder_name
        self.mockup_folder_path = self._validate_mockup_folder()
        self.output_folder: str = self._validate_output_folder()
        self.smart_object_layer_name: str = self.mockup_cfg.get("smart_object_layer_name", "Artwork")
        
    
    def _validate_image_file(self, image_file_path: str) -> str:
        """Validate that the image file exists and is a valid image."""
        if not os.path.exists(image_file_path):
            raise FileNotFoundError(f"Image file does not exist: {image_file_path}")
        
        try:
            with Image.open(image_file_path) as img:
                img.verify()
            logging.info(f"Validated image file: {image_file_path}")
            return image_file_path
        except Exception as e:
            raise ValueError(f"File is not a valid image: {image_file_path}") from e    
    
    def _validate_mockup_folder(self) -> str:
        """Validate that the mockup folder exists and is accessible."""
        folders: dict = self.mockup_cfg.get("folders", {})
        mockup_folder_base = self.mockup_cfg.get("mockups_base_folder", "")
        
        if self.mockup_folder_name not in folders:
            raise ValueError(f"Mockup Folder Name not found: {self.mockup_folder_name}")
            
        mockup_folder_path: str = folders.get(self.mockup_folder_name, "")
        mockup_folder_path = os.path.join(mockup_folder_base, mockup_folder_path)
        
        if not os.path.exists(mockup_folder_path):
            raise FileNotFoundError(f"Mockup folder does not exist: {mockup_folder_path}")
        
        if not os.path.isdir(mockup_folder_path):
            raise ValueError(f"Mockup path is not a directory: {mockup_folder_path}")
        
        logging.info(f"Validated mockup folder: {mockup_folder_path}")
        return mockup_folder_path
    
    
    def _validate_output_folder(self) -> str:
        """Validate and create the output folder for mockups."""
        # Get the folder for self.image_file_path
        image_folder = os.path.dirname(self.image_file_path)
        
        # Get the basename for self.image_file_path
        image_basename = os.path.basename(self.image_file_path)
        
        # Use regex to look for "_v(\d)_" in basename. this is the image_version.
        version_match = re.search(r'_v(\d+)_', image_basename)
        image_version = version_match.group(1) if version_match else None
        
        # Output folder is the image folder + "mockups"
        output_folder = os.path.join(image_folder, "mockups")
        
        # If there was a version found for image_version then append that to the output folder name.
        if image_version:
            output_folder = f"{output_folder}_v{image_version}"
        
        # Now check to see if the folder exists.
        if os.path.exists(output_folder):
            # If yes then check to see if it has files already and error if yes.
            if os.listdir(output_folder):
                raise FileExistsError(f"Output folder already contains files: {output_folder}")
            logging.info(f"Using existing empty output folder: {output_folder}")
        else:
            # If no then create the folder
            os.makedirs(output_folder, exist_ok=True)
            logging.info(f"Created output folder: {output_folder}")
        
        return output_folder
    
    def get_mockup_files(self) -> list[dict]:
        """Return list of PSD files in the mockup folder."""
        try:
            mockup_files = []
            
            # List all files in mockup folder
            for filename in os.listdir(self.mockup_folder_path):
                if filename.lower().endswith(('.psd', '.psb')):
                    mockup_files.append({
                        'filename': filename,
                        'basename': os.path.splitext(filename)[0]
                    })
            
            # Sort by filename
            mockup_files.sort(key=lambda x: x['filename'])
            
            logging.info(f"Found {len(mockup_files)} mockup files in {self.mockup_folder_path}")
            return mockup_files
            
        except Exception as e:
            logging.error(f"Error getting mockup files: {e}", exc_info=True)
            return []
    
    def get_psd_file_path(self, psd_filename: str) -> str:
        """Get the full path to a specific PSD file in the mockup folder."""
        return os.path.join(self.mockup_folder_path, psd_filename)
    
    def get_config_dict(self) -> dict:
        """Return configuration dictionary that gets written to json and used by the photoshop *.jsx script."""
        try:
            # Get file tags from config
            file_tags = self.config.config_data.get("file_tags", [])
            
            # Use get_imageset_from_filename to get the imagesetname and tags
            imageset_name, ext, tags = get_imageset_from_filename(
                os.path.basename(self.image_file_path), file_tags
            )
            
            # Check if there is a version tag (ie. v2, v3, v4)
            version_tag = None
            for tag in tags:
                if tag.startswith('v') and tag[1:].isdigit():
                    version_tag = tag
                    break
            
            # Create output filename template
            if version_tag:
                output_template = f"{imageset_name}_{version_tag}-{{mockup}}{ext}"
            else:
                output_template = f"{imageset_name}-{{mockup}}{ext}"
            
            return {
                "image_path": self.image_file_path,
                "mockup_folder_path": self.mockup_folder_path,
                "output_folder": self.output_folder,
                "output_template": output_template,
                "smart_object_layer_name": self.smart_object_layer_name,
                "imageset_name": imageset_name,
                "version_tag": version_tag,
                "extension": ext
            }
            
        except Exception as e:
            logging.error(f"Error getting config dict: {e}", exc_info=True)
            return {}


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Load configuration
        from img_catalog_tui.config import Config
        config = Config()
        
        # Test parameters - update these paths as needed
        test_image_path = r"E:\fooocus\images\new\2024-03-25\2024-03-25_00-01-47_2872\2024-03-25_00-01-47_2872_up4.png"
        test_mockup_folder_name = "poster_vertical"
        
        # Create ImageMockups instance
        mockups = ImageMockups(
            config=config,
            image_file_path=test_image_path,
            mockup_folder_name=test_mockup_folder_name
        )
        
        logging.info("ImageMockups object created successfully")
        logging.info(f"Image file: {mockups.image_file_path}")
        logging.info(f"Mockup folder: {mockups.mockup_folder_path}")
        logging.info(f"Output folder: {mockups.output_folder}")
        logging.info(f"Smart object layer: {mockups.smart_object_layer_name}")
        
        # Test getting mockup files
        mockup_files = mockups.get_mockup_files()
        logging.info(f"Found {len(mockup_files)} mockup files:")
        for mf in mockup_files:
            logging.info(f"  - {mf['filename']}")
        
        # Test getting config dict
        config_dict = mockups.get_config_dict()
        logging.info(f"Config dict: {json.dumps(config_dict, indent=2)}")
        
    except Exception as e:
        logging.error(f"Error in main: {e}", exc_info=True)