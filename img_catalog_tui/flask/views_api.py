import logging
from flask import jsonify, request

from img_catalog_tui.config import Config

from img_catalog_tui.core.folders import Folders
from img_catalog_tui.core.folder import ImagesetFolder
from img_catalog_tui.core.imageset import Imageset

config = Config()


    

def folders():
    """Return list of folders as JSON."""
    try:
        folders_obj = Folders()
        return jsonify(folders_obj.folders)
    except Exception as e:
        logging.error(f"Error getting folders: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    
# TODO: implement an api route that takes a folder, a list of imagesets, a stat_field (status, edits, needs), a value and and an action (set, remove, add) then performs that action on each of the imagesets


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
    
def review_new(foldername: str):
    try:
        folders_obj = Folders()
        folder_path = folders_obj.folders[foldername]
        # create a folder object for the foldername
        folder_obj = ImagesetFolder(config=config, foldername=folder_path)
        
        # return a jsonify folder.to_dict()
        return jsonify(folder_obj.review_new())
        
    except FileNotFoundError as e:
        logging.error(f"Folder not found: {e}")
        return jsonify({"error": f"Folder not found: {foldername}"}), 404
    except Exception as e:
        logging.error(f"Error processing folder {foldername}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# TODO: review
    

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


def folders_add(folder_path: str):
    """Add a new folder to the collection."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
            
        # Add folder using Folders class
        folders_obj = Folders()
        success = folders_obj.add(folder_path)
        
        if success:
            logging.info(f"Successfully added folder: {folder_path}")
            return jsonify({"message": "Folder added successfully", "folder_path": folder_path}), 201
        else:
            return jsonify({"error": "Failed to add folder"}), 400
            
    except Exception as e:
        logging.error(f"Error adding folder: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def folders_delete(foldername: str):
    """Remove a folder from the collection."""
    try:
        # Validate request method
        if request.method != 'DELETE':
            return jsonify({"error": "Method not allowed"}), 405
            
        # Delete folder using Folders class
        folders_obj = Folders()
        success = folders_obj.delete(foldername)
        
        if success:
            logging.info(f"Successfully deleted folder: {foldername}")
            return jsonify({"message": "Folder deleted successfully", "folder_name": foldername}), 200
        else:
            return jsonify({"error": f"Folder '{foldername}' not found or failed to delete"}), 404
            
    except Exception as e:
        logging.error(f"Error deleting folder {foldername}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def favicon():
    """Return a simple SVG favicon."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
        <rect width="16" height="16" fill="#2563eb"/>
        <rect x="2" y="2" width="12" height="12" fill="none" stroke="#ffffff" stroke-width="1"/>
        <circle cx="8" cy="8" r="3" fill="#ffffff"/>
    </svg>'''
    return svg, 200, {'Content-Type': 'image/svg+xml'}

