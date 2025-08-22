"""
Folder indexing functionality for the Image Catalog TUI application.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

import jinja2

from img_catalog_tui.config import Config
from img_catalog_tui.utils.file_utils import find_file_with_tag


def build_folder_index(folder_name: str, config: Config) -> Dict[str, Any]:
    """
    Build an index of imagesets in a folder.
    
    Args:
        folder_name: Path to the folder to index
        config: Application configuration
        
    Returns:
        Dictionary containing index data
    """
    logging.info(f"Building index for folder: {folder_name}")
    index = {
        "folder_name": folder_name,
        "timestamp": datetime.now().isoformat(),
        "imagesets": {}
    }
    
    try:
        # Check if folder exists
        if not os.path.exists(folder_name):
            logging.error(f"Folder does not exist: {folder_name}")
            return index
            
        # Scan folder for imagesets
        for item in os.listdir(folder_name):
            item_path = os.path.join(folder_name, item)
            
            # Skip items starting with underscore or non-directories
            if item.startswith("_") or not os.path.isdir(item_path):
                continue
                
            # Found an imageset folder
            imageset = item
            index["imagesets"][imageset] = {}
            
            # Find original image
            orig_file = find_file_with_tag(item_path, "orig")
            logging.debug(f"Orig file: {orig_file}")
            if orig_file:
                # Store just the filename of the original image
                filename = os.path.basename(orig_file)
                logging.debug(f"Filename: {filename}")
                index["imagesets"][imageset]["orig"] = filename
            
        logging.info(f"Index built with {len(index['imagesets'])} imagesets")
        return index
        
    except Exception as e:
        logging.error(f"Error building folder index: {e}", exc_info=True)
        return index


def save_index_json(folder_name: str, index: Dict[str, Any]) -> bool:
    """
    Save index data to a JSON file.
    
    Args:
        folder_name: Path to the folder
        index: Index data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Save index to JSON file directly in the folder
        index_file = os.path.join(folder_name, "index.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
            
        logging.info(f"Index saved to {index_file}")
        return True
        
    except Exception as e:
        logging.error(f"Error saving index JSON: {e}", exc_info=True)
        return False


def generate_html_index(folder_name: str, index: Dict[str, Any], config: Config) -> bool:
    """
    Generate HTML index from template.
    
    Args:
        folder_name: Path to the folder
        index: Index data
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get template path
        template_path = os.path.join(config.config_dir, "templates", "index_review.html")
        logging.info(f"Template path: {template_path}")
        
        # Check if template exists
        if not os.path.exists(template_path):
            logging.error(f"Template not found: {template_path}")
            return False
        
        # Set up Jinja environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(template_path)),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        try:
            # Load template
            template = env.get_template(os.path.basename(template_path))
            
            # Render template
            html_content = template.render(
                index=index,
                folder_name=folder_name,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Save HTML file directly in the folder
            html_file = os.path.join(folder_name, "index.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logging.info(f"HTML index generated: {html_file}")
            return True
            
        except jinja2.exceptions.TemplateError as e:
            logging.error(f"Template error: {e}", exc_info=True)
            return False
            
    except Exception as e:
        logging.error(f"Error generating HTML index: {e}", exc_info=True)
        return False





def folder_index(args: Dict[str, Any], config: Config) -> bool:
    """
    Generate index for a folder.
    
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
            
        logging.info(f"Generating index for folder: {folder_name}")
        
        # Build folder index
        index = build_folder_index(folder_name, config)
        
        # Save index to JSON file
        if not save_index_json(folder_name, index):
            logging.error("Failed to save index JSON")
            return False
            
        # Generate HTML index
        if not generate_html_index(folder_name, index, config):
            logging.error("Failed to generate HTML index")
            return False
            
        logging.info(f"Folder index generated successfully for {folder_name}")
        return True
        
    except Exception as e:
        logging.error(f"Error generating folder index: {e}", exc_info=True)
        return False
