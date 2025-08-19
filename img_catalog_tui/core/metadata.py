"""
Metadata extraction and handling for the Image Catalog TUI application.
"""

import logging
import os
from typing import Dict, List, Any, Optional

import toml

from img_catalog_tui.config import Config
from img_catalog_tui.utils.exif import (
    get_exif_data, is_fooocus_image, is_midjourney_image,
    parse_fooocus_metadata, parse_midjourney_metadata
)
from img_catalog_tui.utils.file_utils import find_file_with_tag


def extract_exif_data_from_orig_images(folder_name: str, imagesets: List[str], config: Config) -> None:
    """
    Extract EXIF metadata from original images and save to TOML files.
    
    Args:
        folder_name: Path to the parent folder
        imagesets: List of imageset names
        config: Application configuration
    """
    logging.info(f"Extracting EXIF data from original images in {folder_name}")
    
    try:
        for imageset in imagesets:
            imageset_folder = os.path.join(folder_name, imageset)
            
            # Skip if not a directory
            if not os.path.isdir(imageset_folder):
                continue
                
            # Get the original image file
            orig_image_file = find_file_with_tag(imageset_folder, "orig")
            if not orig_image_file:
                logging.warning(f"No original image found for {imageset}")
                continue
                
            # Get the TOML file path
            toml_file = os.path.join(imageset_folder, f"{imageset}.toml")
            
            # Load existing TOML data if available
            toml_data = {}
            if os.path.exists(toml_file):
                try:
                    toml_data = toml.load(toml_file)
                except Exception as e:
                    logging.error(f"Error loading TOML file {toml_file}: {e}", exc_info=True)
            else:
                toml_data["imageset"] = imageset
                
            # Skip if metadata already exists
            if "source" in toml_data:
                if toml_data["source"] == "midjourney" and "midjourney" in toml_data and "prompt" in toml_data["midjourney"]:
                    logging.debug(f"Midjourney metadata already exists for {imageset}")
                    continue
                    
                if toml_data["source"] == "fooocus" and "fooocus" in toml_data and "Prompt" in toml_data["fooocus"]:
                    logging.debug(f"Fooocus metadata already exists for {imageset}")
                    continue
            
            # Extract EXIF data from the original image
            exif_data = get_exif_data(orig_image_file)
            if not exif_data:
                logging.warning(f"No EXIF data found in {orig_image_file}")
                continue
                
            # Get source identification settings from config
            sources_config = config.get("sources", {})
            midjourney_author = sources_config.get("midjourney_author", "aardvark_fike")
            midjourney_exif_field = sources_config.get("midjourney_exif_field", "PNG:Description")
            fooocus_scheme = sources_config.get("fooocus_scheme", "PNG:Fooocus_scheme")
            fooocus_exif_field = sources_config.get("fooocus_exif_field", "PNG:Parameters")
                
            # Check if this is a Fooocus image
            if is_fooocus_image(exif_data, fooocus_scheme):
                fooocus_data = parse_fooocus_metadata(exif_data, fooocus_exif_field)
                if fooocus_data:
                    toml_data["source"] = "fooocus"
                    toml_data["fooocus"] = fooocus_data
                    logging.info(f"Extracted Fooocus metadata for {imageset}")
                    
            # Check if this is a Midjourney image
            elif is_midjourney_image(exif_data, "PNG:Author", midjourney_author):
                midjourney_data = parse_midjourney_metadata(exif_data, midjourney_exif_field)
                if midjourney_data:
                    toml_data["source"] = "midjourney"
                    toml_data["midjourney"] = midjourney_data
                    logging.info(f"Extracted Midjourney metadata for {imageset}")
            
            # Save TOML data
            try:
                with open(toml_file, "w") as f:
                    toml.dump(toml_data, f)
                logging.info(f"Saved metadata to {toml_file}")
            except Exception as e:
                logging.error(f"Error saving TOML file {toml_file}: {e}", exc_info=True)
                
    except Exception as e:
        logging.error(f"Error extracting EXIF data: {e}", exc_info=True)


def load_imageset_metadata(imageset_folder: str, imageset: str) -> Optional[Dict[str, Any]]:
    """
    Load metadata for an imageset from its TOML file.
    
    Args:
        imageset_folder: Path to the parent folder
        imageset: Name of the imageset
        
    Returns:
        Dictionary containing metadata, or None if not found
    """
    toml_file = os.path.join(imageset_folder, imageset, f"{imageset}.toml")
    
    try:
        if os.path.exists(toml_file):
            return toml.load(toml_file)
        return None
    except Exception as e:
        logging.error(f"Error loading metadata for {imageset}: {e}", exc_info=True)
        return None


def save_imageset_metadata(imageset_folder: str, imageset: str, metadata: Dict[str, Any]) -> bool:
    """
    Save metadata for an imageset to its TOML file.
    
    Args:
        imageset_folder: Path to the parent folder
        imageset: Name of the imageset
        metadata: Dictionary containing metadata
        
    Returns:
        True if successful, False otherwise
    """
    toml_file = os.path.join(imageset_folder, imageset, f"{imageset}.toml")
    
    try:
        with open(toml_file, "w") as f:
            toml.dump(metadata, f)
        logging.info(f"Saved metadata to {toml_file}")
        return True
    except Exception as e:
        logging.error(f"Error saving metadata for {imageset}: {e}", exc_info=True)
        return False
