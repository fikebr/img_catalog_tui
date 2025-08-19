"""
Folder operations for the Image Catalog TUI application.
"""

import logging
import os
from typing import Dict, List, Any

from img_catalog_tui.config import Config
from img_catalog_tui.core.metadata import extract_exif_data_from_orig_images
from img_catalog_tui.utils.file_utils import (
    create_folder, delete_folder, find_file_with_tag,
    get_imageset_from_filename, is_image_file, move_files
)


def get_imagesets_in_folder(folder_name: str, config: Config) -> List[str]:
    """
    Get a list of imagesets in a folder.
    
    Args:
        folder_name: Path to the folder to scan
        config: Application configuration
        
    Returns:
        List of imageset names
    """
    logging.info(f"Scanning folder for imagesets: {folder_name}")
    imagesets = []
    
    try:
        # Check if folder exists
        if not os.path.exists(folder_name):
            logging.error(f"Folder does not exist: {folder_name}")
            return []
            
        # Get file tags from config
        file_tags = config.get_file_tags()
        
        # Scan folder for imagesets
        for item in os.listdir(folder_name):
            item_path = os.path.join(folder_name, item)
            
            # Skip items starting with underscore
            if item.startswith("_"):
                continue
                
            # If item is a directory, it's an imageset
            if os.path.isdir(item_path):
                imagesets.append(item)
                logging.debug(f"Found imageset directory: {item}")
                
            # If item is a file, extract imageset name and create folder
            elif os.path.isfile(item_path) and not item.startswith("_"):
                # Skip non-image files
                if not is_image_file(item_path):
                    continue
                    
                # Get imageset name from filename
                imageset, _, _ = get_imageset_from_filename(item, file_tags)
                
                # Create imageset folder if it doesn't exist
                imageset_folder = os.path.join(folder_name, imageset)
                if create_folder(imageset_folder):
                    # Move all files for this imageset to the new folder
                    move_files(imageset, folder_name, imageset_folder)
                    
                    if imageset not in imagesets:
                        imagesets.append(imageset)
                        logging.info(f"Created imageset folder for: {imageset}")
        
        logging.info(f"Found {len(imagesets)} imagesets in {folder_name}")
        return imagesets
        
    except Exception as e:
        logging.error(f"Error getting imagesets in folder {folder_name}: {e}", exc_info=True)
        return []


def delete_abandoned_folders(folder_name: str, imagesets: List[str]) -> List[str]:
    """
    Delete folders that have no image files.
    
    Args:
        folder_name: Path to the parent folder
        imagesets: List of imageset names
        
    Returns:
        Updated list of imagesets
    """
    logging.info(f"Checking for abandoned folders in {folder_name}")
    imagesets_to_delete = []
    
    try:
        for imageset in imagesets:
            imageset_folder = os.path.join(folder_name, imageset)
            
            # Skip if not a directory
            if not os.path.isdir(imageset_folder):
                continue
                
            # Check if folder has any image files
            has_images = False
            for file_name in os.listdir(imageset_folder):
                file_path = os.path.join(imageset_folder, file_name)
                if os.path.isfile(file_path) and is_image_file(file_path):
                    has_images = True
                    break
                    
            # If no images found, mark for deletion
            if not has_images:
                imagesets_to_delete.append(imageset)
                
        # Delete abandoned folders
        for imageset in imagesets_to_delete:
            folder_to_delete = os.path.join(folder_name, imageset)
            if delete_folder(folder_to_delete):
                logging.info(f"Deleted abandoned folder: {imageset}")
                
        # Remove deleted imagesets from list
        remaining_imagesets = [img for img in imagesets if img not in imagesets_to_delete]
        
        if imagesets_to_delete:
            logging.info(f"Deleted {len(imagesets_to_delete)} abandoned folders")
            
        return remaining_imagesets
        
    except Exception as e:
        logging.error(f"Error deleting abandoned folders in {folder_name}: {e}", exc_info=True)
        return imagesets


def tag_orig_file(folder_name: str, imagesets: List[str], config: Config) -> None:
    """
    Ensure each imageset folder has an original file tagged.
    
    Args:
        folder_name: Path to the parent folder
        imagesets: List of imageset names
        config: Application configuration
    """
    logging.info(f"Tagging original files in {folder_name}")
    
    try:
        for imageset in imagesets:
            imageset_folder = os.path.join(folder_name, imageset)
            
            # Skip if not a directory
            if not os.path.isdir(imageset_folder):
                continue
                
            # Check if there's already an orig file
            orig_file = find_file_with_tag(imageset_folder, "orig")
            if orig_file:
                logging.debug(f"Original file already exists for {imageset}: {os.path.basename(orig_file)}")
                continue
                
            # Get all image files in the folder
            image_files = []
            for file_name in os.listdir(imageset_folder):
                file_path = os.path.join(imageset_folder, file_name)
                if os.path.isfile(file_path) and is_image_file(file_path):
                    image_files.append(file_path)
                    
            if not image_files:
                logging.warning(f"No image files found in {imageset_folder}")
                continue
                
            # If only one image file, tag it as orig
            if len(image_files) == 1:
                file_path = image_files[0]
                base_name, ext = os.path.splitext(os.path.basename(file_path))
                new_name = f"{base_name}_orig{ext}"
                new_path = os.path.join(imageset_folder, new_name)
                
                try:
                    os.rename(file_path, new_path)
                    logging.info(f"Tagged single file as orig: {new_name}")
                except Exception as e:
                    logging.error(f"Error renaming file {file_path}: {e}", exc_info=True)
                    
            # If multiple files, find one without tags
            else:
                # Get file tags from config with underscore prefix
                file_tags = [f"_{tag}" for tag in config.get_file_tags()]
                
                for file_path in image_files:
                    file_name = os.path.basename(file_path)
                    has_tag = any(tag in file_name for tag in file_tags)
                    
                    if not has_tag:
                        base_name, ext = os.path.splitext(file_name)
                        new_name = f"{base_name}_orig{ext}"
                        new_path = os.path.join(imageset_folder, new_name)
                        
                        try:
                            os.rename(file_path, new_path)
                            logging.info(f"Tagged file as orig: {new_name}")
                            break
                        except Exception as e:
                            logging.error(f"Error renaming file {file_path}: {e}", exc_info=True)
                
    except Exception as e:
        logging.error(f"Error tagging original files in {folder_name}: {e}", exc_info=True)


def folder_scan(args: Dict[str, Any], config: Config) -> bool:
    """
    Scan a folder for imagesets and process them.
    
    Args:
        args: Command arguments
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        folder_name = args.get("folder_name")
        if not folder_name:
            logging.error("No folder name provided")
            return False
            
        # Ensure folder exists
        if not os.path.exists(folder_name):
            logging.error(f"Folder does not exist: {folder_name}")
            return False
            
        logging.info(f"Scanning folder: {folder_name}")
        
        # Get imagesets in folder
        imagesets = get_imagesets_in_folder(folder_name, config)
        
        # Delete abandoned folders
        imagesets = delete_abandoned_folders(folder_name, imagesets)
        
        # Tag original files
        tag_orig_file(folder_name, imagesets, config)
        
        # Extract EXIF data from original images
        extract_exif_data_from_orig_images(folder_name, imagesets, config)
        
        logging.info(f"Folder scan completed for {folder_name}")
        return True
        
    except Exception as e:
        logging.error(f"Error scanning folder: {e}", exc_info=True)
        return False
