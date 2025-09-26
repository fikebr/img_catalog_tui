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
