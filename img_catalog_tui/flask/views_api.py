import logging
from flask import jsonify, request

from img_catalog_tui.config import Config

from img_catalog_tui.core.folders import Folders
from img_catalog_tui.core.folder import ImagesetFolder
from img_catalog_tui.core.imageset import Imageset
from img_catalog_tui.core.imageset_batch_update import ImagesetBatch

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
        # Get full folder path from registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return jsonify({"error": f"Folder '{foldername}' not found"}), 404
        
        folder_path = folders_obj.folders[foldername]
        
        # Create imageset object directly with full folder path
        imageset_obj = Imageset(config=config, folder_name=folder_path, imageset_name=imageset)
        
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


def batch_update(foldername: str):
    """Batch update imagesets with specified field and value."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = ['update_type', 'value', 'imagesets']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        update_type = data['update_type']
        value = data['value']
        imagesets = data['imagesets']
        append = data.get('append', False)  # Optional parameter, defaults to False
        
        # Validate imagesets is a list
        if not isinstance(imagesets, list):
            return jsonify({"error": "imagesets must be a list"}), 400
        
        if not imagesets:
            return jsonify({"error": "imagesets list cannot be empty"}), 400
        
        # Get folder path from Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return jsonify({"error": f"Folder '{foldername}' not found"}), 404
        
        folder_path = folders_obj.folders[foldername]
        
        # Create ImagesetBatch object and perform update
        batch_updater = ImagesetBatch(
            config=config,
            folder=folder_path,
            update_type=update_type,
            imagesets=imagesets,
            value=value,
            append=append
        )
        
        error_imagesets = batch_updater.update_now()
        
        # Prepare response
        total_imagesets = len(imagesets)
        successful_count = total_imagesets - len(error_imagesets)
        
        response_data = {
            "message": "Batch update completed",
            "total_imagesets": total_imagesets,
            "successful_count": successful_count,
            "failed_count": len(error_imagesets),
            "failed_imagesets": error_imagesets,
            "update_type": update_type,
            "value": value
        }
        
        # Return appropriate status code based on results
        if error_imagesets:
            if successful_count == 0:
                # All failed
                logging.error(f"Batch update failed for all imagesets in folder '{foldername}'")
                return jsonify(response_data), 500
            else:
                # Partial success
                logging.warning(f"Batch update partially failed for folder '{foldername}': {len(error_imagesets)} failures")
                return jsonify(response_data), 207  # Multi-Status
        else:
            # All successful
            logging.info(f"Batch update successful for all {total_imagesets} imagesets in folder '{foldername}'")
            return jsonify(response_data), 200
        
    except ValueError as e:
        logging.error(f"Validation error in batch update: {e}")
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        logging.error(f"File not found in batch update: {e}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logging.error(f"Error in batch update for folder {foldername}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def imageset_update(foldername: str, imageset: str):
    """Update imageset metadata fields."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        # Get form data from request
        data = request.form
        if not data:
            return jsonify({"error": "No form data provided"}), 400
        
        # Validate foldername exists in Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return jsonify({"error": f"Folder '{foldername}' not found"}), 404
        
        folder_path = folders_obj.folders[foldername]
        
        # Create folder object and validate imageset exists
        folder_obj = ImagesetFolder(config=config, foldername=folder_path)
        if imageset not in folder_obj.imagesets:
            logging.warning(f"Imageset '{imageset}' not found in folder '{foldername}'")
            return jsonify({"error": f"Imageset '{imageset}' not found in folder '{foldername}'"}), 404
        
        # Get the imageset object
        imageset_obj = folder_obj.imagesets[imageset]
        
        # Track which fields were updated
        updated_fields = []
        
        # Update each field if provided
        if 'status' in data:
            try:
                imageset_obj.status = data['status']
                updated_fields.append('status')
                logging.info(f"Updated status for {imageset}: {data['status']}")
            except ValueError as e:
                return jsonify({"error": f"Invalid status value: {str(e)}"}), 400
        
        if 'edits' in data:
            try:
                imageset_obj.edits = data['edits']
                updated_fields.append('edits')
                logging.info(f"Updated edits for {imageset}: {data['edits']}")
            except ValueError as e:
                return jsonify({"error": f"Invalid edits value: {str(e)}"}), 400
        
        if 'needs' in data:
            try:
                imageset_obj.needs = data['needs']
                updated_fields.append('needs')
                logging.info(f"Updated needs for {imageset}: {data['needs']}")
            except ValueError as e:
                return jsonify({"error": f"Invalid needs value: {str(e)}"}), 400
        
        if 'good_for' in data:
            try:
                imageset_obj.good_for = data['good_for']
                updated_fields.append('good_for')
                logging.info(f"Updated good_for for {imageset}: {data['good_for']}")
            except ValueError as e:
                return jsonify({"error": f"Invalid good_for value: {str(e)}"}), 400
        
        if 'posted_to' in data:
            try:
                imageset_obj.posted_to = data['posted_to']
                updated_fields.append('posted_to')
                logging.info(f"Updated posted_to for {imageset}: {data['posted_to']}")
            except ValueError as e:
                return jsonify({"error": f"Invalid posted_to value: {str(e)}"}), 400
        
        # Return success response
        response_data = {
            "message": "Imageset updated successfully",
            "imageset": imageset,
            "folder": foldername,
            "updated_fields": updated_fields
        }
        
        logging.info(f"Successfully updated imageset {imageset} in folder {foldername}: {', '.join(updated_fields)}")
        return jsonify(response_data), 200
        
    except FileNotFoundError as e:
        logging.error(f"File not found in imageset update: {e}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logging.error(f"Error updating imageset {imageset} in folder {foldername}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def favicon():
    """Return a simple SVG favicon."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
        <rect width="16" height="16" fill="#2563eb"/>
        <rect x="2" y="2" width="12" height="12" fill="none" stroke="#ffffff" stroke-width="1"/>
        <circle cx="8" cy="8" r="3" fill="#ffffff"/>
    </svg>'''
    return svg, 200, {'Content-Type': 'image/svg+xml'}

