import logging
import os
from flask import jsonify, render_template, send_file, abort

from img_catalog_tui.config import Config

from img_catalog_tui.core.folders import Folders
from img_catalog_tui.core.folder import ImagesetFolder

config = Config()

def index() -> str:
    try:
        return render_template('index.html', title="Image Catalog TUI", message="Welcome to the Image Catalog!")
    except Exception as e:
        logging.error(f"Error in index endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


def folders() -> str:
    """Return the folders management HTML page."""
    try:
        return render_template('folders.html', title="Folder Management")
    except Exception as e:
        logging.error(f"Error in folders endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def reviews(foldername: str, review_type: str = "new") -> str:
    """Return the reviews HTML page for a specific folder and review type."""
    try:
        logging.debug(f"reviews endpoint: folder={foldername}, review_type={review_type}")
        
        # Validate foldername exists in Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return render_template('reviews.html', 
                                 title="Image Catalog Review", 
                                 foldername=foldername,
                                 review_type=review_type,
                                 imagesets={},
                                 error=f"Folder '{foldername}' not found"), 404
        
        # Get imagesets based on review_type
        imagesets = _get_imagesets_for_review_type(foldername, review_type, folders_obj)
        
        return render_template('reviews.html', 
                             title="Image Catalog Review", 
                             foldername=foldername,
                             review_type=review_type,
                             imagesets=imagesets)
    except Exception as e:
        logging.error(f"Error in reviews endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def _get_imagesets_for_review_type(foldername: str, review_type: str, folders_obj: Folders) -> dict:
    """Get filtered imagesets based on review_type."""
    try:
        folder_path = folders_obj.folders[foldername]
        folder_obj = ImagesetFolder(config=config, foldername=folder_path)
        
        # Handle different review types
        if review_type == "new":
            return folder_obj.review_new()
        else:
            # Future review types will be implemented here
            # For now, return empty dict for unsupported types
            logging.warning(f"Unsupported review_type: {review_type}")
            return {}
            
    except Exception as e:
        logging.error(f"Error getting imagesets for review_type {review_type}: {e}", exc_info=True)
        return {}



def folder(foldername: str) -> str:
    """Return the folder HTML page for a specific folder."""
    try:
        logging.debug(f"folder endpoint: folder={foldername}")
        
        # Validate foldername exists in Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return render_template('folder.html', 
                                 title="Folder Details", 
                                 foldername=foldername,
                                 folder_data={},
                                 error=f"Folder '{foldername}' not found"), 404
        
        # Get folder data with detailed imageset information
        folder_path = folders_obj.folders[foldername]
        folder_obj = ImagesetFolder(config=config, foldername=folder_path)
        
        # Create enhanced folder data with imageset details
        folder_data = {
            'foldername': folder_obj.foldername,
            'imageset_count': len(folder_obj.imagesets),
            'imagesets': {}
        }
        
        # Add detailed imageset information
        for imageset_name, imageset_obj in folder_obj.imagesets.items():
            folder_data['imagesets'][imageset_name] = imageset_obj.to_dict()
        
        return render_template('folder.html', 
                             title=f"Folder: {foldername}", 
                             foldername=foldername,
                             folder_data=folder_data)
                             
    except Exception as e:
        logging.error(f"Error in folder endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def health() -> tuple[dict, int]:
    """Return health status of the application."""
    try:
        logging.info("Health check endpoint accessed")
        return {"status": "healthy"}, 200
    except Exception as e:
        logging.error(f"Error in health endpoint: {e}")
        return {"status": "error", "message": str(e)}, 500


def serve_image(foldername: str, imageset_name: str, filename: str):
    """Serve image files from their original filesystem locations."""
    try:
        # Get folder path from Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            abort(404)
        
        folder_path = folders_obj.folders[foldername]
        
        # Construct full image path
        image_path = os.path.join(folder_path, imageset_name, filename)
        
        # Security check: ensure the path is within the allowed folder
        if not os.path.abspath(image_path).startswith(os.path.abspath(folder_path)):
            logging.warning(f"Security violation: path traversal attempt for {foldername}/{imageset_name}/{filename}")
            abort(403)
        
        # Check if file exists
        if not os.path.exists(image_path):
            logging.warning(f"Image file not found: {image_path}")
            abort(404)
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(image_path):
            logging.warning(f"Path is not a file: {image_path}")
            abort(404)
        
        logging.debug(f"Serving image: {image_path}")
        return send_file(image_path)
        
    except Exception as e:
        logging.error(f"Error serving image {foldername}/{imageset_name}/{filename}: {e}", exc_info=True)
        abort(500)


def batch_update_form(foldername: str) -> str:
    """Return the batch update form HTML page for a specific folder."""
    try:
        logging.debug(f"batch_update_form endpoint: folder={foldername}")
        
        # Validate foldername exists in Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return render_template('batch_update.html', 
                                 title="Batch Update", 
                                 foldername=foldername,
                                 folder_data={},
                                 config_options={},
                                 error=f"Folder '{foldername}' not found"), 404
        
        # Get folder data with imagesets
        folder_path = folders_obj.folders[foldername]
        folder_obj = ImagesetFolder(config=config, foldername=folder_path)
        
        # Create folder data for the template
        folder_data = {
            'foldername': folder_obj.foldername,
            'imageset_count': len(folder_obj.imagesets),
            'imagesets': {}
        }
        
        # Add imageset information with basic details
        for imageset_name, imageset_obj in folder_obj.imagesets.items():
            folder_data['imagesets'][imageset_name] = {
                'name': imageset_name,
                'status': imageset_obj.status,
                'edits': imageset_obj.edits,
                'needs': imageset_obj.needs,
                'good_for': imageset_obj.good_for,
                'posted_to': imageset_obj.posted_to
            }
        
        # Get configuration options for form dropdowns
        config_options = {
            'status': config.config_data.get('status', []),
            'edits': config.config_data.get('edits', []),
            'needs': config.config_data.get('needs', []),
            'good_for': config.config_data.get('good_for', []),
            'posted_to': config.config_data.get('posted_to', [])
        }
        
        return render_template('batch_update.html', 
                             title=f"Batch Update: {foldername}", 
                             foldername=foldername,
                             folder_data=folder_data,
                             config_options=config_options)
                             
    except Exception as e:
        logging.error(f"Error in batch_update_form endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500