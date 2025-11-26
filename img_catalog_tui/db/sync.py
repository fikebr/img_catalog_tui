"""
Synchronization functions for TOML <-> Database migration and sync.
"""

import os
import json
import logging
import tomllib
from pathlib import Path
from typing import Optional, Dict, List

from img_catalog_tui.config import Config
from img_catalog_tui.core.imageset_toml import ImagesetToml
from img_catalog_tui.db.utils import init_database, get_db_path
from img_catalog_tui.db.folders import FoldersTable
from img_catalog_tui.db.imagesets import ImagesetsTable
from img_catalog_tui.db.imageset_sections import ImagesetSectionsTable
from img_catalog_tui.db.interviews import InterviewsTable
from img_catalog_tui.db.imagesetfiles import ImagesetFilesTable
from img_catalog_tui.db.imagesetfile_tags import ImagesetFileTagsTable


def sync_folders_toml_to_db(config: Config) -> bool:
    """
    Sync folders from TOML file to database.
    
    Args:
        config: Configuration object
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logging.info("Starting sync: TOML folders -> Database")
        
        # Initialize database if needed
        init_database(config)
        
        # Load folders from TOML
        folders_toml_path = Path(__file__).parent / "folders.toml"
        if not folders_toml_path.exists():
            logging.warning(f"folders.toml not found at {folders_toml_path}")
            return False
        
        import toml
        with open(folders_toml_path, 'r', encoding='utf-8') as f:
            toml_data = toml.load(f)
        
        folders_dict = toml_data.get("folders", {})
        
        # Sync to database
        folders_table = FoldersTable(config)
        synced_count = 0
        
        for name, path in folders_dict.items():
            # Check if folder already exists
            existing = folders_table.get_by_name(name)
            if existing:
                # Update if path changed
                if existing['path'] != path:
                    folders_table.update(existing['id'], path=path)
                    logging.debug(f"Updated folder: {name}")
            else:
                # Create new
                folders_table.create(name, path)
                logging.debug(f"Created folder: {name}")
            synced_count += 1
        
        logging.info(f"Synced {synced_count} folders from TOML to database")
        return True
        
    except Exception as e:
        logging.error(f"Failed to sync folders from TOML to DB: {e}", exc_info=True)
        return False


def sync_folders_db_to_toml(config: Config) -> bool:
    """
    Sync folders from database to TOML file.
    
    Args:
        config: Configuration object
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logging.info("Starting sync: Database folders -> TOML")
        
        folders_table = FoldersTable(config)
        folders_dict = folders_table.get_all_dict()
        
        # Write to TOML
        folders_toml_path = Path(__file__).parent / "folders.toml"
        
        import toml
        toml_data = {"folders": folders_dict}
        
        with open(folders_toml_path, 'w', encoding='utf-8') as f:
            toml.dump(toml_data, f)
        
        logging.info(f"Synced {len(folders_dict)} folders from database to TOML")
        return True
        
    except Exception as e:
        logging.error(f"Failed to sync folders from DB to TOML: {e}", exc_info=True)
        return False


