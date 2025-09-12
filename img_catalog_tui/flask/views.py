import logging
from flask import jsonify, render_template

from img_catalog_tui.config import Config

from img_catalog_tui.core.folders import Folders
from img_catalog_tui.core.folder import ImagesetFolder
from img_catalog_tui.core.imageset import Imageset

config = Config()
config.load()


def hello() -> str:
    """Return a simple hello message."""
    try:
        logging.info("Hello endpoint accessed")
        return render_template('index.html', title="Image Catalog TUI", message="Welcome to the Image Catalog!")
    except Exception as e:
        logging.error(f"Error in hello endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


def health() -> tuple[dict, int]:
    """Return health status of the application."""
    try:
        logging.info("Health check endpoint accessed")
        return {"status": "healthy"}, 200
    except Exception as e:
        logging.error(f"Error in health endpoint: {e}")
        return {"status": "error", "message": str(e)}, 500
    

def folders():
    """Return list of folders as JSON."""
    try:
        folders_obj = Folders()
        return jsonify(folders_obj.folders)
    except Exception as e:
        logging.error(f"Error getting folders: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def folder(foldername: str):
    """Return folder information as JSON."""
    try:
        folders_obj = Folders()
        folder_path = folders_obj.folders[foldername]
        # create a folder object for the foldername
        folder_obj = ImagesetFolder(config=config, foldername=folder_path)
        
        # return a jsonify folder.to_dict()
        return jsonify(folder_obj.to_dict())
        
    except FileNotFoundError as e:
        logging.error(f"Folder not found: {e}")
        return jsonify({"error": f"Folder not found: {foldername}"}), 404
    except Exception as e:
        logging.error(f"Error processing folder {foldername}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    

def imageset(foldername: str, imageset: str):
    """Return imageset information as JSON."""
    try:
        # Test if folder exists in Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return jsonify({"error": f"Folder '{foldername}' not found"}), 404
        
        folder_path = folders_obj.folders[foldername]
        
        # Test if folder path exists on filesystem and create folder object
        folder_obj = ImagesetFolder(config=config, foldername=folder_path)
        
        # Test if imageset exists in folder
        if imageset not in folder_obj.imagesets:
            logging.warning(f"Imageset '{imageset}' not found in folder '{foldername}'")
            return jsonify({"error": f"Imageset '{imageset}' not found in folder '{foldername}'"}), 404
            
        imageset_obj = folder_obj.imagesets[imageset]
        
        return jsonify(imageset_obj.to_dict())
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        return jsonify({"error": f"Folder path not found: {foldername}"}), 404
    except Exception as e:
        logging.error(f"Error processing imageset {imageset} in folder {foldername}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def favicon():
    """Return a simple SVG favicon."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
        <rect width="16" height="16" fill="#2563eb"/>
        <rect x="2" y="2" width="12" height="12" fill="none" stroke="#ffffff" stroke-width="1"/>
        <circle cx="8" cy="8" r="3" fill="#ffffff"/>
    </svg>'''
    return svg, 200, {'Content-Type': 'image/svg+xml'}

