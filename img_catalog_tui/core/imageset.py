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
        self.files = self._get_imageset_files() # dict{filename: dict{fullpath, ext, tags}}

        self.get_exif_data()
        
    def get_exif_data(self):
        
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
            
            metadata = ImagesetMetaData(imagefile=self.get_file_orig())
            logging.debug(f"exif source: {metadata.source}")
            logging.debug(f"exif data: {metadata.data}")
            
            self.toml.set(key="source", value=metadata.source)
            self.toml.set(section=metadata.source, value=metadata.data)
            
    def get_file_orig(self):
        """Get the first file in the imageset folder that contains '_orig' in its filename."""
        
        try:
            for filename, file_info in self.files.items():
                if "_orig" in filename:
                    logging.debug(f"Found orig file: {filename}")
                    return file_info["fullpath"]
            
            logging.debug("No orig file found in imageset")
            return None
            
        except Exception as e:
            logging.error(f"Error finding orig file: {e}", exc_info=True)
            return None
        
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
        
        files = {}
        
        tags = self.config.get_file_tags()
        
        imageset_folder = os.path.join(self.folder_name, self.imageset_name)
        
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
                        
                # load the file into the files dict
                files[file_name] = {"fullpath": file_path, "ext": file_ext, "tags": file_tags}
                        
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
        pass
    
    def has_file_toml(self) -> bool:
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
            interview.save_raw_interview()
            interview.save_text_interview()
            interview.parse_interview()
            interview.save_json_interview()
            
            logging.info(f"Interview process completed for imageset: {self.imageset_name}")
            return interview.save_text_interview()
            
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
    config.load()
    setup_logging()
    
    folder = r"E:\fooocus\images\new\2025-08-03_tmp"
    imageset_name = "2025-08-03_00-00-23_7134"
    #imageset_name = "aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_0"
    
    imageset = Imageset(config=config, folder_name=folder, imageset_name=imageset_name)
    imageset.interview_image()
    
    