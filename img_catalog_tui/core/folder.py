import logging
import os

from img_catalog_tui.utils.file_utils import (
    create_folder, get_imageset_from_filename, is_image_file, move_files, move_folder
)

from img_catalog_tui.config import Config
from img_catalog_tui.logger import setup_logging
from img_catalog_tui.core.imageset import Imageset



class ImagesetFolder:
    
    def __init__(self, config: Config, foldername: str):
        
        self.foldername = self._validate_foldername(foldername)
        self.config = config
        self.imagesets: dict[str, Imageset] = {}
        self.folder_scan()
        
        
    def _validate_foldername(self, foldername: str):
        if os.path.exists(foldername) and os.path.isdir(foldername):
            return foldername
        else:
            raise FileNotFoundError(f"Folder does not exist: {foldername}")
        
    def to_dict(self):
        return {
            'foldername': self.foldername,
            'imagesets': list(self.imagesets.keys())
        }
        
    def folder_scan(self) -> bool:
        """ Scan a folder for imagesets and process them. """

        try:
            folder_name = self.foldername

            logging.info(f"Scanning folder: {folder_name}")
            
            # Get folder contents
            
            subfolders = []
            loose_files = []
            
            try:
                for item in os.listdir(self.foldername):
                    # Skip items starting with underscore
                    if item.startswith("_") or item.startswith("index."):
                        continue
                    
                    item_path = os.path.join(self.foldername, item)
                    
                    if os.path.isdir(item_path):
                        subfolders.append(item)
                        logging.debug(f"Found subfolder: {item}")
                    elif os.path.isfile(item_path):
                        loose_files.append(item)
                        logging.debug(f"Found loose file: {item}")
                        
                logging.info(f"Found {len(subfolders)} subfolders and {len(loose_files)} loose files")
                
            except OSError as e:
                logging.error(f"Error reading folder {self.foldername}: {e}", exc_info=True)
                return False



            # Manage Loose Files
            
            # Get file tags from config
            file_tags = self.config.get_file_tags()
            
            for loose_file in loose_files:
                try:
                    # Check if the file still exists
                    file_path = os.path.join(self.foldername, loose_file)
                    if not os.path.exists(file_path):
                        logging.warning(f"File no longer exists: {loose_file}")
                        continue
                    
                    # Skip non-image files
                    if not is_image_file(file_path):
                        logging.debug(f"Skipping non-image file: {loose_file}")
                        continue
                    
                    # Get the imageset_name using get_imageset_from_filename func
                    imageset_name, _, _ = get_imageset_from_filename(loose_file, file_tags)
                    
                    # Check if there's already a folder for that imageset
                    imageset_folder_path = os.path.join(self.foldername, imageset_name)
                    if not os.path.exists(imageset_folder_path):
                        # Create the folder and add it to subfolders list
                        if create_folder(imageset_folder_path):
                            subfolders.append(imageset_name)
                            logging.info(f"Created imageset folder: {imageset_name}")
                        else:
                            logging.error(f"Failed to create folder for imageset: {imageset_name}")
                            continue
                    
                    # Move all files where "*<imagesetname>*" to its subfolder
                    moved_files = move_files(imageset_name, self.foldername, imageset_folder_path)
                    if moved_files:
                        logging.info(f"Moved {len(moved_files)} files for imageset: {imageset_name}")
                    
                except Exception as e:
                    logging.error(f"Error processing loose file {loose_file}: {e}", exc_info=True)
                    continue 
            
            
            # Manage subfolders

            # Archive abandoned folders
            subfolders = self.archive_abandoned_folders(imagesets=subfolders)
            
            for imageset_name in subfolders:
                imageset_obj = Imageset(config=self.config, folder_name=self.foldername, imageset_name=imageset_name)
                
                if imageset_obj.status != "archive":
                    self.imagesets[imageset_name] = imageset_obj
                else:
                    logging.info(f"imageset {imageset_name} is status=archived so it did not get loaded into this folder.")
            
            logging.info(f"Folder scan completed for {folder_name}")
            return True
            
        except Exception as e:
            logging.error(f"Error scanning folder: {e}", exc_info=True)
            return False

        
        
        
    



    def archive_abandoned_folders(self, imagesets: list[str]) -> list[str]:
        """
        Archive folders that have no image files.
        """
        logging.debug(f"Checking for abandoned folders in {self.foldername}")
        imagesets_to_archive = []
        imagesets_remaining = []
        
        try:
            for imageset in imagesets:
                imageset_folder = os.path.join(self.foldername, imageset)
                
                # Check if folder has any image files
                has_images = False
                for file_name in os.listdir(imageset_folder):
                    file_path = os.path.join(imageset_folder, file_name)
                    if os.path.isfile(file_path) and is_image_file(file_path):
                        has_images = True
                        break
                        
                # If no images found, mark for deletion
                if has_images:
                    imagesets_remaining.append(imageset)
                else:
                    imagesets_to_archive.append(imageset)
                    
            # Delete abandoned folders
            if imagesets_to_archive:
                
                archive_folder = os.path.join(self.foldername, "_archive")
                
                if not os.path.exists(archive_folder):
                    create_folder(archive_folder)
                
                for imageset in imagesets_to_archive:
                    folder_to_archive = os.path.join(self.foldername, imageset)
                    if move_folder(source_folder=folder_to_archive, target_folder=archive_folder):
                        logging.info(f"Archived abandoned folder: {imageset}")
                        
                
            return imagesets_remaining
            
        except Exception as e:
            logging.error(f"Error deleting abandoned folders in {self.foldername}: {e}", exc_info=True)
            return imagesets


if __name__ == "__main__":
    
    config = Config()
    setup_logging()
    
    foldername = r"E:\\fooocus\\images\\new\\2025-08-03_tmp"
    
    folder = ImagesetFolder(config=config, foldername=foldername)