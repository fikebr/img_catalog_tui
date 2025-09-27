from PIL import Image, ExifTags
import os
import json

class ImagesetMetaData:
    
    def __init__(self, imagefile: str):
        self.imagefile = self._validate_filename(imagefile)
        self.source = ""
        self.exif = self.get_exif_data()
        self.data = {}
        
        self.set_data()
        
    
    def get_exif_data(self):

        exif_data = {}
        
        try:
            with Image.open(self.imagefile) as img:
                # Get standard EXIF data
                if hasattr(img, '_getexif') and img._getexif():
                    for tag, value in img._getexif().items():
                        if tag in ExifTags.TAGS:
                            exif_data[ExifTags.TAGS[tag]] = value
                
                # Get PNG text data (used by Midjourney and Fooocus)
                if img.format == 'PNG' and hasattr(img, 'text'):
                    for key, value in img.text.items():
                        exif_data[f"PNG:{key}"] = value
            
            return(exif_data)
            
        except Exception as e:
            raise SystemError(f"Error extracting EXIF data from {self.imagefile}: {e}")

    def is_fooocus(self) -> bool:

        scheme_field = "PNG:fooocus_scheme"

        if scheme_field in self.exif:
            if self.exif[scheme_field] == "fooocus":
                self.source = "fooocus"
                return True
                
        return False


    def is_midjourney(self) -> bool:
        
        author_field = "PNG:Author"
        author_value = "aardvark_fike"

        if author_field in self.exif:
            if self.exif[author_field] == author_value:
                self.source = "midjourney"
                return True
            
        return False

    def set_fooocus_data(self) -> dict:
        
        parameters_field: str = "PNG:parameters"
        
        try:
            # Parse JSON data from parameters field
            parameters = self.exif[parameters_field]
            
            # Try to parse as JSON
            parsed_data = json.loads(parameters)
            self.data = parsed_data

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Error parsing Fooocus JSON parameters: {e}") from e 


    def set_midjourney_data(self):
        
        description_field = "PNG:Description"

        def parse_midjourney_description(description: str) -> tuple:
            job_id = ""
            prompt = description
            
            # Extract job ID if present
            if "Job ID:" in description:
                parts = description.split("Job ID:")
                prompt = parts[0].strip()
                job_id = parts[1].strip()
            
            return prompt, job_id



        if description_field in self.exif:
        
            try:
                description = self.exif[description_field]
                
                prompt, job_id = parse_midjourney_description(description)
                
                result = {
                    "description": description,
                    "prompt": prompt,
                    "jobid": job_id
                }
                
                self.data = result

            except Exception as e:
                raise RuntimeError(f"Error parsing Midjourney metadata: {e}") from e

    
    def _validate_filename(self, imagefile: str | None) -> str:
        if imagefile is None:
            raise ValueError("Image file path cannot be None")
        
        if not isinstance(imagefile, (str, bytes, os.PathLike)):
            raise TypeError(f"Image file path must be string, bytes, or PathLike, not {type(imagefile)}")
            
        if not os.path.exists(imagefile):
            raise FileExistsError(f"Image file not found: {imagefile}")
        
        return(imagefile)
        
    
    def set_data(self):
        
        if self.is_fooocus():
            self.set_fooocus_data()

        elif self.is_midjourney():
            self.set_midjourney_data()

        else:
            self.data = self.exif
        
            
if __name__ == "__main__":
    
    image_file = r"E:\fooocus\images\new\2025-08-03_tmp\2025-08-03_00-00-23_7134\2025-08-03_00-00-23_7134_orig.png"
    # image_file = r"E:\fooocus\images\new\2025-08-03_tmp\aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_0\aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_0_orig.png"
    
    img_exif = ImagesetMetaData(imagefile = image_file)
    
    print(img_exif.data)
    print(f"is_fooocus: {img_exif.is_fooocus()}")
    print(f"is_midjourney: {img_exif.is_midjourney()}")
    print(img_exif.data.get('prompt', "not found"))
    print(img_exif.source)
    
    
    