def sync_imageset_toml_to_db(config: Config, folder_path: str, imageset_name: str) -> Optional[int]:
    """
    Sync a single imageset from TOML to database.
    
    Args:
        config: Configuration object
        folder_path: Full path to parent folder
        imageset_name: Imageset name
        
    Returns:
        int: Imageset ID if successful, None otherwise
    """
    try:
        imageset_folder = os.path.join(folder_path, imageset_name)
        
        if not os.path.exists(imageset_folder):
            logging.warning(f"Imageset folder does not exist: {imageset_folder}")
            return None
        
        # Load TOML data
        toml_obj = ImagesetToml(imageset_folder=imageset_folder)
        toml_data = toml_obj.get()
        
        # Get folder ID
        folders_table = FoldersTable(config)
        folder_name = os.path.basename(folder_path)
        folder_record = folders_table.get_by_name(folder_name)
        
        if not folder_record:
            # Try to find by path
            folder_record = folders_table.get_by_path(folder_path)
            if not folder_record:
                logging.error(f"Folder not found in database: {folder_path}")
                return None
        
        folder_id = folder_record['id']
        
        # Create or update imageset
        imagesets_table = ImagesetsTable(config)
        existing = imagesets_table.get_by_folder_path_and_name(folder_path, imageset_name)
        
        # Extract top-level fields
        status = toml_data.get("status", "")
        edits = toml_data.get("edits", "")
        needs = toml_data.get("needs", "")
        source = toml_data.get("source", "")
        
        # Get prompt from source section
        prompt = ""
        if source and source in toml_data:
            source_section = toml_data[source]
            if isinstance(source_section, dict):
                prompt = source_section.get("prompt", "")
        
        # Get good_for and posted_to from biz section
        good_for = ""
        posted_to = ""
        biz_section = toml_data.get("biz", {})
        if isinstance(biz_section, dict):
            good_for = biz_section.get("good_for", "")
            posted_to = biz_section.get("posted_to", "")
        
        # Calculate paths
        imageset_folder_path = os.path.join(folder_path, imageset_name)
        
        if existing:
            # Update existing
            imagesets_table.update(
                existing['id'],
                status=status,
                edits=edits,
                needs=needs,
                good_for=good_for,
                source=source,
                prompt=prompt
            )
            imageset_id = existing['id']
        else:
            # Create new
            imageset_id = imagesets_table.create(
                folder_id=folder_id,
                name=imageset_name,
                folder_path=folder_path,
                imageset_folder_path=imageset_folder_path,
                status=status,
                edits=edits,
                needs=needs,
                good_for=good_for,
                source=source,
                prompt=prompt
            )
        
        if not imageset_id:
            return None
        
        # Sync sections
        sections_table = ImagesetSectionsTable(config)
        
        # Sync all sections except top-level fields
        top_level_keys = {"imageset", "status", "edits", "needs", "source"}
        
        for section_name, section_data in toml_data.items():
            if section_name in top_level_keys:
                continue
            
            if isinstance(section_data, dict):
                sections_table.update(imageset_id, section_name, section_data)
        
        # Sync files
        files_table = ImagesetFilesTable(config)
        files_table.sync_from_filesystem(imageset_id, imageset_folder_path, config)
        
        # Extract tags from filenames and sync
        tags_table = ImagesetFileTagsTable(config)
        files = files_table.get_by_imageset_id(imageset_id)
        
        for file_record in files:
            filename = file_record['filename']
            file_id = file_record['id']
            
            # Extract tags from filename
            tags = []
            file_tags = config.get_file_tags()
            for tag in file_tags:
                if f"_{tag}_" in filename or f"_{tag}." in filename:
                    tags.append(tag)
            
            if tags:
                tags_table.set_tags_for_file(file_id, tags)
        
        # Calculate and update cover_image_path and orig_image_path
        cover_image_path = None
        orig_image_path = None
        
        # Get image files
        img_file_ext = config.config_data.get("img_file_ext", [])
        image_files = [f for f in files if f['file_type'] == 'image']
        
        if image_files:
            # Find cover image (priority: thumb > orig > any image)
            thumb_files = []
            orig_files = []
            other_files = []
            
            for file_record in image_files:
                file_tags = tags_table.get_tags_by_file_id(file_record['id'])
                if 'thumb' in file_tags:
                    thumb_files.append(file_record['fullpath'])
                elif 'orig' in file_tags:
                    orig_files.append(file_record['fullpath'])
                    # Set orig_image_path to first orig file found
                    if not orig_image_path:
                        orig_image_path = file_record['fullpath']
                else:
                    other_files.append(file_record['fullpath'])
            
            # Set cover_image_path (priority: thumb > orig > any)
            if thumb_files:
                cover_image_path = thumb_files[0]
            elif orig_files:
                cover_image_path = orig_files[0]
            elif other_files:
                cover_image_path = other_files[0]
        
        # Update imageset with image paths
        if cover_image_path or orig_image_path:
            imagesets_table.update(
                imageset_id,
                cover_image_path=cover_image_path,
                orig_image_path=orig_image_path
            )
            logging.debug(f"Updated image paths for imageset {imageset_name}: cover={cover_image_path}, orig={orig_image_path}")
        
        # Sync interview files if they exist
        _sync_interview_files(config, imageset_id, imageset_folder_path)
        
        logging.debug(f"Synced imageset {imageset_name} from TOML to database")
        return imageset_id
        
    except Exception as e:
        logging.error(f"Failed to sync imageset {imageset_name} from TOML to DB: {e}", exc_info=True)
        return None


