import logging
import os
from flask import jsonify, request

from img_catalog_tui.config import Config

from img_catalog_tui.core.folders import Folders
from img_catalog_tui.core.folder import ImagesetFolder
from img_catalog_tui.core.imageset import Imageset
from img_catalog_tui.core.imageset_batch_update import ImagesetBatch

config = Config()


def interview():
    """Execute an AI interview on the cover image of an imageset."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        if 'foldername' not in data:
            return jsonify({"error": "Missing required field: foldername"}), 400
        if 'imagesetname' not in data:
            return jsonify({"error": "Missing required field: imagesetname"}), 400
        
        foldername = data['foldername']
        imagesetname = data['imagesetname']
        
        # Get folder path using lightweight utility function
        from img_catalog_tui.utils.folder_utils import get_folder_path
        folderpath = get_folder_path(foldername)
        
        if not folderpath:
            return jsonify({"error": f"Folder '{foldername}' not found in registry"}), 404
        
        imageset_path = os.path.join(folderpath, imagesetname)
        
        # Error if imageset_path does not exist
        if not os.path.exists(imageset_path):
            logging.error(f"Imageset path does not exist: {imageset_path}")
            return jsonify({"error": f"Imageset '{imagesetname}' not found in folder '{folderpath}'"}), 404
        
        # Get an imageset object
        imageset_obj = Imageset(config=config, folder_name=folderpath, imageset_name=imagesetname)
        
        # Get the full path to the cover image for the imageset
        cover_image_path = imageset_obj.cover_image
        if not cover_image_path:
            logging.error(f"No cover image found for imageset: {imagesetname}")
            return jsonify({"error": f"No cover image found for imageset '{imagesetname}'"}), 404
        
        # Create an interview object for the cover_image
        from img_catalog_tui.core.imageset_interview import Interview
        interview_obj = Interview(config=config, image_file=cover_image_path)
        
        # Execute interview.interview_image()
        interview_obj.interview_image()
        
        # Return success response with interview results
        response_data = {
            "success": True,
            "message": "Interview completed successfully",
            "imageset": imagesetname,
            "folder": foldername,
            "cover_image": cover_image_path,
            "interview_response": interview_obj.interview_response,
            "interview_parsed": interview_obj.interview_parsed
        }
        
        logging.info(f"Successfully completed interview for imageset {imagesetname} in folder {folderpath}")
        return jsonify(response_data), 200
        
    except FileNotFoundError as e:
        logging.error(f"File not found in interview: {e}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logging.error(f"Error during interview for imageset {imagesetname} in folder {folderpath}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

def folders():
    """Return list of folders as JSON."""
    try:
        folders_obj = Folders(config=config)
        return jsonify(folders_obj.folders)
    except Exception as e:
        logging.error(f"Error getting folders: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    

def folder(foldername: str):
    """Return folder information as JSON."""
    try:
        folders_obj = Folders(config=config)
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
        folders_obj = Folders(config=config)
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


def imageset(foldername: str, imageset: str):
    """Return imageset information as JSON."""
    try:
        # Get full folder path from registry
        folders_obj = Folders(config=config)
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
        folders_obj = Folders(config=config)
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
        folders_obj = Folders(config=config)
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
        folders_obj = Folders(config=config)
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
        folders_obj = Folders(config=config)
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


def create_thumbnail(foldername: str, imageset_name: str, filename: str):
    """Create a thumbnail for an image file."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        # Get folder path from Folders registry
        folders_obj = Folders(config=config)
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return jsonify({"error": f"Folder '{foldername}' not found"}), 404
        
        folder_path = folders_obj.folders[foldername]
        
        # Construct full file path
        file_path = os.path.join(folder_path, imageset_name, filename)
        
        # Security check: ensure the path is within the allowed folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(folder_path)):
            logging.warning(f"Security violation: path traversal attempt for {foldername}/{imageset_name}/{filename}")
            return jsonify({"error": "Access denied"}), 403
        
        # Check if file exists
        if not os.path.exists(file_path):
            logging.warning(f"Image file not found: {file_path}")
            return jsonify({"error": f"File '{filename}' not found"}), 404
        
        # Create ImageFile object
        from img_catalog_tui.core.imagefile import ImageFile
        
        try:
            imagefile_obj = ImageFile(file_path=file_path)
            thumbnail_path = imagefile_obj.create_thumbnail()
            
            if thumbnail_path:
                logging.info(f"Successfully created thumbnail for {filename}: {thumbnail_path}")
                return jsonify({
                    "success": True,
                    "message": "Thumbnail created successfully",
                    "thumbnail_path": thumbnail_path
                }), 200
            else:
                logging.error(f"Failed to create thumbnail for {filename}")
                return jsonify({"error": "Failed to create thumbnail"}), 500
                
        except Exception as e:
            logging.error(f"Error creating thumbnail for {filename}: {e}", exc_info=True)
            return jsonify({"error": f"Failed to create thumbnail: {str(e)}"}), 500
        
    except Exception as e:
        logging.error(f"Error in create_thumbnail endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def create_watermark(foldername: str, imageset_name: str, filename: str):
    """Create a watermarked version of an image file."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        # Get watermark file path from config
        watermark_file = config.config_data.get('paths', {}).get('watermark_file', '')
        if not watermark_file:
            logging.error("Watermark file path not configured")
            return jsonify({"error": "Watermark file path not configured in config.toml"}), 500
        
        # Check if watermark file exists
        if not os.path.exists(watermark_file):
            logging.error(f"Watermark file does not exist: {watermark_file}")
            return jsonify({"error": f"Watermark file not found: {watermark_file}"}), 500
        
        # Get folder path from Folders registry
        folders_obj = Folders(config=config)
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return jsonify({"error": f"Folder '{foldername}' not found"}), 404
        
        folder_path = folders_obj.folders[foldername]
        
        # Construct full file path
        file_path = os.path.join(folder_path, imageset_name, filename)
        
        # Security check: ensure the path is within the allowed folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(folder_path)):
            logging.warning(f"Security violation: path traversal attempt for {foldername}/{imageset_name}/{filename}")
            return jsonify({"error": "Access denied"}), 403
        
        # Check if file exists
        if not os.path.exists(file_path):
            logging.warning(f"Image file not found: {file_path}")
            return jsonify({"error": f"File '{filename}' not found"}), 404
        
        # Create ImageFile object
        from img_catalog_tui.core.imagefile import ImageFile
        
        try:
            imagefile_obj = ImageFile(file_path=file_path)
            watermark_path = imagefile_obj.create_watermark(watermark_file=watermark_file)
            
            if watermark_path:
                logging.info(f"Successfully created watermark for {filename}: {watermark_path}")
                return jsonify({
                    "success": True,
                    "message": "Watermark created successfully",
                    "watermark_path": watermark_path
                }), 200
            else:
                logging.error(f"Failed to create watermark for {filename}")
                return jsonify({"error": "Failed to create watermark"}), 500
                
        except Exception as e:
            logging.error(f"Error creating watermark for {filename}: {e}", exc_info=True)
            return jsonify({"error": f"Failed to create watermark: {str(e)}"}), 500
        
    except Exception as e:
        logging.error(f"Error in create_watermark endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def mockup_create():
    """Create mockups for an image file using Photoshop."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = ['image_file_path', 'mockup_type', 'orientation']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        image_file_path = data['image_file_path']
        mockup_type = data['mockup_type']
        orientation = data['orientation']
        layer_name = data.get('layer_name', None)
        
        # Validate that image file exists
        if not os.path.exists(image_file_path):
            return jsonify({"error": f"Image file not found: {image_file_path}"}), 404
        
        # Create ImageMockup object
        from img_catalog_tui.core.imagefile_mockups import ImageMockup
        
        try:
            mockup_obj = ImageMockup(
                config=config,
                image_file_path=image_file_path,
                mockup_type=mockup_type,
                orientation=orientation,
                layer_name=layer_name
            )
            
            # Build the mockups
            mockup_obj.build_mockups()
            
            # Return success response
            return jsonify({
                "success": True,
                "message": "Mockups created successfully",
                "mockup_count": len(mockup_obj.mockups),
                "output_folder": mockup_obj.output_folder,
                "mockups": mockup_obj.mockups
            }), 200
            
        except Exception as e:
            logging.error(f"Error creating mockups: {e}", exc_info=True)
            return jsonify({"error": f"Failed to create mockups: {str(e)}"}), 500
        
    except Exception as e:
        logging.error(f"Error in mockup_create endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def imageset_move(foldername: str, imageset: str):
    """Move an imageset to a different folder."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required field
        if 'target_foldername' not in data:
            return jsonify({"error": "Missing required field: target_foldername"}), 400
        
        target_foldername = data['target_foldername']
        
        # Get folder paths from Folders registry
        folders_obj = Folders(config=config)
        
        # Validate source folder exists
        if foldername not in folders_obj.folders:
            logging.warning(f"Source folder '{foldername}' not found in registry")
            return jsonify({"error": f"Source folder '{foldername}' not found"}), 404
        
        # Validate target folder exists
        if target_foldername not in folders_obj.folders:
            logging.warning(f"Target folder '{target_foldername}' not found in registry")
            return jsonify({"error": f"Target folder '{target_foldername}' not found"}), 404
        
        # Prevent moving to the same folder
        if foldername == target_foldername:
            return jsonify({"error": "Cannot move imageset to the same folder"}), 400
        
        source_folder_path = folders_obj.folders[foldername]
        target_folder_path = folders_obj.folders[target_foldername]
        
        # Create imageset object
        imageset_obj = Imageset(config=config, folder_name=source_folder_path, imageset_name=imageset)
        
        # Move the imageset
        new_imageset_path = imageset_obj.move_to_folder(target_folder_path)
        
        # Return success response
        response_data = {
            "message": "Imageset moved successfully",
            "imageset": imageset,
            "source_folder": foldername,
            "target_folder": target_foldername,
            "new_path": new_imageset_path
        }
        
        logging.info(f"Successfully moved imageset '{imageset}' from '{foldername}' to '{target_foldername}'")
        return jsonify(response_data), 200
        
    except FileNotFoundError as e:
        logging.error(f"File not found during imageset move: {e}")
        return jsonify({"error": str(e)}), 404
    except FileExistsError as e:
        logging.error(f"Target already exists during imageset move: {e}")
        return jsonify({"error": str(e)}), 409
    except PermissionError as e:
        logging.error(f"Permission error during imageset move: {e}")
        return jsonify({"error": f"Permission denied: {str(e)}"}), 403
    except Exception as e:
        logging.error(f"Error moving imageset {imageset} from {foldername} to {target_foldername}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def move_imagesets(foldername: str):
    """Move multiple imagesets to a target folder (bulk operation)."""
    try:
        # Validate request method
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required field
        if 'target_foldername' not in data:
            return jsonify({"error": "Missing required field: target_foldername"}), 400
        
        target_foldername = data['target_foldername']
        imagesets_list = data.get('imagesets', [])
        filter_status = data.get('filter_status', None)
        
        # Get folder paths from Folders registry
        folders_obj = Folders(config=config)
        
        # Validate source folder exists
        if foldername not in folders_obj.folders:
            logging.warning(f"Source folder '{foldername}' not found in registry")
            return jsonify({"error": f"Source folder '{foldername}' not found"}), 404
        
        # Validate target folder exists
        if target_foldername not in folders_obj.folders:
            logging.warning(f"Target folder '{target_foldername}' not found in registry")
            return jsonify({"error": f"Target folder '{target_foldername}' not found"}), 404
        
        # Prevent moving to the same folder
        if foldername == target_foldername:
            return jsonify({"error": "Cannot move imagesets to the same folder"}), 400
        
        source_folder_path = folders_obj.folders[foldername]
        target_folder_path = folders_obj.folders[target_foldername]
        
        # Create folder object to get imagesets
        folder_obj = ImagesetFolder(config=config, foldername=source_folder_path)
        
        # Determine which imagesets to move based on the mode
        imagesets_to_move = []
        
        if imagesets_list:
            # Mode 1: Specific list of imagesets provided
            imagesets_to_move = imagesets_list
            logging.info(f"Moving specific imagesets: {len(imagesets_to_move)}")
        elif filter_status:
            # Mode 2: Filter by status
            for imageset_name, imageset_obj in folder_obj.imagesets.items():
                if imageset_obj.status == filter_status:
                    imagesets_to_move.append(imageset_name)
            logging.info(f"Moving imagesets with status '{filter_status}': {len(imagesets_to_move)}")
        else:
            # Mode 3: Move all imagesets
            imagesets_to_move = list(folder_obj.imagesets.keys())
            logging.info(f"Moving all imagesets: {len(imagesets_to_move)}")
        
        if not imagesets_to_move:
            return jsonify({"error": "No imagesets to move"}), 400
        
        # Track successes and failures
        successful_moves = []
        failed_moves = []
        
        # Process each imageset
        for imageset_name in imagesets_to_move:
            try:
                # Check if imageset exists in source folder
                if imageset_name not in folder_obj.imagesets:
                    logging.warning(f"Imageset '{imageset_name}' not found in source folder")
                    failed_moves.append({
                        "imageset": imageset_name,
                        "error": "Imageset not found in source folder"
                    })
                    continue
                
                # Get the imageset object
                imageset_obj = folder_obj.imagesets[imageset_name]
                
                # Move the imageset
                imageset_obj.move_to_folder(target_folder_path)
                
                successful_moves.append(imageset_name)
                logging.info(f"Successfully moved imageset '{imageset_name}'")
                
            except FileExistsError as e:
                logging.error(f"Target already exists for imageset '{imageset_name}': {e}")
                failed_moves.append({
                    "imageset": imageset_name,
                    "error": f"Imageset already exists in target folder"
                })
            except Exception as e:
                logging.error(f"Error moving imageset '{imageset_name}': {e}", exc_info=True)
                failed_moves.append({
                    "imageset": imageset_name,
                    "error": str(e)
                })
        
        # Prepare response
        total_imagesets = len(imagesets_to_move)
        successful_count = len(successful_moves)
        failed_count = len(failed_moves)
        
        response_data = {
            "message": "Bulk move operation completed",
            "source_folder": foldername,
            "target_folder": target_foldername,
            "total_imagesets": total_imagesets,
            "successful_count": successful_count,
            "failed_count": failed_count,
            "successful_moves": successful_moves,
            "failed_moves": failed_moves
        }
        
        # Return appropriate status code based on results
        if failed_moves:
            if successful_count == 0:
                # All failed
                logging.error(f"Bulk move failed for all imagesets from '{foldername}' to '{target_foldername}'")
                return jsonify(response_data), 500
            else:
                # Partial success
                logging.warning(f"Bulk move partially failed: {failed_count} failures out of {total_imagesets}")
                return jsonify(response_data), 207  # Multi-Status
        else:
            # All successful
            logging.info(f"Bulk move successful for all {total_imagesets} imagesets from '{foldername}' to '{target_foldername}'")
            return jsonify(response_data), 200
        
    except FileNotFoundError as e:
        logging.error(f"File not found during bulk move: {e}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logging.error(f"Error in bulk move from {foldername} to target folder: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def favicon():
    """Return a simple SVG favicon."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
        <rect width="16" height="16" fill="#2563eb"/>
        <rect x="2" y="2" width="12" height="12" fill="none" stroke="#ffffff" stroke-width="1"/>
        <circle cx="8" cy="8" r="3" fill="#ffffff"/>
    </svg>'''
    return svg, 200, {'Content-Type': 'image/svg+xml'}


def search_imagesets():
    """Search imagesets based on query criteria."""
    try:
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405
        
        data = request.get_json() or {}
        
        # Build query from request data
        query = {}
        
        if 'status' in data:
            query['status'] = data['status']
        
        if 'good_for' in data:
            query['good_for'] = data['good_for']
        
        if 'posted_to' in data:
            posted_to = data['posted_to']
            if isinstance(posted_to, dict) and 'operator' in posted_to:
                query['posted_to'] = {
                    'operator': posted_to.get('operator', '='),
                    'value': posted_to.get('value', '')
                }
            else:
                query['posted_to'] = posted_to
        
        if 'prompt_contains' in data:
            query['prompt_contains'] = data['prompt_contains']
        
        if 'folder' in data:
            query['folder'] = data['folder']
        
        # TODO: Implement search using database tables directly
        # The search functionality needs to be reimplemented using ImagesetsTable
        # For now, return empty results
        logging.warning("Search functionality not yet implemented with new database structure")
        
        return jsonify({
            'results': [],
            'count': 0,
            'message': 'Search functionality being updated for new database structure'
        }), 200
        
    except Exception as e:
        logging.error(f"Error searching imagesets: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

