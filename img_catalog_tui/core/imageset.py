"""
Image set operations for the Image Catalog TUI application.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from img_catalog_tui.config import Config
from img_catalog_tui.core.metadata import load_imageset_metadata, save_imageset_metadata
from img_catalog_tui.utils.file_utils import find_file_with_tag

# ------- Data Models --------------------

class ImagesetFile(BaseModel):
    """Each File in a Dataset."""
    title: str = Field(
        description="SEO-friendly title for the product post.",
        example=("Transform your space with this charming vintage-style sloth gentleman "
                 "portrait on premium canvas! This delightfully quirky art print features "
                 "a dapper sloth dressed in Victorian-era formal attire, complete with "
                 "waistcoat and cravat.")
    )
    description: str = Field(
        description="SEO-friendly description tuned for the target marketplace."
    )
    tags: list[str] = Field(
        description="15-20 SEO-friendly tags (mix of short/long tail)."
    )



class Imageset():
    
    def __init__(
        self,
        config: Config,
        folder_name: str,
        imageset_name: str
    ):
        
        self.config = config
        self.folder_name = folder_name
        self.imageset_name = imageset_name
        self.imageset_folder = self._get_imageset_folder()
        self.files = self._get_imageset_files() # dict{filename: dict{fullpath, ext, tags}}
        
        def _get_imageset_folder(self):
            if not os.path.exists(self.folder_name):
                logging.error(f"Base folder not found: {self.folder_name}")
                raise(f"Base folder not found: {self.folder_name}")

            imageset_folder = os.path.join(self.folder_name, self.imageset_name)            
            
            if not os.path.exists(imageset_folder):
                logging.error(f"Imageset Folder does not exist: {imageset_folder}")
                raise(f"Imageset Folder does not exist: {imageset_folder}")
            
            return(imageset_folder)
        
        def _get_imageset_files(self):
            
            files = {}
            
            tags = self.config.file_tags
            
            imageset_folder = os.path.join(self.folder_name, self.imageset_name)
            
            try:
                if not os.path.exists(imageset_folder):
                    logging.error(f"Imageset folder does not exist: {imageset_folder}")
                    raise(f"Imageset folder does not exist: {imageset_folder}")
                    
                # Get all files in the imageset folder
                for file_name in os.listdir(imageset_folder):
                    file_path = os.path.join(imageset_folder, file_name)
                    file_ext = os.path.splitext(file_name)[1] 
                    
                    # Skip directories
                    if not os.path.isfile(file_path):
                        continue
                        
                    # Check for tags
                    file_tags = []
                    for tag in tags:
                        if f"_{tag}_" in file_name or f"_{tag}." in file_name:
                            file_tags.append(tag)
                            
                    # load the file into the files dict
                    files[file_name] = {"fullpath": file_path, "ext": file_ext, "tags": file_tags}
                            
                return files
                
            except Exception as e:
                logging.error(f"Error getting files for imageset {self.imageset_name}: {e}", exc_info=True)
                raise(f"Error getting files for imageset {self.imageset_name}: {e}")


                
                

def get_imageset_files(folder_name: str, imageset: str) -> Dict[str, str]:
    """
    Get all files for an imageset with their tags.
    
    Args:
        folder_name: Path to the parent folder
        imageset: Name of the imageset
        
    Returns:
        Dictionary mapping tags to file paths
    """
    result = {}
    imageset_folder = os.path.join(folder_name, imageset)
    
    try:
        if not os.path.exists(imageset_folder):
            logging.error(f"Imageset folder does not exist: {imageset_folder}")
            return result
            
        # Get all files in the imageset folder
        for file_name in os.listdir(imageset_folder):
            file_path = os.path.join(imageset_folder, file_name)
            
            # Skip directories
            if not os.path.isfile(file_path):
                continue
                
            # Check for tags
            tags = ["orig", "thumb", "v2", "v3", "v4", "v5", "up2", "up3", "up4", "up6"]
            for tag in tags:
                tag_pattern = f"_{tag}"
                if tag_pattern in file_name:
                    result[tag] = file_path
                    break
                    
        return result
        
    except Exception as e:
        logging.error(f"Error getting files for imageset {imageset}: {e}", exc_info=True)
        return result


def generate_html_report(folder_name: str, imageset: str, config: Config) -> bool:
    """
    Generate an HTML report for an imageset.
    
    Args:
        folder_name: Path to the parent folder
        imageset: Name of the imageset
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        imageset_folder = os.path.join(folder_name, imageset)
        
        # Check if imageset folder exists
        if not os.path.exists(imageset_folder):
            logging.error(f"Imageset folder does not exist: {imageset_folder}")
            return False
            
        # Load metadata
        metadata = load_imageset_metadata(folder_name, imageset)
        if not metadata:
            logging.error(f"No metadata found for imageset: {imageset}")
            return False
            
        # Get imageset files
        files = get_imageset_files(folder_name, imageset)
        
        # Generate HTML file path
        html_file = os.path.join(imageset_folder, f"{imageset}.html")
        
        # Generate HTML content
        html_content = generate_html_content(imageset, metadata, files)
        
        # Write HTML file
        with open(html_file, "w") as f:
            f.write(html_content)
            
        logging.info(f"Generated HTML report for {imageset}: {html_file}")
        return True
        
    except Exception as e:
        logging.error(f"Error generating HTML report for {imageset}: {e}", exc_info=True)
        return False


