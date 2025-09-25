import os
import logging
from PIL import Image as PILImage


from img_catalog_tui.config import Config
from img_catalog_tui.core.openrouter import Openrouter


class Interview:
    def __init__(self, config: Config, interview_template: str = "default", image_file: str = None):
        self.config = config

        self.interview_template = interview_template
        self.image_file = self._validate_image_file(image_file)

        # Logging the core inputs early helps a lot when debugging env issues
        logging.debug("Initializing Interview with template=%r, image_file=%r", interview_template, image_file)

        self.prompt = self._get_prompt(interview_template)

        self.interview_response: str = None # the full text of the interview results
        self.interview_raw: dict = None # the raw json of the interview request
        self.interview_parsed: dict = None # the parsed results from the instructor module

        
    def interview_image(self) -> str:
        
        user_prompt = self.prompt
        system_prompt = ""
        image_file = self.image_file
        
        openrouter = Openrouter(config=self.config)
        
        results = openrouter.chat_w_image(user_prompt=user_prompt, image_file_name=image_file, system_prompt=system_prompt)
       
        openrouter.save_output(image_file=image_file, text=results["text"], file_tag="interview")
        openrouter.save_output(image_file=image_file, text=results["raw"], file_tag="interview_raw")
        
        self.interview_response = results["text"]
        self.interview_raw = results["raw"]

        results_json = openrouter.chat_w_schema(prompt=results["text"], schema=openrouter.interview_results_schema)
        openrouter.save_output(image_file=image_file, text=results_json["text"], file_tag="interview", file_ext="json")
        
        self.interview_parsed = results_json["text"]

        # print(results)


        
        
        
    def _validate_image_file(self, image_file_path: str) -> str:
        """Validate that the image file exists and is a valid image file."""
        if image_file_path is None:
            return None
            
        if not os.path.exists(image_file_path):
            logging.error("Image file does not exist: %s", image_file_path)
            raise FileNotFoundError(f"Image file does not exist: {image_file_path}")
        
        if not os.path.isfile(image_file_path):
            logging.error("Path is not a file: %s", image_file_path)
            raise ValueError(f"Path is not a file: {image_file_path}")
        
        try:
            # Try to open the image to verify it's a valid image file
            with PILImage.open(image_file_path) as img:
                img.verify()  # Verify the image is valid
            logging.debug("Successfully validated image file: %s", image_file_path)
        except Exception as e:
            logging.error("Invalid image file: %s - %s", image_file_path, str(e))
            raise ValueError(f"Invalid image file: {image_file_path} - {str(e)}")
        
        return image_file_path
        

    def _get_prompt(self, prompt_template: str) -> str:
        """Load the interview prompt template from disk."""
        # get the template directory from the config (robust to missing keys)
        paths = (self.config.get("paths") or {})
        template_dir = paths.get("templates_dir", "config/templates")

        template_file = os.path.join(template_dir, f"interview_{prompt_template}.tmpl")
        
        if os.path.exists(template_file):
            with open(template_file, "r", encoding="utf-8") as fh:
                prompt = fh.read()
                logging.debug("Loaded prompt template from %s\n\n%s\n", template_file, prompt)
                return prompt

        logging.error("Prompt template file not found: %s", template_file)
        raise FileNotFoundError(f"Prompt template file not found: {prompt_template}")
    



# ---------------------------
# Example usage
# ---------------------------

if __name__ == "__main__":

    # Load configuration
    config = Config("./config/config.toml")  # Adjust path as needed

    # Example image
    # image_file = r"E:\fooocus\images\new\2025-08-03_tmp\2025-08-03_00-05-54_8875\2025-08-03_00-05-54_8875_orig.png"
    image_file = r"C:\Users\bradf\Downloads\2025-09-16 - Hall of Eyes\2025-09-16 - Hall of Eyes_orig.png"
    # image_file = r"C:\Users\bradf\Downloads\2025-09-15 - Never Trust the Living Moth\2025-09-15 - Never Trust the Living Moth_orig.jpg"

    interview = Interview(config=config, image_file=image_file)
    try:
        interview.interview_image()
        print("Interview response (truncated):", (interview.interview_response or "")[:400], "...\n")

    except Exception as e:
        print(f"Error testing interview: {e}")
