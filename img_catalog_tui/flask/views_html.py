import logging
import os
import requests
from flask import jsonify, render_template, send_file, abort, request, url_for

from img_catalog_tui.config import Config
from img_catalog_tui.core.search import SearchService

from img_catalog_tui.core.folders import Folders
from img_catalog_tui.core.folder import ImagesetFolder

config = Config()


def _get_search_form_options() -> dict:
    """Return config-driven options for search forms."""
    return {
        "status": config.config_data.get("status", []),
        "good_for": config.config_data.get("good_for", []),
        "posted_to": config.config_data.get("posted_to", []),
        "needs": config.config_data.get("needs", []),
    }


def _build_thumbnail_url(result: dict) -> str:
    """Construct a relative thumbnail URL if we can safely map it to serve_image."""
    cover_path = result.get("cover_image_path")
    imageset_folder_path = result.get("imageset_folder_path")
    foldername = result.get("folder_name")
    imageset_name = result.get("imageset_name")

    if not all([cover_path, imageset_folder_path, foldername, imageset_name]):
        return ""

    normalized_cover = cover_path.replace("\\", "/")
    normalized_folder = imageset_folder_path.replace("\\", "/")

    if not normalized_cover.startswith(normalized_folder):
        return ""

    relative = normalized_cover[len(normalized_folder):].lstrip("/\\")
    if not relative:
        return ""

    return url_for('serve_image', foldername=foldername, imageset_name=imageset_name, filename=relative)


def _augment_search_results(results: list[dict]) -> list[dict]:
    """Attach template-ready helpers (links, URLs, etc.) to each result."""
    enhanced: list[dict] = []
    for row in results:
        row_copy = row.copy()
        foldername = row_copy.get("folder_name") or ""
        imageset_name = row_copy.get("imageset_name") or ""
        if foldername and imageset_name:
            row_copy["imageset_url"] = url_for('imageset', foldername=foldername, imageset_name=imageset_name)
            row_copy["edit_url"] = url_for('imageset_edit', foldername=foldername, imageset_name=imageset_name)
            row_copy["move_url"] = url_for('imageset_move_form', foldername=foldername, imageset_name=imageset_name)
            row_copy["review_url"] = url_for('reviews_list', foldername=foldername)
        else:
            row_copy["imageset_url"] = ""
            row_copy["edit_url"] = ""
            row_copy["move_url"] = ""
            row_copy["review_url"] = ""

        row_copy["thumbnail_url"] = _build_thumbnail_url(row_copy)
        enhanced.append(row_copy)
    return enhanced