def generate_html_content(imageset: str, metadata: Dict[str, Any], files: Dict[str, str]) -> str:
    """
    Generate HTML content for an imageset report.
    
    Args:
        imageset: Name of the imageset
        metadata: Dictionary containing metadata
        files: Dictionary mapping tags to file paths
        
    Returns:
        HTML content as a string
    """
    # Get source-specific metadata
    source = metadata.get("source", "unknown")
    source_data = metadata.get(source, {})
    
    # Get original image file
    orig_file = os.path.basename(files.get("orig", ""))
    
    # Start HTML content
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Imageset: {imageset}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .metadata {{ margin: 20px 0; }}
        .metadata h2 {{ color: #555; }}
        .metadata table {{ border-collapse: collapse; width: 100%; }}
        .metadata th, .metadata td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .metadata th {{ background-color: #f2f2f2; }}
        .images {{ display: flex; flex-wrap: wrap; gap: 20px; }}
        .image-container {{ margin-bottom: 20px; }}
        .image-container img {{ max-width: 300px; max-height: 300px; }}
        .image-container p {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Imageset: {imageset}</h1>
    
    <div class="metadata">
        <h2>Metadata</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>Source</td><td>{source}</td></tr>
"""
    
    # Add review metadata if available
    if "review" in metadata:
        review = metadata["review"]
        html += f'            <tr><td>Review Needs</td><td>{review.get("needs", "")}</td></tr>\n'
    
    # Add business metadata if available
    if "biz" in metadata:
        biz = metadata["biz"]
        html += f'            <tr><td>Good For</td><td>{biz.get("good_for", "")}</td></tr>\n'
        html += f'            <tr><td>Posted To</td><td>{biz.get("posted_to", "")}</td></tr>\n'
    
    # Add interview metadata if available
    if "interview" in metadata:
        interview = metadata["interview"]
        html += f'            <tr><td>Interview Date</td><td>{interview.get("interview_date", "")}</td></tr>\n'
        html += f'            <tr><td>Template Used</td><td>{interview.get("template_used", "")}</td></tr>\n'
        html += f'            <tr><td>Title</td><td>{interview.get("title", "")}</td></tr>\n'
        html += f'            <tr><td>Description</td><td>{interview.get("description", "")}</td></tr>\n'
    
    # Add source-specific metadata
    if source == "midjourney" and source_data:
        html += f'            <tr><td>Prompt</td><td>{source_data.get("prompt", "")}</td></tr>\n'
        html += f'            <tr><td>Job ID</td><td>{source_data.get("jobid", "")}</td></tr>\n'
    elif source == "fooocus" and source_data:
        html += f'            <tr><td>Prompt</td><td>{source_data.get("Prompt", "")}</td></tr>\n'
        html += f'            <tr><td>Negative Prompt</td><td>{source_data.get("Negative Prompt", "")}</td></tr>\n'
        html += f'            <tr><td>Resolution</td><td>{source_data.get("Resolution", "")}</td></tr>\n'
        html += f'            <tr><td>Model</td><td>{source_data.get("Base Model", "")}</td></tr>\n'
    
    # Close metadata table
    html += """        </table>
    </div>
    
    <div class="images">
"""
    
    # Add images
    for tag, file_path in files.items():
        file_name = os.path.basename(file_path)
        html += f"""        <div class="image-container">
            <img src="{file_name}" alt="{tag}">
            <p>{file_name}</p>
            <p>Tag: {tag}</p>
        </div>
"""
    
    # Close HTML
    html += """    </div>
</body>
</html>
"""
    
    return html


def process_interview(folder_name: str, imageset: str, template_name: str, config: Config) -> bool:
    """
    Process an interview for an imageset.
    
    Args:
        folder_name: Path to the parent folder
        imageset: Name of the imageset
        template_name: Name of the interview template
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load template
        templates_dir = config.get("paths.templates_dir", "./config/templates")
        template_file = os.path.join(templates_dir, f"{template_name}.tmpl")
        
        if not os.path.exists(template_file):
            logging.error(f"Template file not found: {template_file}")
            return False
            
        # Load template content
        with open(template_file, "r") as f:
            template_content = f.read()
            
        # Load imageset metadata
        metadata = load_imageset_metadata(folder_name, imageset)
        if not metadata:
            metadata = {"imageset": imageset}
            
        # Ensure interview section exists
        if "interview" not in metadata:
            metadata["interview"] = {}
            
        # Update interview metadata
        metadata["interview"]["template_used"] = template_name
        
        # TODO: Implement interactive interview process
        # This would be part of the TUI implementation
        
        # For now, just save the updated metadata
        if save_imageset_metadata(folder_name, imageset, metadata):
            logging.info(f"Interview template {template_name} applied to {imageset}")
            return True
        return False
        
    except Exception as e:
        logging.error(f"Error processing interview for {imageset}: {e}", exc_info=True)
        return False
