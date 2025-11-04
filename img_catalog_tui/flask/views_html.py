import logging
import os
import requests
from flask import jsonify, render_template, send_file, abort, request

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


def reviews_list(foldername: str) -> str:
    """Return the reviews list HTML page showing available review presets for a folder."""
    try:
        logging.debug(f"reviews_list endpoint: folder={foldername}")
        
        # Get review presets from config
        presets = config.config_data.get("review_presets", {})
        
        return render_template('reviews_list.html', 
                             foldername=foldername,
                             presets=presets)
                             
    except Exception as e:
        logging.error(f"Error in reviews_list endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def reviews(foldername: str, review_name: str = "new") -> str:
    """Return the reviews HTML page for a specific folder and review name."""
    try:
        from img_catalog_tui.core.folder_review import create_folder_review
        title = f"Image Catalog Review: {review_name}"
        
        logging.debug(f"reviews endpoint: folder={foldername}, review_name={review_name}")
        
        try:
            review_obj = create_folder_review(config=config, folder_name=foldername, review_name=review_name)
        except Exception as e:
            logging.error(f"Failed to create folder review: {e}")
            return render_template('reviews.html', 
                                 title=title, 
                                 foldername=foldername,
                                 name=review_name,
                                 review_type=review_name,
                                 options=[],
                                 imagesets={},
                                 error=str(e)), 404
        
        
        # Convert imagesets to dict format for template
        imagesets_dict = {}
        for imageset_name, imageset_obj in review_obj.imagesets.items():
            imagesets_dict[imageset_name] = imageset_obj.to_dict()

        return render_template('reviews.html', 
                             title=title, 
                             foldername=foldername,
                             name=review_name,
                             review_type=review_obj.review_type,
                             options=review_obj.options,
                             review_obj=review_obj,
                             imagesets=imagesets_dict)
                             
    except Exception as e:
        logging.error(f"Error in reviews endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

def interview(foldername: str, imageset_name: str) -> str:
    """Return the interview HTML page for a specific imageset."""
    try:
        logging.debug(f"interview endpoint: folder={foldername}, imageset={imageset_name}")
        
        # Get folder path using lightweight utility function
        from img_catalog_tui.utils.folder_utils import get_folder_path
        folder_path = get_folder_path(foldername)
        
        if not folder_path:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return render_template('interview.html', 
                                 title="Interview: Imageset Not Found", 
                                 foldername=foldername,
                                 imagesetname=imageset_name,
                                 imageset_data=None,
                                 error=f"Folder '{foldername}' not found"), 404
        
        # Create imageset object
        from img_catalog_tui.core.imageset import Imageset
        
        try:
            imageset_obj = Imageset(config=config, folder_name=folder_path, imageset_name=imageset_name)
        except FileNotFoundError as e:
            logging.warning(f"Imageset not found: {e}")
            return render_template('interview.html', 
                                 title="Interview: Imageset Not Found", 
                                 foldername=foldername,
                                 imagesetname=imageset_name,
                                 imageset_data=None,
                                 error=f"Imageset '{imageset_name}' not found"), 404
        
        # Convert imageset to dict format for template
        imageset_data = imageset_obj.to_dict()
        
        def get_interview_file(files: dict) -> str:
        
            filename: str = ""
            
            for filename, filedata in files.items():
                if filename.endswith("_interview.txt"):
                    return filedata["fullpath"]
                
            return ""
        
        def get_interview_file_content(interview_file_path: str) -> str:
            """Get the content of an interview file if it exists."""
            
            if interview_file_path == "":
                return ""
            
            try:
                # Validate filepath exists; if not return ""
                if not os.path.exists(interview_file_path):
                    logging.debug(f"Interview file does not exist: {interview_file_path}")
                    return ""
                
                # Open and read interview_file_path and return it
                with open(interview_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    logging.debug(f"Successfully read interview file: {interview_file_path}")
                    return content
                    
            except Exception as e:
                logging.error(f"Error reading interview file {interview_file_path}: {e}", exc_info=True)
                return ""
        
        interview_file_content = get_interview_file_content(get_interview_file(imageset_data['files']))
                
        
        return render_template('interview.html', 
                             title=f"Interview: {imageset_name}", 
                             foldername=foldername,
                             imagesetname=imageset_name,
                             imageset_data=imageset_data,
                             interview_file_content = interview_file_content)
                             
    except Exception as e:
        logging.error(f"Error in interview endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

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
            'imagesets': {},
            'counts': {
                'status': {}
            }
        }
        
        # Add detailed imageset information and count by status
        for imageset_name, imageset_obj in folder_obj.imagesets.items():
            folder_data['imagesets'][imageset_name] = imageset_obj.to_dict()
            
            # Count imagesets by status
            status = imageset_obj.status
            if status in folder_data['counts']['status']:
                folder_data['counts']['status'][status] += 1
            else:
                folder_data['counts']['status'][status] = 1
        
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
    """Serve files from their original filesystem locations."""
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
        
        logging.debug(f"Serving file: {image_path}")
        
        # Determine if this is a text file that should be displayed inline
        text_extensions = {'.txt', '.toml', '.json', '.md', '.yaml', '.yml', '.log', '.cfg', '.ini', '.py', '.js', '.css', '.html', '.xml', '.csv'}
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension in text_extensions:
            # Serve text files with inline disposition to display in browser
            return send_file(image_path, mimetype='text/plain', as_attachment=False)
        else:
            # Serve other files (images, etc.) normally
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


def imageset(foldername: str, imageset_name: str) -> str:
    """Return the imageset HTML page that displays detailed information about a specific imageset."""
    try:
        logging.debug(f"imageset endpoint: folder={foldername}, imageset={imageset_name}")
        
        # Build the API URL to fetch imageset data
        # Use request.host_url to get the current host and port
        api_url = f"{request.host_url}api/imageset/{foldername}/{imageset_name}"
        
        # Make request to the API endpoint
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 404:
                return render_template('imageset.html',
                                     title="Imageset Not Found",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     imageset_data=None,
                                     error="Imageset not found"), 404
            elif response.status_code != 200:
                logging.error(f"API returned status {response.status_code}: {response.text}")
                return render_template('imageset.html',
                                     title="Error",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     imageset_data=None,
                                     error="Failed to fetch imageset data"), 500
            
            imageset_data = response.json()
            
        except requests.RequestException as e:
            logging.error(f"Error fetching imageset data from API: {e}")
            return render_template('imageset.html',
                                 title="Error",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 imageset_data=None,
                                 error="Failed to connect to API"), 500
            
        # build a image_files dict and pass it into the 
        
        return render_template('imageset.html',
                             title=f"Imageset: {imageset_name}",
                             foldername=foldername,
                             imageset_name=imageset_name,
                             imageset_data=imageset_data)
                             
    except Exception as e:
        logging.error(f"Error in imageset endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def imageset_edit(foldername: str, imageset_name: str) -> str:
    """Return the imageset edit HTML page for editing imageset metadata."""
    try:
        logging.debug(f"imageset_edit endpoint: folder={foldername}, imageset={imageset_name}")
        
        # Build the API URL to fetch imageset data
        api_url = f"{request.host_url}api/imageset/{foldername}/{imageset_name}"
        
        # Make request to the API endpoint
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 404:
                return render_template('imageset_edit.html',
                                     title="Imageset Not Found",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     imageset_data=None,
                                     config_options={},
                                     error="Imageset not found"), 404
            elif response.status_code != 200:
                logging.error(f"API returned status {response.status_code}: {response.text}")
                return render_template('imageset_edit.html',
                                     title="Error",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     imageset_data=None,
                                     config_options={},
                                     error="Failed to fetch imageset data"), 500
            
            imageset_data = response.json()
            
        except requests.RequestException as e:
            logging.error(f"Error fetching imageset data from API: {e}")
            return render_template('imageset_edit.html',
                                 title="Error",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 imageset_data=None,
                                 config_options={},
                                 error="Failed to connect to API"), 500
        
        # Get configuration options for form dropdowns
        config_options = {
            'status': config.config_data.get('status', []),
            'edits': config.config_data.get('edits', []),
            'needs': config.config_data.get('needs', []),
            'good_for': config.config_data.get('good_for', []),
            'posted_to': config.config_data.get('posted_to', [])
        }
        
        return render_template('imageset_edit.html',
                             title=f"Edit Imageset: {imageset_name}",
                             foldername=foldername,
                             imageset_name=imageset_name,
                             imageset_data=imageset_data,
                             config_options=config_options)
                             
    except Exception as e:
        logging.error(f"Error in imageset_edit endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def imagefile(foldername: str, imageset_name: str, filename: str) -> str:
    """Return the imagefile HTML page that displays detailed information about a specific image file."""
    try:
        logging.debug(f"imagefile endpoint: folder={foldername}, imageset={imageset_name}, filename={filename}")
        
        # Get folder path from Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return render_template('imagefile.html',
                                 title="File Not Found",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
                                 imagefile_data=None,
                                 error=f"Folder '{foldername}' not found"), 404
        
        folder_path = folders_obj.folders[foldername]
        
        # Construct full file path
        file_path = os.path.join(folder_path, imageset_name, filename)
        
        # Security check: ensure the path is within the allowed folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(folder_path)):
            logging.warning(f"Security violation: path traversal attempt for {foldername}/{imageset_name}/{filename}")
            return render_template('imagefile.html',
                                 title="Access Denied",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
                                 imagefile_data=None,
                                 error="Access denied"), 403
        
        # Check if file exists
        if not os.path.exists(file_path):
            logging.warning(f"Image file not found: {file_path}")
            return render_template('imagefile.html',
                                 title="File Not Found",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
                                 imagefile_data=None,
                                 error=f"File '{filename}' not found"), 404
        
        # Create ImageFile object
        from img_catalog_tui.core.imagefile import ImageFile
        
        try:
            imagefile_obj = ImageFile(file_path=file_path)
        except Exception as e:
            logging.error(f"Error creating ImageFile object: {e}")
            return render_template('imagefile.html',
                                 title="Error",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
                                 imagefile_data=None,
                                 error="Failed to load image file"), 500
        
        # Check if thumbnail and watermark already exist
        thumbnail_exists = bool(imagefile_obj.thumbnail)
        watermark_exists = os.path.exists(imagefile_obj.file_path.replace(os.path.splitext(imagefile_obj.file_path)[1], f"_watermark{os.path.splitext(imagefile_obj.file_path)[1]}"))
        
        # Prepare data for template
        imagefile_data = {
            'filename': filename,
            'file_path': file_path,
            'height': imagefile_obj.height,
            'width': imagefile_obj.width,
            'aspect_ratio': imagefile_obj.aspect_ratio,
            'size': imagefile_obj.size,
            'thumbnail_exists': thumbnail_exists,
            'watermark_exists': watermark_exists
        }
        
        return render_template('imagefile.html',
                             title=f"ImageFile: {filename}",
                             foldername=foldername,
                             imageset_name=imageset_name,
                             filename=filename,
                             imagefile_data=imagefile_data)
                             
    except Exception as e:
        logging.error(f"Error in imagefile endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def mockups(foldername: str, imageset_name: str, filename: str) -> str:
    """Return the mockups HTML page for generating mockup images using Photopea."""
    try:
        logging.debug(f"mockups endpoint: folder={foldername}, imageset={imageset_name}, filename={filename}")
        
        # Get folder path from Folders registry
        folders_obj = Folders()
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return render_template('mockups.html',
                                 title="Mockups - Folder Not Found",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
                                 mockup_folders={},
                                 error=f"Folder '{foldername}' not found"), 404
        
        folder_path = folders_obj.folders[foldername]
        
        # Construct full file path
        file_path = os.path.join(folder_path, imageset_name, filename)
        
        # Security check: ensure the path is within the allowed folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(folder_path)):
            logging.warning(f"Security violation: path traversal attempt for {foldername}/{imageset_name}/{filename}")
            return render_template('mockups.html',
                                 title="Mockups - Access Denied",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
                                 mockup_folders={},
                                 error="Access denied"), 403
        
        # Check if file exists
        if not os.path.exists(file_path):
            logging.warning(f"Image file not found: {file_path}")
            return render_template('mockups.html',
                                 title="Mockups - File Not Found",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
                                 mockup_folders={},
                                 error=f"File '{filename}' not found"), 404
        
        # Get mockup folders from config
        mockup_folders = config.config_data.get("mockups", {}).get("folders", {})
        
        return render_template('mockups.html',
                             title=f"Generate Mockups: {filename}",
                             foldername=foldername,
                             imageset_name=imageset_name,
                             filename=filename,
                             mockup_folders=mockup_folders)
                             
    except Exception as e:
        logging.error(f"Error in mockups endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500