def search_page() -> str:
    """Render the search landing page."""
    try:
        return render_template(
            'search.html',
            title="Search Catalog",
            config_options=_get_search_form_options()
        )
    except Exception as e:
        logging.error(f"Error rendering search page: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def search_results() -> str:
    """Render the search results grid."""
    try:
        search_type = (request.values.get("search_type") or "").strip()
        service = SearchService(config)
        results: list[dict] = []
        error_message: str | None = None
        search_context: dict[str, str] = {}

        def _record_context(label: str, value: str) -> None:
            if value and value.strip():
                search_context[label] = value

        if search_type == "prompt":
            prompt_text = request.values.get("prompt_text", "")
            _record_context("Prompt contains", prompt_text)
            if prompt_text.strip():
                results = service.search_by_prompt(prompt_text)
            else:
                error_message = "Enter prompt text to run a prompt search."
        elif search_type == "status_good_for_posted_to":
            status_value = request.values.get("status_filter", "")
            good_for_value = request.values.get("good_for_filter", "")
            posted_exclude = request.values.get("posted_to_exclude", "")
            _record_context("Status", status_value)
            _record_context("Good for contains", good_for_value)
            _record_context("Posted_to excludes", posted_exclude)
            if status_value.strip() and good_for_value.strip() and posted_exclude.strip():
                results = service.search_status_good_for_posted_to(status_value, good_for_value, posted_exclude)
            else:
                error_message = "Status, Good For, and Posted To filters are required for this search."
        elif search_type == "folder":
            folder_value = request.values.get("folder_value", "")
            _record_context("Folder", folder_value)
            if folder_value.strip():
                results = service.search_by_folder(folder_value)
            else:
                error_message = "Provide a folder name or path."
        elif search_type == "imageset_name":
            name_value = request.values.get("imageset_name_value", "")
            _record_context("Imageset contains", name_value)
            if name_value.strip():
                results = service.search_imageset_name(name_value)
            else:
                error_message = "Provide part of an imageset name."
        elif search_type == "status_needs":
            status_value = request.values.get("needs_status", "")
            needs_value = request.values.get("needs_contains", "")
            _record_context("Status", status_value)
            _record_context("Needs contains", needs_value)
            if status_value.strip():
                results = service.search_status_and_needs(status_value, needs_value)
            else:
                error_message = "Status is required for the status/needs search."
        else:
            error_message = "Unknown search type. Please launch searches from the search page."

        enhanced_results = _augment_search_results(results)
        return render_template(
            'search_results.html',
            title="Search Results",
            search_type=search_type,
            search_context=search_context,
            results=enhanced_results,
            error_message=error_message,
            result_count=len(enhanced_results)
        )
    except Exception as e:
        logging.error(f"Error rendering search results: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

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
        folders_obj = Folders(config=config)
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
        folders_obj = Folders(config=config)
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
        folders_obj = Folders(config=config)
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


def _csv_to_list(value: str | None) -> list[str]:
    """Convert a comma-separated string into a list of trimmed values."""
    if not value or not isinstance(value, str):
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def _empty_selection_map() -> dict[str, list[str]]:
    """Return an empty selection map for checkbox fields."""
    return {
        'edits': [],
        'needs': [],
        'good_for': [],
        'posted_to': []
    }


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
                                     selected_options=_empty_selection_map(),
                                     error="Imageset not found"), 404
            elif response.status_code != 200:
                logging.error(f"API returned status {response.status_code}: {response.text}")
                return render_template('imageset_edit.html',
                                     title="Error",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     imageset_data=None,
                                     config_options={},
                                     selected_options=_empty_selection_map(),
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
                                 selected_options=_empty_selection_map(),
                                 error="Failed to connect to API"), 500
        
        # Get configuration options for form dropdowns
        config_options = {
            'status': config.config_data.get('status', []),
            'edits': config.config_data.get('edits', []),
            'needs': config.config_data.get('needs', []),
            'good_for': config.config_data.get('good_for', []),
            'posted_to': config.config_data.get('posted_to', [])
        }
        
        selected_options = {
            'edits': _csv_to_list(imageset_data.get('edits')),
            'needs': _csv_to_list(imageset_data.get('needs')),
            'good_for': _csv_to_list(imageset_data.get('good_for')),
            'posted_to': _csv_to_list(imageset_data.get('posted_to'))
        }
        
        return render_template('imageset_edit.html',
                             title=f"Edit Imageset: {imageset_name}",
                             foldername=foldername,
                             imageset_name=imageset_name,
                             imageset_data=imageset_data,
                             config_options=config_options,
                             selected_options=selected_options)
                             
    except Exception as e:
        logging.error(f"Error in imageset_edit endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def imageset_move_form(foldername: str, imageset_name: str) -> str:
    """Return the imageset move HTML page for moving imageset to another folder."""
    try:
        logging.debug(f"imageset_move_form endpoint: folder={foldername}, imageset={imageset_name}")
        
        # Build the API URL to fetch imageset data
        api_url = f"{request.host_url}api/imageset/{foldername}/{imageset_name}"
        
        # Make request to the API endpoint
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 404:
                return render_template('imageset_move.html',
                                     title="Imageset Not Found",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     imageset_data=None,
                                     available_folders={},
                                     error="Imageset not found"), 404
            elif response.status_code != 200:
                logging.error(f"API returned status {response.status_code}: {response.text}")
                return render_template('imageset_move.html',
                                     title="Error",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     imageset_data=None,
                                     available_folders={},
                                     error="Failed to fetch imageset data"), 500
            
            imageset_data = response.json()
            
        except requests.RequestException as e:
            logging.error(f"Error fetching imageset data from API: {e}")
            return render_template('imageset_move.html',
                                 title="Error",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 imageset_data=None,
                                 available_folders={},
                                 error="Failed to connect to API"), 500
        
        # Get available folders from Folders registry
        folders_obj = Folders(config=config)
        available_folders = folders_obj.folders
        
        return render_template('imageset_move.html',
                             title=f"Move Imageset: {imageset_name}",
                             foldername=foldername,
                             imageset_name=imageset_name,
                             imageset_data=imageset_data,
                             available_folders=available_folders)
                             
    except Exception as e:
        logging.error(f"Error in imageset_move_form endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def imagefile(foldername: str, imageset_name: str, filename: str) -> str:
    """Return the imagefile HTML page that displays detailed information about a specific image file."""
    try:
        logging.debug(f"imagefile endpoint: folder={foldername}, imageset={imageset_name}, filename={filename}")
        
        # Get folder path from Folders registry
        folders_obj = Folders(config=config)
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
    """Return the mockups HTML page or process mockup generation request."""
    try:
        logging.debug(f"mockups endpoint: folder={foldername}, imageset={imageset_name}, filename={filename}")
        
        # Get folder path from Folders registry
        folders_obj = Folders(config=config)
        if foldername not in folders_obj.folders:
            logging.warning(f"Folder '{foldername}' not found in registry")
            return render_template('mockups.html',
                                 title="Mockups - Folder Not Found",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
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
                                 error="Access denied"), 403
        
        # Check if file exists
        if not os.path.exists(file_path):
            logging.warning(f"Image file not found: {file_path}")
            return render_template('mockups.html',
                                 title="Mockups - File Not Found",
                                 foldername=foldername,
                                 imageset_name=imageset_name,
                                 filename=filename,
                                 error=f"File '{filename}' not found"), 404
        
        # Handle POST request - build mockups
        if request.method == 'POST':
            try:
                from img_catalog_tui.core.imagefile_mockups import ImageMockup
                
                # Get form data
                mockup_type = request.form.get('mockup_type')
                orientation = request.form.get('orientation')
                layer_name = request.form.get('layer_name', None)
                
                # Validate required fields
                if not mockup_type or not orientation:
                    return render_template('mockups.html',
                                         title=f"Generate Mockups: {filename}",
                                         foldername=foldername,
                                         imageset_name=imageset_name,
                                         filename=filename,
                                         error="Missing required fields: mockup_type and orientation"), 400
                
                # Create ImageMockup instance
                mockup_obj = ImageMockup(
                    config=config,
                    image_file_path=file_path,
                    mockup_type=mockup_type,
                    orientation=orientation,
                    layer_name=layer_name if layer_name else None
                )
                
                # Build mockups
                mockup_obj.build_mockups()
                
                # Re-render template with success message
                return render_template('mockups.html',
                                     title=f"Generate Mockups: {filename}",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     filename=filename,
                                     mockup_obj=mockup_obj,
                                     success=f"Successfully created {len(mockup_obj.mockups)} mockup(s)")
                
            except Exception as e:
                logging.error(f"Error building mockups: {e}", exc_info=True)
                return render_template('mockups.html',
                                     title=f"Generate Mockups: {filename}",
                                     foldername=foldername,
                                     imageset_name=imageset_name,
                                     filename=filename,
                                     error=f"Failed to build mockups: {str(e)}"), 500
        
        # Handle GET request - show form or existing mockups
        # Try to load existing mockup info
        mockup_obj = None
        try:
            from img_catalog_tui.core.imagefile_mockups import ImageMockup
            
            # Try to detect if mockups already exist
            # We'll try common configurations
            mockup_types = config.config_data.get("mockups", {}).get("types", {})
            
            # For now, just show the form - let user select mockup type and orientation
            # If mockups already exist, they will be detected after POST
            
        except Exception as e:
            logging.debug(f"Could not pre-load mockup info: {e}")
        
        # Get available mockup types from config
        mockup_types = config.config_data.get("mockups", {}).get("types", {})
        
        return render_template('mockups.html',
                             title=f"Generate Mockups: {filename}",
                             foldername=foldername,
                             imageset_name=imageset_name,
                             filename=filename,
                             mockup_types=mockup_types,
                             mockup_obj=mockup_obj)
                             
    except Exception as e:
        logging.error(f"Error in mockups endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500