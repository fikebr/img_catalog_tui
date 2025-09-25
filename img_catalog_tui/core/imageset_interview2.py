import os
import logging
import base64
from dataclasses import dataclass
from PIL import Image as PILImage
from io import BytesIO

import outlines
from outlines.inputs import Chat, Image as OLImage
from openai import OpenAI

from img_catalog_tui.config import Config
from img_catalog_tui.core.openrouter import Openrouter

# -------------------- Dataclasses --------------------
@dataclass
class ProductPost:
    title: str
    description: str
    tags: list[str]  # 15–20 SEO-friendly tags

@dataclass
class InterviewResults:
    etsy_post: ProductPost
    redbubble_post: ProductPost



class Interview:
    def __init__(self, config: Config, interview_template: str = "default", image_file: str = None):
        self.config = config

        self.interview_template = interview_template
        self.image_file = self._validate_image_file(image_file)

        # Logging the core inputs early helps a lot when debugging env issues
        logging.debug("Initializing Interview with template=%r, image_file=%r", interview_template, image_file)

        self.prompt = self._get_prompt(interview_template)

        self.model_vision = self._build_model(provider = "openrouter", model_name=self.config.openrouter_model_vision)
        self.model_text = self._build_model(provider="openrouter", model_name=self.config.openrouter_model_text)

        self.pil_image = self._load_local_image(self.image_file) if self.image_file else None

        self.interview_response: str = None # the full text of the interview results
        self.interview_raw: dict = None # the raw json of the interview request
        self.interview_parsed: InterviewResults = None # the parsed results from the instructor module

        
    def interview_image(self) -> str:
        if self.pil_image is None:
            raise ValueError("No image loaded. Cannot perform image interview.")
            
        model = self.model_vision
        prompt_text = self.prompt
        image = self.pil_image
        
        chat = Chat()
        chat.add_system_message("You are a careful visual describer. Output a detailed description.")
        chat.add_user_message([prompt_text, OLImage(image)])
        raw_caption = model(chat, max_new_tokens=800)   # free text

        self.interview_response = raw_caption.strip()
        return raw_caption.strip()
    
    # -------------------- Pass 2: raw caption → structured --------------------
    def _structured_attempt(self) -> InterviewResults:
        model = self.model_text
        raw_caption = self.interview_response
        
        chat = Chat()
        chat.add_system_message(
            "You are a meticulous product copywriter. "
            "Always return ONLY valid JSON for the requested schema. No markdown fences, no commentary."
        )
        chat.add_user_message(
            "Convert the following interview text into an InterviewResults object.\n"
            "Rules:\n"
            "1) Output JSON only.\n"
            "2) For each post, produce title (string), description (string), and tags (array of 15-20 strings).\n"
            "3) Tags should be SEO-friendly and relevant.\n\n"
            f"Interview text:\n{raw_caption}"
        )
        return model(chat, InterviewResults, max_new_tokens=1200)  # schema enforced

    def parse_interview(self, max_attempts: int = 3) -> InterviewResults:
        model = self.model_text
        raw_caption = self.interview_response
        
        last_error_msg = ""

        for attempt in range(1, max_attempts + 1):
            try:
                return self._structured_attempt()
            except Exception as e:
                last_error_msg = f"Attempt {attempt}: {e}"
                # Repair prompt after parse error
                chat = Chat()
                chat.add_system_message(
                    "You will fix the output to match the InterviewResults schema. Return ONLY valid structured data; no explanations."
                )
                chat.add_user_message(
                    "The previous output was not valid. "
                    "Re-create a valid InterviewResults object from the same interview text.\n\n"
                    f"Interview text:\n{raw_caption}"
                )
                try:
                    return model(chat, InterviewResults, max_new_tokens=1200)
                except Exception as e2:
                    last_error_msg = f"Attempt {attempt} repair failed: {e2}"
                    continue

        raise RuntimeError(
            f"Failed to produce valid InterviewResults after {max_attempts} attempts. Last error: {last_error_msg}"
        )

        
        
        
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
        
    def _load_local_image(self, path: str) -> PILImage.Image:
        """Preserve transparency: always return RGBA."""
        img = PILImage.open(path)
        return img.convert("RGBA")


    def _build_model(self, provider: str, model_name: str):
        prov = provider.lower()
        if prov == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("Set OPENROUTER_API_KEY for OpenRouter.")
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            return outlines.from_openai(client, model_name)
        if prov == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("Set OPENAI_API_KEY for OpenAI.")
            client = OpenAI(api_key=api_key)
            return outlines.from_openai(client, model_name)
        raise ValueError("provider must be 'openai' or 'openrouter'")


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
    
    def save_text_interview(self):
        """Save the interview response text to a text file based on the image filename."""
        if not self.image_file:
            logging.error("Cannot save text interview: image_file is not set")
            raise ValueError("Cannot save text interview: image_file is not set")
        
        if not self.interview_response:
            logging.error("Cannot save text interview: interview_response is not set")
            raise ValueError("Cannot save text interview: interview_response is not set")
        
        try:
            # Get the directory and basename of the image file
            image_dir = os.path.dirname(self.image_file)
            image_basename = os.path.splitext(os.path.basename(self.image_file))[0]
            
            # Create the output filename
            interview_textfile = os.path.join(image_dir, f"{image_basename}_interview.txt")
            
            # Write the interview response text to file
            with open(interview_textfile, 'w', encoding='utf-8') as f:
                f.write(self.interview_response)
            
            logging.info("Text interview saved to: %s", interview_textfile)
            return interview_textfile
            
        except Exception as e:
            logging.exception("Error saving text interview: %s", e)
            raise RuntimeError(f"Failed to save text interview: {e}") from e



# ---------------------------
# Example usage
# ---------------------------

if __name__ == "__main__":

    # Load configuration
    config = Config("./config/config.toml")  # Adjust path as needed
    # if not config.load():
    #     print("Failed to load configuration")
    #     raise SystemExit(1)

    # Example image
    # image_file = r"E:\fooocus\images\new\2025-08-03_tmp\2025-08-03_00-05-54_8875\2025-08-03_00-05-54_8875_orig.png"
    image_file = r"C:\Users\bradf\Downloads\2025-09-24 - Working Whale\2025-09-24 - Working Whale_up2.jpg"
    # image_file = r"C:\Users\bradf\Downloads\2025-09-15 - Never Trust the Living Moth\2025-09-15 - Never Trust the Living Moth_orig.jpg"

    interview = Interview(config=config, image_file=image_file)
    try:
        interview.interview_image()
        print("Interview response (truncated):", (interview.interview_response or "")[:400], "...\n")
        # interview.save_raw_interview()
        interview.save_text_interview()

        #interview.parse_interview()
        # Pretty-print the structured result
        #print("Interview results (JSON):")
        #print(interview.interview_parsed.model_dump_json(indent=2))
        #interview.save_json_interview()
        # interview.save_all_files()

    except Exception as e:
        print(f"Error testing interview: {e}")