def sync_imageset_db_to_toml(config: Config, folder_path: str, imageset_name: str) -> bool:
    """
    Sync a single imageset from database to TOML.
    
    Args:
        config: Configuration object
        folder_path: Full path to parent folder
        imageset_name: Imageset name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        imageset_folder = os.path.join(folder_path, imageset_name)
        
        # Get imageset from database
        imagesets_table = ImagesetsTable(config)
        imageset = imagesets_table.get_by_folder_path_and_name(folder_path, imageset_name)
        
        if not imageset:
            logging.warning(f"Imageset not found in database: {imageset_name}")
            return False
        
        imageset_id = imageset['id']
        
        # Get sections
        sections_table = ImagesetSectionsTable(config)
        sections = sections_table.get_by_imageset_id(imageset_id)
        
        # Create TOML object
        toml_obj = ImagesetToml(imageset_folder=imageset_folder)
        
        # Update top-level fields
        if imageset['status']:
            toml_obj.set(key="status", value=imageset['status'])
        if imageset['edits']:
            toml_obj.set(key="edits", value=imageset['edits'])
        if imageset['needs']:
            toml_obj.set(key="needs", value=imageset['needs'])
        if imageset['source']:
            toml_obj.set(key="source", value=imageset['source'])
        
        # Update sections
        for section in sections:
            section_name = section['section_name']
            section_data = section['section_data']
            
            if section_data:
                toml_obj.set(section=section_name, value=section_data)
        
        logging.debug(f"Synced imageset {imageset_name} from database to TOML")
        return True
        
    except Exception as e:
        logging.error(f"Failed to sync imageset {imageset_name} from DB to TOML: {e}", exc_info=True)
        return False


def sync_all_imagesets_toml_to_db(config: Config, folder_path: Optional[str] = None) -> int:
    """
    Sync all imagesets from TOML to database.
    
    Args:
        config: Configuration object
        folder_path: Optional specific folder path, otherwise syncs all folders
        
    Returns:
        int: Number of imagesets synced
    """
    try:
        logging.info("Starting sync: All TOML imagesets -> Database")
        
        folders_table = FoldersTable(config)
        
        if folder_path:
            # Sync specific folder
            folder_name = os.path.basename(folder_path)
            folder_record = folders_table.get_by_name(folder_name) or folders_table.get_by_path(folder_path)
            if not folder_record:
                logging.error(f"Folder not found: {folder_path}")
                return 0
            folders_to_sync = [folder_record]
        else:
            # Sync all folders
            folders_to_sync = folders_table.get_all()
        
        synced_count = 0
        
        for folder_record in folders_to_sync:
            folder_path = folder_record['path']
            
            if not os.path.exists(folder_path):
                logging.warning(f"Folder path does not exist: {folder_path}")
                continue
            
            # Scan for imageset folders
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                
                # Skip special folders and files
                if item.startswith("_") or item.startswith("index."):
                    continue
                
                if os.path.isdir(item_path):
                    # Check if it has a TOML file
                    toml_file = os.path.join(item_path, f"{item}.toml")
                    if os.path.exists(toml_file):
                        imageset_id = sync_imageset_toml_to_db(config, folder_path, item)
                        if imageset_id:
                            synced_count += 1
        
        logging.info(f"Synced {synced_count} imagesets from TOML to database")
        return synced_count
        
    except Exception as e:
        logging.error(f"Failed to sync all imagesets from TOML to DB: {e}", exc_info=True)
        return 0


def _sync_interview_files(config: Config, imageset_id: int, imageset_folder_path: str) -> None:
    """
    Sync interview files from filesystem to database.
    
    Args:
        config: Configuration object
        imageset_id: Imageset ID
        imageset_folder_path: Full path to imageset folder
    """
    try:
        interviews_table = InterviewsTable(config)
        files_table = ImagesetFilesTable(config)
        
        # Find interview files
        interview_files = files_table.get_by_file_type(imageset_id, "interview")
        
        for file_record in interview_files:
            filename = file_record['filename']
            file_path = file_record['fullpath']
            
            # Determine interview type from filename
            if filename.endswith("_interview.txt"):
                # Read interview response
                interview_response = None
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        interview_response = f.read()
                
                # Look for corresponding raw and parsed files
                base_name = filename.replace("_interview.txt", "")
                raw_file = f"{base_name}_interview_raw.txt"
                parsed_file = f"{base_name}_interview.json"
                
                interview_raw = None
                interview_parsed = None
                
                raw_path = os.path.join(imageset_folder_path, raw_file)
                parsed_path = os.path.join(imageset_folder_path, parsed_file)
                
                if os.path.exists(raw_path):
                    with open(raw_path, 'r', encoding='utf-8') as f:
                        try:
                            interview_raw = json.loads(f.read())
                        except json.JSONDecodeError:
                            pass
                
                if os.path.exists(parsed_path):
                    with open(parsed_path, 'r', encoding='utf-8') as f:
                        try:
                            interview_parsed = json.loads(f.read())
                        except json.JSONDecodeError:
                            pass
                
                # Find the image file used (extract from base_name)
                image_file_path = None
                # Try to find the original image
                all_files = files_table.get_by_imageset_id(imageset_id)
                for f in all_files:
                    if f['file_type'] == 'image' and 'orig' in f['filename']:
                        image_file_path = f['fullpath']
                        break
                
                if not image_file_path:
                    # Fall back to any image file
                    for f in all_files:
                        if f['file_type'] == 'image':
                            image_file_path = f['fullpath']
                            break
                
                if image_file_path:
                    # Check if interview already exists
                    existing = interviews_table.get_by_imageset_id(imageset_id)
                    if not existing:
                        interviews_table.create(
                            imageset_id=imageset_id,
                            interview_template="default",  # Could be extracted from filename or config
                            image_file_path=image_file_path,
                            interview_response=interview_response,
                            interview_raw=interview_raw,
                            interview_parsed=interview_parsed
                        )
        
    except Exception as e:
        logging.error(f"Failed to sync interview files for imageset {imageset_id}: {e}", exc_info=True)


def sync_interview_db_to_files(config: Config, imageset_id: int, imageset_folder_path: str) -> bool:
    """
    Sync interview from database to filesystem files.
    
    Args:
        config: Configuration object
        imageset_id: Imageset ID
        imageset_folder_path: Full path to imageset folder
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        interviews_table = InterviewsTable(config)
        interview = interviews_table.get_latest_by_imageset_id(imageset_id)
        
        if not interview:
            return True  # No interview to sync
        
        # Determine base filename from image_file_path
        image_file_path = interview['image_file_path']
        base_name = os.path.splitext(os.path.basename(image_file_path))[0]
        
        # Write interview response
        if interview['interview_response']:
            response_file = os.path.join(imageset_folder_path, f"{base_name}_interview.txt")
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(interview['interview_response'])
        
        # Write raw response
        if interview['interview_raw']:
            raw_file = os.path.join(imageset_folder_path, f"{base_name}_interview_raw.txt")
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(interview['interview_raw'], indent=2))
        
        # Write parsed response
        if interview['interview_parsed']:
            parsed_file = os.path.join(imageset_folder_path, f"{base_name}_interview.json")
            with open(parsed_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(interview['interview_parsed'], indent=2))
        
        logging.debug(f"Synced interview from database to files for imageset {imageset_id}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to sync interview from DB to files for imageset {imageset_id}: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    """
    Entry point for running database synchronization as a module.
    
    Usage:
        uv run -m img_catalog_tui.db.sync
    """
    import sys
    
    # Set up logging
    from img_catalog_tui.logger import setup_logging
    setup_logging()
    
    # Load configuration
    from img_catalog_tui.config import Config
    
    try:
        logging.info("Starting database synchronization from TOML...")
        config = Config()
        
        # Sync folders first
        logging.info("Syncing folders from TOML to database...")
        if sync_folders_toml_to_db(config):
            print("✓ Folders synced successfully")
        else:
            print("✗ Failed to sync folders")
            sys.exit(1)
        
        # Sync all imagesets
        logging.info("Syncing imagesets from TOML to database...")
        count = sync_all_imagesets_toml_to_db(config)
        
        if count >= 0:
            print(f"✓ Synced {count} imagesets successfully")
            logging.info(f"Database synchronization completed. Synced {count} imagesets.")
            sys.exit(0)
        else:
            print("✗ Failed to sync imagesets")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logging.error(f"Configuration file not found: {e}", exc_info=True)
        print(f"✗ Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error during synchronization: {e}", exc_info=True)
        print(f"✗ Error during synchronization: {e}")
        sys.exit(1)

