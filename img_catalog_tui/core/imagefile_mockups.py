"""
ImageMockup class for creating mockup images using Photoshop.

This module provides functionality to generate mockup images by integrating
with Adobe Photoshop via JSX scripts.
"""

import json
import logging
import os
import re
import subprocess
from pathlib import Path

from img_catalog_tui.config import Config
from img_catalog_tui.utils.file_utils import get_imageset_from_filename


class ImageMockup:
    """
    Class to encapsulate logic for creating mockup images for a given ImageFile.
    
    This class manages the process of generating mockup images by:
    1. Validating all required paths and files
    2. Building a JSON parameter file for the JSX script
    3. Executing Photoshop with the JSX script
    4. Tracking the generated mockup files
    """
    
    def __init__(self, config: Config, image_file_path: str, mockup_type: str, orientation: str, layer_name: str = None):
        """
        Initialize the ImageMockup instance.
        
        Args:
            config: The Config object from the app
            image_file_path: Full path to the image file
            mockup_type: Type of mockups to create (e.g., 'poster', 'tshirt')
            orientation: Orientation of the image ('horizontal' or 'vertical')
            layer_name: Name of the smart object layer (optional, defaults to config)
        """
        self.config = config
        self.mockup_cfg: dict = self.config.config_data.get("mockups", {})
        
        # Store input parameters
        self.image_file_path = image_file_path
        self.mockup_type = mockup_type
        self.orientation = orientation
        
        # Initialize properties
        self.base_folder: str = None
        self.layer_name: str = None
        self.tags: list[str] = []
        self.version: int = 1
        self.output_folder: str = None
        self.mockups_folder: str = None
        self.mockup_script: str = None
        self.mockup_script_json: str = None
        self.mockups: list[str] = []
        
        # Run validation and initialization methods
        self._validate_base_folder()
        self._validate_image_file()
        self._get_file_tags()
        self._get_version()
        self._get_layer_name(layer_name)
        self._get_mockups_folder()
        self._get_mockup_script()
        self._validate_output_folder()
        self._get_existing_mockup_images()
    
    def _validate_base_folder(self):
        """Validate that the base folder exists."""
        self.base_folder = self.mockup_cfg.get("mockups_base_folder", "")
        
        if not self.base_folder:
            raise ValueError("mockups_base_folder not found in configuration")
        
        if not os.path.exists(self.base_folder):
            raise FileNotFoundError(f"Base folder does not exist: {self.base_folder}")
        
        if not os.path.isdir(self.base_folder):
            raise ValueError(f"Base folder is not a directory: {self.base_folder}")
        
        logging.info(f"Validated base folder: {self.base_folder}")
    
    def _validate_image_file(self):
        """Validate that the image file exists."""
        if not os.path.exists(self.image_file_path):
            raise FileNotFoundError(f"Image file does not exist: {self.image_file_path}")
        
        if not os.path.isfile(self.image_file_path):
            raise ValueError(f"Image path is not a file: {self.image_file_path}")
        
        logging.info(f"Validated image file: {self.image_file_path}")
    
    def _get_file_tags(self):
        """Extract file tags from the filename."""
        file_tags = self.config.config_data.get("file_tags", [])
        filename = os.path.basename(self.image_file_path)
        
        _, _, tags = get_imageset_from_filename(filename, file_tags)
        self.tags = tags
        
        logging.info(f"Extracted tags: {self.tags}")
    
    def _get_version(self):
        """Get version from filename tags or default to 1."""
        self.version = 1
        
        # Look for version tag in tags (v2, v3, v4, etc.)
        for tag in self.tags:
            if tag.startswith('v') and tag[1:].isdigit():
                self.version = int(tag[1:])
                logging.info(f"Found version tag: v{self.version}")
                break
        
        if self.version == 1:
            logging.info("No version tag found, defaulting to version 1")
    
    def _get_layer_name(self, layer_name: str = None):
        """Get the smart object layer name from parameter or config."""
        if layer_name:
            self.layer_name = layer_name
        else:
            self.layer_name = self.mockup_cfg.get("smart_object_layer_name", "Poster")
        
        logging.info(f"Smart object layer name: {self.layer_name}")
    
    def _validate_output_folder(self):
        """Validate and create the output folder for mockups."""
        # Get the folder that the image file is in
        image_folder = os.path.dirname(self.image_file_path)
        
        # Output folder is <imagefile_folder>/_mockups_<version>
        if self.version == 1:
            output_folder = os.path.join(image_folder, "_mockups")
        else:
            output_folder = os.path.join(image_folder, f"_mockups_v{self.version}")
        
        # Create the folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
            logging.info(f"Created output folder: {output_folder}")
        else:
            logging.info(f"Output folder already exists: {output_folder}")
        
        self.output_folder = output_folder
    
    def _get_mockups_folder(self):
        """Get and validate the mockups folder containing PSD files."""
        # mockups_folder = <base_folder>/<mockup_type>/<orientation>
        mockups_folder = os.path.join(self.base_folder, self.mockup_type, self.orientation)
        
        if not os.path.exists(mockups_folder):
            raise FileNotFoundError(f"Mockups folder does not exist: {mockups_folder}")
        
        if not os.path.isdir(mockups_folder):
            raise ValueError(f"Mockups path is not a directory: {mockups_folder}")
        
        self.mockups_folder = mockups_folder
        logging.info(f"Validated mockups folder: {self.mockups_folder}")
    
    def _get_mockup_script(self):
        """Get the paths for the JSX script and params JSON file."""
        script_name = self.mockup_cfg.get("jsx_script", "mockup_generator.jsx")
        params_name = self.mockup_cfg.get("params_json", "params.json")
        
        self.mockup_script = os.path.join(self.base_folder, script_name)
        self.mockup_script_json = os.path.join(self.base_folder, params_name)
        
        # Validate that the script exists
        if not os.path.exists(self.mockup_script):
            raise FileNotFoundError(f"JSX script does not exist: {self.mockup_script}")
        
        logging.info(f"Mockup script: {self.mockup_script}")
        logging.info(f"Params JSON: {self.mockup_script_json}")
    
    def _get_existing_mockup_images(self):
        """Load list of existing mockup images from output folder."""
        self.mockups = []
        
        if not os.path.exists(self.output_folder):
            logging.warning(f"Output folder does not exist: {self.output_folder}")
            return
        
        # Get all image files in the output folder
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
        
        try:
            for filename in os.listdir(self.output_folder):
                file_path = os.path.join(self.output_folder, filename)
                
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in image_extensions:
                        self.mockups.append(file_path)
            
            self.mockups.sort()
            logging.info(f"Found {len(self.mockups)} existing mockup images")
            
        except Exception as e:
            logging.error(f"Error reading mockup images: {e}", exc_info=True)
    
    def _build_params_json(self):
        """Build and write the params JSON file for the JSX script."""
        # Validate required properties
        if not self.mockups_folder:
            raise ValueError("mockups_folder is not set")
        if not self.image_file_path:
            raise ValueError("image_file_path is not set")
        if not self.layer_name:
            raise ValueError("layer_name is not set")
        if not self.output_folder:
            raise ValueError("output_folder is not set")
        if not self.mockup_script_json:
            raise ValueError("mockup_script_json is not set")
        
        # Build the params dictionary
        params = {
            "mockups_folder": self.mockups_folder,
            "image_path": self.image_file_path,
            "smart_layer_name": self.layer_name,
            "output_folder": self.output_folder,
            "export_format": "jpg"
        }
        
        # Write JSON to file
        try:
            with open(self.mockup_script_json, 'w') as f:
                json.dump(params, f, indent=2)
            
            logging.info(f"Wrote params JSON to: {self.mockup_script_json}")
            logging.debug(f"Params: {json.dumps(params, indent=2)}")
            
        except Exception as e:
            logging.error(f"Error writing params JSON: {e}", exc_info=True)
            raise
    
    def build_mockups(self):
        """Execute Photoshop with the JSX script to build mockups."""
        # Get Photoshop executable path
        photoshop_exe = self.mockup_cfg.get("photoshop_exe", "")
        
        if not photoshop_exe:
            raise ValueError("photoshop_exe not found in configuration")
        
        if not os.path.exists(photoshop_exe):
            raise FileNotFoundError(f"Photoshop executable not found: {photoshop_exe}")
        
        # Build params JSON file
        self._build_params_json()
        
        # Build command to execute Photoshop with the JSX script
        # Photoshop command format: photoshop.exe script.jsx
        cmd = [photoshop_exe, self.mockup_script]
        
        logging.info(f"Executing Photoshop command: {' '.join(cmd)}")
        
        try:
            # Execute the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logging.info("Photoshop script executed successfully")
                logging.debug(f"Output: {result.stdout}")
            else:
                logging.error(f"Photoshop script failed with return code {result.returncode}")
                logging.error(f"Error output: {result.stderr}")
                raise RuntimeError(f"Photoshop script execution failed: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            logging.error("Photoshop script execution timed out")
            raise RuntimeError("Photoshop script execution timed out after 5 minutes")
        
        except Exception as e:
            logging.error(f"Error executing Photoshop script: {e}", exc_info=True)
            raise
        
        # Refresh the list of existing mockup images
        self._get_existing_mockup_images()
        
        logging.info(f"Build complete. Total mockups: {len(self.mockups)}")
    
    def to_dict(self) -> dict:
        """Convert the object properties to a dictionary."""
        return {
            "image_file_path": self.image_file_path,
            "mockup_type": self.mockup_type,
            "orientation": self.orientation,
            "base_folder": self.base_folder,
            "layer_name": self.layer_name,
            "tags": self.tags,
            "version": self.version,
            "output_folder": self.output_folder,
            "mockups_folder": self.mockups_folder,
            "mockup_script": self.mockup_script,
            "mockup_script_json": self.mockup_script_json,
            "mockups": self.mockups,
            "mockups_count": len(self.mockups)
        }
    
    def to_json(self) -> str:
        """Convert the object to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


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
        config = Config()
        
        # Test parameters - update these paths as needed
        test_image_path = r"E:\fooocus\images\new\2024-04-13\2024-04-13_17-23-01_7209\2024-04-13_17-23-01_7209_orig.png"
        test_mockup_type = "poster"
        test_orientation = "vertical"
        
        # Create ImageMockup instance
        mockup = ImageMockup(
            config=config,
            image_file_path=test_image_path,
            mockup_type=test_mockup_type,
            orientation=test_orientation
        )
        
        logging.info("ImageMockup object created successfully")
        logging.info(f"Image file: {mockup.image_file_path}")
        logging.info(f"Mockup type: {mockup.mockup_type}")
        logging.info(f"Orientation: {mockup.orientation}")
        logging.info(f"Base folder: {mockup.base_folder}")
        logging.info(f"Output folder: {mockup.output_folder}")
        logging.info(f"Mockups folder: {mockup.mockups_folder}")
        logging.info(f"Layer name: {mockup.layer_name}")
        logging.info(f"Version: {mockup.version}")
        logging.info(f"Tags: {mockup.tags}")
        logging.info(f"Existing mockups: {len(mockup.mockups)}")
        
        mockup.build_mockups()
        
        # Print as JSON
        logging.info(f"Object as JSON:\n{mockup.to_json()}")
        
    except Exception as e:
        logging.error(f"Error in main: {e}", exc_info=True)

