import logging
import os
from pathlib import Path
from PIL import Image, ImageOps

from img_catalog_tui.logger import setup_logging


class ImageFile():
    
    def __init__(self, file_path: str):

        self.file_path: str = self._validate_file_path(file_path)
        self.height: int = 0
        self.width: int = 0
        self.aspect_ratio: str = ""
        self.measure_image()
        
        
    def _validate_file_path(self, file_path: str) -> str:
        """Validates that the file exists and is a valid image file."""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File does not exist: {file_path}")
            
            # Get absolute path
            abs_path = os.path.abspath(file_path)
            
            # Validate that it's an image file using Pillow
            try:
                with Image.open(abs_path) as img:
                    img.verify()  # Verify it's a valid image
                return abs_path
            except Exception as e:
                raise ValueError(f"File is not a valid image: {file_path}") from e
                
        except Exception as e:
            logging.error(f"Error validating file path {file_path}: {e}")
            raise

    def _gen_thumbnail_name(self) -> str:
        """Generates the full path for the thumbnail of this file."""
        try:
            path_obj = Path(self.file_path)
            folder = path_obj.parent
            basename = path_obj.stem
            extension = path_obj.suffix
            
            thumbnail_name = f"{basename}_thumb{extension}"
            thumbnail_path = folder / thumbnail_name
            
            return str(thumbnail_path)
        except Exception as e:
            logging.error(f"Error generating thumbnail name for {self.file_path}: {e}")
            raise

    def measure_image(self):
        """Measures the image dimensions and calculates aspect ratio."""
        try:
            with Image.open(self.file_path) as img:
                self.width, self.height = img.size
                
                # Calculate aspect ratio
                if self.height > 0:
                    # Find the greatest common divisor to simplify the ratio
                    from math import gcd
                    gcd_val = gcd(self.width, self.height)
                    simplified_width = self.width // gcd_val
                    simplified_height = self.height // gcd_val
                    self.aspect_ratio = f"{simplified_width}:{simplified_height}"
                else:
                    self.aspect_ratio = "0:0"
                    
        except Exception as e:
            logging.error(f"Error measuring image {self.file_path}: {e}")
            self.width = 0
            self.height = 0
            self.aspect_ratio = "0:0"
    
    @property
    def size(self) -> int:
        """Returns the file size in KB."""
        try:
            file_size_bytes = os.path.getsize(self.file_path)
            file_size_kb = file_size_bytes // 1024
            return file_size_kb
        except Exception as e:
            logging.error(f"Error getting file size for {self.file_path}: {e}")
            return 0
    
    @property
    def thumbnail(self) -> str:
        """Returns the thumbnail filename if it exists, otherwise returns empty string."""
        try:
            thumb_file_name = self._gen_thumbnail_name()
            if os.path.exists(thumb_file_name):
                return thumb_file_name
            else:
                return ""
        except Exception as e:
            logging.error(f"Error checking thumbnail for {self.file_path}: {e}")
            return ""
        
    @property
    def orientation(self) -> str:

        if self.height > self.width:
            return "vertical"
        
        if self.width > self.height:
            return "horizontal"
        
        return "square"
        
        
    
    def create_thumbnail(self, size: int = 500) -> str:
        """Creates a thumbnail of the image with the specified maximum size."""
        try:
            # Check if thumbnail already exists
            existing_thumbnail = self.thumbnail
            if existing_thumbnail:
                return existing_thumbnail
            
            # Generate thumbnail filename
            thumb_file_name = self._gen_thumbnail_name()
            
            # Create thumbnail using Pillow
            with Image.open(self.file_path) as img:
                # Calculate thumbnail size maintaining aspect ratio
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumb_file_name, optimize=True, quality=85)
                
            logging.info(f"Created thumbnail: {thumb_file_name}")
            return thumb_file_name
            
        except Exception as e:
            logging.error(f"Error creating thumbnail for {self.file_path}: {e}")
            return ""
        
    def create_watermark(self, watermark_file: str) -> str:
        """Creates a watermarked version of the image with the watermark tiled across the bottom third."""
        try:
            logging.info(f"Starting watermark creation for {self.file_path} with watermark {watermark_file}")
            
            main_path: str = self.file_path
            
            # Derive the output_path from the main_path: {folder}\{basename}_watermark{ext}
            path_obj = Path(main_path)
            folder = path_obj.parent
            basename = path_obj.stem
            extension = path_obj.suffix
            output_path = str(folder / f"{basename}_watermark{extension}")
            
            # Validate that the watermark_file exists
            if not os.path.exists(watermark_file):
                raise FileNotFoundError(f"Watermark file does not exist: {watermark_file}")
            
            # If output_path exists then return output_path
            if os.path.exists(output_path):
                logging.info(f"Watermarked image already exists: {output_path}")
                return output_path

            opacity: float = 0.60           # 0.0–1.0
            coverage_fraction: float = 1/6   # bottom third

            if not (0.0 <= opacity <= 1.0):
                raise ValueError("opacity must be between 0.0 and 1.0")

            # Open and orient the main image; ensure RGB (no alpha in final JPEG)
            base = ImageOps.exif_transpose(Image.open(main_path)).convert("RGB")
            width, height = base.size
            logging.info(f"Main image dimensions: {width}x{height}")

            # Define the bottom strip to cover
            strip_top = int(height * (1 - coverage_fraction))
            strip_h = height - strip_top
            if strip_h <= 0:
                raise ValueError("coverage_fraction yields zero-height strip")

            # Open watermark as RGBA (to preserve its transparent background)
            wm = Image.open(watermark_file).convert("RGBA")
            wm_w, wm_h = wm.size
            if wm_w == 0 or wm_h == 0:
                raise ValueError("watermark image has invalid dimensions")
            logging.info(f"Watermark dimensions: {wm_w}x{wm_h}")

            # Create an RGBA overlay sized to the bottom strip
            overlay = Image.new("RGBA", (width, strip_h), (0, 0, 0, 0))

            # Tile the watermark across the overlay
            y = 0
            while y < strip_h:
                x = 0
                while x < width:
                    overlay.alpha_composite(wm, dest=(x, y))
                    x += wm_w
                y += wm_h

            # Apply global opacity by scaling the alpha channel
            alpha = overlay.getchannel("A").point(lambda a: int(a * opacity))
            overlay.putalpha(alpha)

            # Paste overlay onto the base image at the bottom strip
            base.paste(overlay, (0, strip_top), overlay)

            # Save as JPEG
            base.save(output_path, format="JPEG", quality=95, subsampling=2)
            logging.info(f"Successfully created watermarked image: {output_path}")
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error creating watermark for {self.file_path}: {e}")
            raise
        
        




if __name__ == "__main__":

    setup_logging()

    file = r"E:\fooocus\images\new\2025-10-07\2025-10-07_00-12-37_2156\2025-10-07_00-12-37_2156_up4.jpg"
    watermark_file = r"C:\Users\bradf\Downloads\Jackrabbit Watermark.png"
    
    imagefile_obj = ImageFile(file_path=file)
    
    print(f"height: {imagefile_obj.height}")
    print(f"width: {imagefile_obj.width}")
    print(f"aspect_ratio: {imagefile_obj.aspect_ratio}")
    print(f"size: {imagefile_obj.size}")
    print(f"thumbnail: {imagefile_obj.thumbnail}")
    
    print(imagefile_obj.create_watermark(watermark_file=watermark_file))