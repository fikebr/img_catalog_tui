import logging
import os

from img_catalog_tui.utils.file_utils import (
    create_folder, get_imageset_from_filename, is_image_file, move_files, move_folder
)

from img_catalog_tui.config import Config
from img_catalog_tui.logger import setup_logging
from img_catalog_tui.core.imageset import Imageset
from img_catalog_tui.core.folders import Folders


def list_imagesets_db(
    config: Config,
    folder_path: str,
    include_archived: bool = False,
) -> list[dict]:
    """
    List imagesets for a folder using the database (DB-first).

    Args:
        config: App config
        folder_path: Full filesystem folder path (parent folder)
        include_archived: Include status=archive rows when True

    Returns:
        List of imageset rows (dicts). Empty list on errors/not found.
    """
    try:
        from img_catalog_tui.db.utils import init_database
        from img_catalog_tui.db.folders import FoldersTable
        from img_catalog_tui.db.imagesets import ImagesetsTable

        init_database(config)
        folders_table = FoldersTable(config)
        folder_row = folders_table.get_by_path(folder_path)
        if not folder_row:
            folder_name = os.path.basename(folder_path.rstrip("\\/"))
            folder_row = folders_table.get_by_name(folder_name)
        if not folder_row:
            return []

        imagesets_table = ImagesetsTable(config)
        rows = imagesets_table.get_by_folder_id(folder_row["id"])
        if include_archived:
            return rows

        return [row for row in rows if (row.get("status") or "").lower() != "archive"]
    except Exception as e:
        logging.error(f"Failed to list imagesets from DB for folder '{folder_path}': {e}", exc_info=True)
        return []


def summarize_imagesets_by_status(imagesets: list[dict]) -> dict[str, int]:
    """Build a status->count summary for a list of DB imageset rows."""
    counts: dict[str, int] = {}
    for row in imagesets:
        status = (row.get("status") or "").strip() or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts



def folder_scan(args: dict, config: Config) -> bool:
    """
    TUI command: scan a folder on disk to (a) organize loose files into imagesets,
    and (b) ensure DB records exist for discovered imagesets.

    Accepts either a folder registry name (DB folders.name) or a full folder path.

    This is an explicit/manual refresh and will:
    - ensure the folder exists in the DB registry
    - scan/organize the filesystem using `ImagesetFolder.folder_scan()`
    - refresh filesystem -> DB file records for each imageset found
    """
    folder_input = (args or {}).get("folder_name") or ""
    folder_input = str(folder_input).strip()

    if not folder_input:
        logging.error("folder_scan missing required arg: folder_name")
        return False

    try:
        folders = Folders(config=config)
        if folder_input in folders.folders:
            folder_path = folders.folders[folder_input]
        else:
            folder_path = folder_input
            # If the user typed a full path, ensure it's registered in DB.
            folders.add(folder_path)
            folders.export_to_toml()

        if not folder_path or not os.path.isdir(folder_path):
            logging.error("folder_scan folder does not exist or is not a directory: %s", folder_path)
            return False

        logging.info("Starting folder_scan for: %s", folder_path)
        folder_obj = ImagesetFolder(config=config, foldername=folder_path)

        refreshed = 0
        for imageset_name, imageset_obj in folder_obj.imagesets.items():
            try:
                if imageset_obj.refresh_files_from_fs():
                    refreshed += 1
            except Exception as e:
                logging.warning("Failed to refresh files for imageset '%s': %s", imageset_name, e)

        logging.info("folder_scan complete: imagesets=%s refreshed=%s", len(folder_obj.imagesets), refreshed)
        return True
    except Exception as e:
        logging.error(f"folder_scan failed: {e}", exc_info=True)
        return False


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
                        
                        # Sync the archived imageset location to database
                        self._sync_archived_imageset_to_db(imageset, archive_folder)
                
            return imagesets_remaining
            
        except Exception as e:
            logging.error(f"Error deleting abandoned folders in {self.foldername}: {e}", exc_info=True)
            return imagesets
    
    def _sync_archived_imageset_to_db(self, imageset_name: str, archive_folder: str) -> None:
        """Sync an archived imageset's location to the database.
        
        This method attempts to sync archived imageset changes to the database.
        Errors are logged but don't interrupt execution (graceful degradation).
        
        Args:
            imageset_name: The imageset name
            archive_folder: Full path to the archive folder
        """
        try:
            from img_catalog_tui.db.sync import sync_imageset_toml_to_db
            
            imageset_id = sync_imageset_toml_to_db(
                config=self.config,
                folder_path=archive_folder,
                imageset_name=imageset_name
            )
            
            if imageset_id:
                logging.debug(f"Synced archived imageset '{imageset_name}' to database (ID: {imageset_id})")
            else:
                logging.warning(f"Database sync returned no ID for archived imageset '{imageset_name}'")
                
        except ImportError:
            # Database module not available, skip sync
            logging.debug("Database sync skipped: db.sync module not available")
        except Exception as e:
            # Log error but continue - graceful degradation
            logging.warning(f"Failed to sync archived imageset '{imageset_name}' to database: {e}")


if __name__ == "__main__":
    
    config = Config()
    setup_logging()
    
    foldername = r"E:\fooocus\images\new\mj 2025-05-08"
    imageset_name = "A_blonde_woman_with_a_black_hoodie_standing_on__3"
    
    folder = ImagesetFolder(config=config, foldername=foldername)
    imageset = folder.imagesets[imageset_name]
    logging.debug(f"===== {imageset_name} : {imageset.to_dict()} =====")