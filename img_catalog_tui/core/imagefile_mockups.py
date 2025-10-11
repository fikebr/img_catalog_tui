from subprocess import run

from img_catalog_tui.config import Config

# run([r"C:\Program Files\Adobe\Adobe Photoshop 2025\Photoshop.exe", "-r", "temp.jsx"])

class ImageMockups:
    
    def __init__(self, config: Config, image_file_path: str, mockup_folder_name: str):
        
        self.config = config
        self.mockup_cfg: dict = self.config.config_data.get("mockups", {})
        self.image_file_path = self._validate_image_file(image_file_path)
        self.mockup_folder_name = mockup_folder_name
        self.mockup_folder_path = self._validate_mockup_folder()
        self.photoshop_exe: str = self._validate_photoshop()
        
        
    def _validate_image_file(self, image_file_path: str) -> str:
        # error if the file does not exist.
        # use the pillow module. error if the file is not an image file
        return image_file_path    
    
    def _validate_mockup_folder(self) -> str:
        
        folders: dict = self.mockup_cfg.get("folders", {})
        
        if self.mockup_folder_name not in folders:
            # error f"Mockup Folder Name not found: {self.mockup_folder_name}"
            pass
            
        mockup_folder_path: str = folders.get(self.mockup_folder_name, "")
        
        # if mockup_folder_path does not exist on the OS then error
        
        return mockup_folder_path
    
    # validate self.photoshop_exe