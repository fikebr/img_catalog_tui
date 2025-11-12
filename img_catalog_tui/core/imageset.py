import logging
import os

from img_catalog_tui.config import Config
from img_catalog_tui.core.imageset_toml import ImagesetToml
from img_catalog_tui.logger import setup_logging


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
        self.toml = ImagesetToml(imageset_folder=self.imageset_folder)
        # If status is already archive but folder not under _archive, move it now
        self._ensure_archive_location()
        self.files = self._get_imageset_files() # dict{filename: dict{fullpath, ext, tags}}

        self.get_exif_data()
        _ = self.orig_image
        

    ### properties and setters
    # cover_image
    # orig_image
    # edits
    # status
    # needs
    
        
    
    def _validate_comma_separated_values(self, value: str, valid_options: list[str], field_name: str) -> None:
        """Validate comma-separated values against config options."""
        if not value:
            return
            
        # Split by comma and strip whitespace
        values = [item.strip() for item in value.split(',') if item.strip()]
        
        # Validate each value
        for val in values:
            if val not in valid_options:
                error_msg = f"Invalid {field_name} value '{val}' in '{value}'. Valid options are: {', '.join(valid_options)}"
                logging.error(error_msg)
                raise ValueError(error_msg)
    
    
    @property
    def cover_image(self) -> str:
        """Return the full path to a cover image for this imageset."""
        
        try:
            # Get valid image file extensions from config
            img_file_ext = self.config.config_data.get("img_file_ext", [])
            
            # Lists to store candidates
            thumb_candidates = []
            orig_candidates = []
            image_candidates = []
            
            # Loop through all files
            for filename, file_info in self.files.items():
                file_ext = file_info["ext"].lower().lstrip('.')
                file_tags = file_info["tags"]
                file_path = file_info["fullpath"]
                
                # Check if file has valid image extension
                if file_ext not in [ext.lower() for ext in img_file_ext]:
                    continue
                
                # Add to appropriate candidate list
                if "thumb" in file_tags:
                    thumb_candidates.append(file_path)
                elif "orig" in file_tags:
                    orig_candidates.append(file_path)
                else:
                    image_candidates.append(file_path)
            
            # Return first thumb file if available
            if thumb_candidates:
                logging.debug(f"Found thumb image for cover: {thumb_candidates[0]}")
                return thumb_candidates[0]
            
            # Return first orig file if available
            if orig_candidates:
                logging.debug(f"Found orig image for cover: {orig_candidates[0]}")
                return orig_candidates[0]
            
            # Return first image file if available
            if image_candidates:
                logging.debug(f"Found image for cover: {image_candidates[0]}")
                return image_candidates[0]
            
            # No image files found
            logging.warning(f"No image files found for cover in imageset: {self.imageset_name}")
            return ""
            
        except Exception as e:
            logging.error(f"Error finding cover image: {e}", exc_info=True)
            return ""

    @property
    def orig_image(self) -> str:
        """Find and return the original image file, tagging it if necessary."""
        
        try:
            # Get valid image file extensions from config
            img_file_ext = self.config.config_data.get("img_file_ext", [])
            
            # Get all image files from the files dict
            image_files = []
            for filename, file_info in self.files.items():
                file_ext = file_info["ext"].lower().lstrip('.')
                if file_ext in [ext.lower() for ext in img_file_ext]:
                    image_files.append({
                        "filename": filename,
                        "fullpath": file_info["fullpath"],  
                        "tags": file_info["tags"]
                    })
            
            # If no image files found, throw an error
            if not image_files:
                error_msg = f"No image files found in imageset: {self.imageset_name}"
                logging.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            # Find files with 'orig' tag
            orig_files = [f for f in image_files if "orig" in f["tags"]]
            
            # Case 1: If there is only one image file that has the orig tag
            if len(orig_files) == 1:
                logging.debug(f"Found single orig file: {orig_files[0]['filename']}")
                return orig_files[0]["fullpath"]
            
            # Case 2: If there are multiple files with orig tag, look for one with only orig tag
            elif len(orig_files) > 1:
                single_orig_files = [f for f in orig_files if len(f["tags"]) == 1 and f["tags"][0] == "orig"]
                if len(single_orig_files) == 1:
                    logging.debug(f"Found orig file with single tag: {single_orig_files[0]['filename']}")
                    return single_orig_files[0]["fullpath"]
                else:
                    # Just return the first orig file if we can't find one with only orig tag
                    logging.warning(f"Multiple orig files found, returning first: {orig_files[0]['filename']}")
                    return orig_files[0]["fullpath"]
            
            # Case 3: No orig files found - need to determine and tag original
            else:
                # Case 3a: If there is only one image file, tag it as orig
                if len(image_files) == 1:
                    file_to_tag = image_files[0]
                    logging.info(f"Single image file found, tagging as orig: {file_to_tag['filename']}")
                    new_filename = self.add_tag_to_file(file_to_tag["filename"], "orig")
                    return os.path.join(self.imageset_folder, new_filename)
                
                # Case 3b: Multiple files - look for one with no tags
                else:
                    untagged_files = [f for f in image_files if len(f["tags"]) == 0]
                    if len(untagged_files) == 1:
                        file_to_tag = untagged_files[0]
                        logging.info(f"Found untagged file, tagging as orig: {file_to_tag['filename']}")
                        new_filename = self.add_tag_to_file(file_to_tag["filename"], "orig")
                        return os.path.join(self.imageset_folder, new_filename)
                    
                    # If no untagged files or multiple untagged files, return first image file
                    else:
                        logging.warning(f"Could not determine orig file automatically, returning first image: {image_files[0]['filename']}")
                        return image_files[0]["fullpath"]
            
        except Exception as e:
            logging.error(f"Error finding orig image: {e}", exc_info=True)
            raise


    @property
    def prompt(self) -> str:
        source = self.toml.get(key="source")
        if not source:
            return ""
        # Use case-insensitive access for the "prompt" key within the source section
        prompt_value = self.toml.get(section=source, key="prompt")
        return prompt_value if isinstance(prompt_value, str) else str(prompt_value)

    @property
    def edits(self) -> str:
        return self.toml.get(key="edits")
        
    @edits.setter
    def edits(self, value: str) -> None:
        """Set the edits value after validating against config options."""
        # Validate value against config (supports comma-separated values)
        valid_edits = self.config.config_data.get("edits", [])
        self._validate_comma_separated_values(value, valid_edits, "edits")
        
        # If setting edits to a non-null value and status is not "edit", set status to "edit"
        if value and value.strip() and self.status != "edit":
            logging.info(f"Setting status to 'edit' because edits is being set to '{value}'")
            self.status = "edit"
        
        self.toml.set(key="edits", value=value)

    @property
    def status(self) -> str:
        return self.toml.get(key="status")
    
    @status.setter
    def status(self, value: str) -> None:
        """Set the status value after validating against config options."""
        # Validate value against config
        valid_status = self.config.config_data.get("status", [])
        if value and value not in valid_status:
            error_msg = f"Invalid status value '{value}'. Valid options are: {', '.join(valid_status)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        self.toml.set(key="status", value=value)
        
        if value == "archive":
            self.archive_imageset()

    @property
    def needs(self) -> str:
        return self.toml.get(key="needs")
    
    @needs.setter
    def needs(self, value: str) -> None:
        """Set the needs value after validating against config options."""
        # Validate value against config (supports comma-separated values)
        valid_needs = self.config.config_data.get("needs", [])
        self._validate_comma_separated_values(value, valid_needs, "needs")
        
        self.toml.set(key="needs", value=value)
        
    @property
    def good_for(self) -> str:
        return self.toml.get(key="good_for")
    
    @good_for.setter
    def good_for(self, value: str) -> None:
        """Set the good_for value after validating against config options."""
        # Validate value against config (supports comma-separated values)
        valid_good_for = self.config.config_data.get("good_for", [])
        self._validate_comma_separated_values(value, valid_good_for, "good_for")
        
        self.toml.set(key="good_for", value=value)
        
    
    @property
    def posted_to(self) -> str:
        return self.toml.get(section="biz", key="posted_to")

    @posted_to.setter
    def posted_to(self, value: str) -> None:
        """Set the posted_to value after validating against config options."""
        # Validate value against config (supports comma-separated values)
        valid_posted_to = self.config.config_data.get("posted_to", [])
        self._validate_comma_separated_values(value, valid_posted_to, "posted_to")
        
        self.toml.set(section="biz", key="posted_to", value=value)
        


    ### Methods ###
    
    def add_tag_to_file(self, filename: str, tag: str) -> str:
        """Add a tag to a file by renaming it with the tag embedded in the filename."""
        
        try:
            # Get valid tags from config
            valid_tags = self.config.get_file_tags()
            
            # Validate tag
            if tag not in valid_tags:
                error_msg = f"Invalid tag '{tag}'. Valid tags are: {', '.join(valid_tags)}"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            # Get full path for file
            file_path = os.path.join(self.imageset_folder, filename)
            
            # Check if file exists
            if not os.path.isfile(file_path):
                error_msg = f"File does not exist: {file_path}"
                logging.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            # Check if filename already has this tag
            if f"_{tag}_" in filename or f"_{tag}." in filename:
                error_msg = f"File '{filename}' already has tag '{tag}'"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            # Split filename and extension
            name_part, ext_part = os.path.splitext(filename)
            
            # Create new filename with tag
            new_filename = f"{name_part}_{tag}{ext_part}"
            new_file_path = os.path.join(self.imageset_folder, new_filename)
            
            # Check if target filename already exists
            if os.path.exists(new_file_path):
                error_msg = f"Target file already exists: {new_filename}"
                logging.error(error_msg)
                raise FileExistsError(error_msg)
            
            # Rename the file
            os.rename(file_path, new_file_path)
            logging.info(f"Successfully renamed '{filename}' to '{new_filename}' with tag '{tag}'")
            
            # Update the files dict to reflect the change
            self.files = self._get_imageset_files()
            
            return new_filename
            
        except Exception as e:
            logging.error(f"Error adding tag '{tag}' to file '{filename}': {e}", exc_info=True)
            raise


    def to_dict(self):
        
        biz = self.toml.get(section="biz")
        
        
        
            
            
        data = {
            "imageset_name": self.imageset_name,
            "imageset_folder": self.imageset_folder,
            "status": self.status,
            "edits": self.edits,
            "needs": self.needs,
            "posted_to": self.posted_to,
            "good_for": self.good_for,
            "prompt": self.prompt,
            "source": self.toml.get(key="source"),
            "files": self.files,
            "cover_image": self.cover_image
        }
        
        if biz:
            data["biz"] = biz
        
        return data

    def archive_imageset(self) -> str:
        """Archive the imageset by moving it to the archive folder and updating status."""
        
        try:
            
            # Get archive folder path: {self.folder_name}/_archive/
            archive_folder = os.path.join(self.folder_name, "_archive")
            
            # Create archive folder if it doesn't exist
            if not os.path.exists(archive_folder):
                logging.info(f"Creating archive folder: {archive_folder}")
                os.makedirs(archive_folder, exist_ok=True)
            
            # Get the new path for the imageset in the archive
            new_imageset_path = os.path.join(archive_folder, self.imageset_name)
            
            # Check if target already exists
            if os.path.exists(new_imageset_path):
                error_msg = f"Archive target already exists: {new_imageset_path}"
                logging.error(error_msg)
                raise FileExistsError(error_msg)
            
            # Move the imageset folder to the archive
            logging.info(f"Moving imageset from {self.imageset_folder} to {new_imageset_path}")
            os.rename(self.imageset_folder, new_imageset_path)
            
            # Update the imageset_folder path to reflect the new location
            self.imageset_folder = new_imageset_path
            # Reinitialize toml with new location
            self.toml = ImagesetToml(imageset_folder=self.imageset_folder)
            
            logging.info(f"Successfully archived imageset: {self.imageset_name}")
            return new_imageset_path
            
        except Exception as e:
            logging.error(f"Error archiving imageset {self.imageset_name}: {e}", exc_info=True)
            raise

    def move_to_folder(self, new_folder_path: str) -> str:
        """Move the imageset to a different folder.
        
        Args:
            new_folder_path: Full OS path to the target folder
            
        Returns:
            str: Full OS path to the moved imageset
            
        Raises:
            FileNotFoundError: If target folder doesn't exist
            FileExistsError: If imageset already exists in target folder
            PermissionError: If insufficient permissions to move
        """
        
        try:
            # Validate target folder exists
            if not os.path.exists(new_folder_path):
                error_msg = f"Target folder does not exist: {new_folder_path}"
                logging.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            if not os.path.isdir(new_folder_path):
                error_msg = f"Target path is not a directory: {new_folder_path}"
                logging.error(error_msg)
                raise NotADirectoryError(error_msg)
            
            # Get the new path for the imageset in the target folder
            new_imageset_path = os.path.join(new_folder_path, self.imageset_name)
            
            # Check if target already exists
            if os.path.exists(new_imageset_path):
                error_msg = f"Imageset already exists in target folder: {new_imageset_path}"
                logging.error(error_msg)
                raise FileExistsError(error_msg)
            
            # Store old path for logging
            old_imageset_path = self.imageset_folder
            
            # Move the imageset folder to the target folder
            logging.info(f"Moving imageset from {old_imageset_path} to {new_imageset_path}")
            os.rename(self.imageset_folder, new_imageset_path)
            
            # Update the imageset_folder path to reflect the new location
            self.imageset_folder = new_imageset_path
            # Update the folder_name to reflect the new parent folder
            self.folder_name = new_folder_path
            # Reinitialize toml with new location
            self.toml = ImagesetToml(imageset_folder=self.imageset_folder)
            
            logging.info(f"Successfully moved imageset '{self.imageset_name}' to folder '{new_folder_path}'")
            return new_imageset_path
            
        except Exception as e:
            logging.error(f"Error moving imageset {self.imageset_name} to {new_folder_path}: {e}", exc_info=True)
            raise
        
    def _ensure_archive_location(self) -> None:
        """Ensure archived imagesets live under the _archive folder."""
        
        try:
            # Only act if status is already 'archive'
            if self.status != "archive":
                return
            
            archive_folder = os.path.join(self.folder_name, "_archive")
            current_parent = os.path.normpath(os.path.dirname(self.imageset_folder))
            archive_parent = os.path.normpath(archive_folder)
            
            # If already under the archive folder, nothing to do
            if current_parent == archive_parent:
                return
            
            # Create archive folder if needed
            if not os.path.exists(archive_folder):
                logging.info(f"Creating archive folder: {archive_folder}")
                os.makedirs(archive_folder, exist_ok=True)
            
            target_path = os.path.join(archive_folder, self.imageset_name)
            
            if os.path.exists(target_path):
                error_msg = f"Archive target already exists: {target_path}"
                logging.error(error_msg)
                raise FileExistsError(error_msg)
            
            logging.info(f"Relocating archived imageset from {self.imageset_folder} to {target_path}")
            os.rename(self.imageset_folder, target_path)
            self.imageset_folder = target_path
            # Reinitialize toml to point at new folder
            self.toml = ImagesetToml(imageset_folder=self.imageset_folder)
        except Exception as e:
            logging.error(f"Error ensuring archive location for {self.imageset_name}: {e}", exc_info=True)
            raise
        
    def get_exif_data(self):
        """get the exif data and set into self.toml"""
        
        toml = self.toml.get()
        source = toml.get("source", None)
        logging.debug(f"source: {source}")
        
        needs_exif = False
        
        if not source:
            needs_exif = True
            
        if source and source not in toml:
            needs_exif = True
        
        if needs_exif:
            from img_catalog_tui.core.imageset_metadata import ImagesetMetaData
            
            orig_file = self.orig_image
            if orig_file is None:
                logging.warning(f"No orig file found for imageset {self.imageset_name}, skipping EXIF extraction")
                # Set default values when no orig file is available
                self.toml.set(key="source", value="unknown")
                return
            
            metadata = ImagesetMetaData(imagefile=orig_file)
            logging.debug(f"exif source: {metadata.source}")
            logging.debug(f"exif data: {metadata.data}")
            
            # Set the source at top level
            if metadata.source:
                self.toml.set(key="source", value=metadata.source)
                # Only create a section if we have a valid source name
                self.toml.set(section=metadata.source, value=metadata.data)
            else:
                # No specific source detected, store as other data
                self.toml.set(key="source", value="other")
                self.toml.set(section="other", value=metadata.data)
            
    def _get_imageset_folder(self):
        if not os.path.exists(self.folder_name):
            logging.error(f"Base folder not found: {self.folder_name}")
            raise FileNotFoundError(f"Base folder not found: {self.folder_name}")

        imageset_folder = os.path.join(self.folder_name, self.imageset_name)            
        
        if not os.path.exists(imageset_folder):
            logging.error(f"Imageset Folder does not exist: {imageset_folder}")
            raise FileNotFoundError(f"Imageset Folder does not exist: {imageset_folder}")
        
        return(imageset_folder)
        
    def _get_imageset_files(self):
        """get the files in the imageset folder. returns a dict with this structure... dict{filename: dict{fullpath, ext, tags}}"""
        
        files = {}
        
        tags = self.config.get_file_tags()
        
        imageset_folder = self.imageset_folder
        
        try:
            if not os.path.exists(imageset_folder):
                logging.error(f"Imageset folder does not exist: {imageset_folder}")
                raise FileNotFoundError(f"Imageset folder does not exist: {imageset_folder}")
                
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
                        
                # decide on a file_type
                file_type = "other"
                
                if file_ext == ".toml":
                    file_type = "toml"

                if file_ext == ".txt":
                    file_type = "text"

                if "interview" in file_name:
                    file_type = "interview"
                    
                if file_ext[1:] in self.config.config_data["img_file_ext"]:
                    file_type = "image"
                
                        
                # load the file into the files dict
                files[file_name] = {"fullpath": file_path, "ext": file_ext, "tags": file_tags, "file_type": file_type}
                        
            return files
            
        except Exception as e:
            logging.error(f"Error getting files for imageset {self.imageset_name}: {e}", exc_info=True)
            raise RuntimeError(f"Error getting files for imageset {self.imageset_name}: {e}")
        
    def get_file_interview(self) -> str:
        """Get the full path of the interview file if it exists."""
        
        try:
            for filename, file_info in self.files.items():
                if filename.endswith("_interview.txt"):
                    logging.debug(f"Found interview file: {filename}")
                    return file_info["fullpath"]
            
            logging.debug("No interview file found in imageset")
            return None
            
        except Exception as e:
            logging.error(f"Error finding interview file: {e}", exc_info=True)
            return None

    def has_file_thumb(self) -> bool:
        # TODO: implement this
        pass
    
    def has_file_toml(self) -> bool:
        # TODO: implement this
        pass


    def interview_image(self, version: str = "orig"):
        """Create interview files for the imageset using AI analysis."""
        
        interview_file = self.get_file_interview()
        
        if interview_file:
            logging.info(f"Interview file already created: {interview_file}")
            return interview_file
        
        # Get valid image file extensions from config
        img_file_ext = self.config.config_data["img_file_ext"]
        
        try:
            # Find the best image file for interview
            selected_image = self._find_best_image_for_interview(version, img_file_ext)
            if not selected_image:
                logging.error(f"No suitable image file found with version '{version}'")
                return None
            
            # Check file size and create thumbnail if needed
            final_image = self._prepare_image_for_interview(selected_image)
            if not final_image:
                logging.error("Failed to prepare image for interview")
                return None
            
            # Import and run the interview process
            from img_catalog_tui.core.imageset_interview import Interview
            
            interview = Interview(config=self.config, image_file=final_image)
            
            # Execute the complete interview workflow
            interview.interview_image()
            
            logging.info(f"Interview process completed for imageset: {self.imageset_name}")
            return interview.interview_parsed
            
        except Exception as e:
            logging.error(f"Error during interview process: {e}", exc_info=True)
            return None
        finally:
            # Refresh the files list to include any newly created files
            self.files = self._get_imageset_files()
    
    def _find_best_image_for_interview(self, version: str, valid_extensions: list) -> str:
        """Find the smallest image file with the specified version tag."""
        
        try:
            candidates = []
            
            # Find all files that match the criteria
            for filename, file_info in self.files.items():
                file_ext = file_info["ext"].lower().lstrip('.')
                file_tags = file_info["tags"]
                file_path = file_info["fullpath"]
                
                # Check if file has valid image extension
                if file_ext not in [ext.lower() for ext in valid_extensions]:
                    continue
                
                # Check if file has the required version tag
                if version not in file_tags:
                    continue
                
                # Get file size
                try:
                    file_size = os.path.getsize(file_path)
                    candidates.append({
                        "path": file_path,
                        "size": file_size,
                        "filename": filename
                    })
                except OSError as e:
                    logging.warning(f"Could not get size for file {file_path}: {e}")
                    continue
            
            if not candidates:
                logging.debug(f"No image files found with version tag '{version}'")
                return None
            
            # Sort by file size (smallest first)
            candidates.sort(key=lambda x: x["size"])
            
            selected = candidates[0]
            logging.info(f"Selected image for interview: {selected['filename']} ({selected['size']} bytes)")
            return selected["path"]
            
        except Exception as e:
            logging.error(f"Error finding best image for interview: {e}", exc_info=True)
            return None
    
    def _prepare_image_for_interview(self, image_path: str) -> str:
        """Check file size and create thumbnail if needed."""
        
        try:
            file_size = os.path.getsize(image_path)
            size_limit = 2 * 1024 * 1024  # 2MB in bytes
            
            logging.debug(f"Image file size: {file_size} bytes (limit: {size_limit} bytes)")
            
            # If file is within size limit, use original
            if file_size <= size_limit:
                logging.info(f"Image file size acceptable, using original: {image_path}")
                return image_path
            
            # File is too large, create thumbnail
            logging.info(f"Image file too large ({file_size} bytes), creating thumbnail")
            return self._create_thumbnail_for_interview(image_path)
            
        except Exception as e:
            logging.error(f"Error preparing image for interview: {e}", exc_info=True)
            return None
    
    def _create_thumbnail_for_interview(self, image_path: str) -> str:
        """Create a thumbnail of the image for interview purposes."""
        
        try:
            from PIL import Image
            
            # Generate thumbnail filename
            base_dir = os.path.dirname(image_path)
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            thumb_filename = f"{base_name}_interview_thumb.png"
            thumb_path = os.path.join(base_dir, thumb_filename)
            
            # Check if thumbnail already exists
            if os.path.exists(thumb_path):
                thumb_size = os.path.getsize(thumb_path)
                if thumb_size <= 2 * 1024 * 1024:  # 2MB limit
                    logging.info(f"Using existing thumbnail: {thumb_path}")
                    return thumb_path
            
            # Create new thumbnail
            with Image.open(image_path) as img:
                # Calculate thumbnail size to stay under 2MB
                # Start with a reasonable max dimension
                max_dimension = 1024
                
                while max_dimension > 256:  # Don't go too small
                    # Calculate proportional dimensions
                    ratio = min(max_dimension / img.width, max_dimension / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    
                    # Create thumbnail
                    thumbnail = img.copy()
                    thumbnail.thumbnail(new_size, Image.Resampling.LANCZOS)
                    
                    # Save temporary file to check size
                    temp_path = thumb_path + ".tmp"
                    thumbnail.save(temp_path, "PNG", optimize=True)
                    
                    temp_size = os.path.getsize(temp_path)
                    
                    if temp_size <= 2 * 1024 * 1024:  # Under 2MB
                        # Move temp file to final location
                        if os.path.exists(thumb_path):
                            os.remove(thumb_path)
                        os.rename(temp_path, thumb_path)
                        
                        logging.info(f"Created thumbnail: {thumb_path} ({temp_size} bytes)")
                        return thumb_path
                    else:
                        # Remove temp file and try smaller
                        os.remove(temp_path)
                        max_dimension = int(max_dimension * 0.8)
                
                # If we get here, even 256px is too large - use minimum quality
                thumbnail = img.copy()
                thumbnail.thumbnail((256, 256), Image.Resampling.LANCZOS)
                thumbnail.save(thumb_path, "PNG", optimize=True, quality=10)
                
                final_size = os.path.getsize(thumb_path)
                logging.warning(f"Created minimal quality thumbnail: {thumb_path} ({final_size} bytes)")
                return thumb_path
                
        except Exception as e:
            logging.error(f"Error creating thumbnail for interview: {e}", exc_info=True)
            return None
                
                



if __name__ == "__main__":
    
    config = Config()
    setup_logging()
    
    folder = r"E:\fooocus\images\new\2025-08-17\_needs creative"
    imageset_name = "2025-08-17_02-33-34_5812"
    #imageset_name = "aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_0"
    
    imageset = Imageset(config=config, folder_name=folder, imageset_name=imageset_name)
    print(imageset.orig_image)
    # imageset.interview_image()
    
    