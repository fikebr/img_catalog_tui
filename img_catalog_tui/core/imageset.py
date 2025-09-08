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
        self.files = self._get_imageset_files() # dict{filename: dict{fullpath, ext, tags}}

        self.toml = ImagesetToml(imageset_folder=self.imageset_folder)
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
        
    def has_file_orig(self) -> bool:
        pass

    def has_file_interview(self) -> bool:
        pass

    def has_file_thumb(self) -> bool:
        pass
    
    def has_file_toml(self) -> bool:
        pass



                
                



if __name__ == "__main__":
    
    config = Config()
    config.load()
    setup_logging()
    
    folder = r"E:\fooocus\images\new\2025-08-03_tmp"
    imageset_name = "2025-08-03_00-00-23_7134"
    #imageset_name = "aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_0"
    
    imageset = Imageset(config=config, folder_name=folder, imageset_name=imageset_name)
    
    #imageset.get_exif_data()