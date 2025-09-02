import os
import logging
import json
from typing import Optional, Any

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, model_validator

from img_catalog_tui.config import Config
# from img_catalog_tui.logger import setup_logging
from img_catalog_tui.core.openrouter import Openrouter


# ---------------------------
# Pydantic models
# ---------------------------

class ProductPost(BaseModel):
    """Data needed for a marketplace post (Etsy/Redbubble)."""
    title: str = Field(
        description="SEO-friendly title for the product post.",
        example=("Transform your space with this charming vintage-style sloth gentleman "
                 "portrait on premium canvas! This delightfully quirky art print features "
                 "a dapper sloth dressed in Victorian-era formal attire, complete with "
                 "waistcoat and cravat.")
    )
    description: str = Field(
        description="SEO-friendly description tuned for the target marketplace."
    )
    tags: list[str] = Field(
        description="15-20 SEO-friendly tags (mix of short/long tail)."
    )


class InterviewResults(BaseModel):
    """Structured results from parsing the interview free text."""
    etsy_post: ProductPost = Field(description="Post tuned for Etsy.")
    redbubble_post: ProductPost = Field(description="Post tuned for Redbubble.")

    @model_validator(mode='before')
    @classmethod
    def parse_string_fields(cls, data: Any) -> Any:
        """Convert JSON strings to objects if needed."""
        if isinstance(data, dict):
            # First, log what we received for debugging
            logging.debug("InterviewResults received data: %s", data)
            
            for field_name in ['etsy_post', 'redbubble_post']:
                if field_name in data:
                    field_value = data[field_name]
                    logging.debug(f"Processing {field_name}: type={type(field_value)}, value={repr(field_value)}")
                    
                    # Handle None or empty values
                    if field_value is None or field_value == "":
                        logging.warning(f"{field_name} is None or empty, skipping JSON parsing")
                        continue
                        
                    # Handle string values that might be JSON
                    if isinstance(field_value, str):
                        # Skip if it's just whitespace
                        if not field_value.strip():
                            logging.warning(f"{field_name} is whitespace only, skipping JSON parsing")
                            continue
                            
                        try:
                            # Try to parse as JSON
                            parsed = json.loads(field_value)
                            logging.debug(f"Successfully parsed {field_name} JSON: {parsed}")
                            
                            # Convert keys to lowercase if they're uppercase
                            if isinstance(parsed, dict):
                                normalized = {}
                                for k, v in parsed.items():
                                    key = k.lower().replace(' ', '_') if isinstance(k, str) else k
                                    if key == 'title':
                                        normalized['title'] = v
                                    elif key == 'description':
                                        normalized['description'] = v
                                    elif key == 'tags':
                                        # Handle tags as string or list
                                        if isinstance(v, str):
                                            # Split on common delimiters
                                            tags = [tag.strip() for tag in v.replace(',', '\n').replace(';', '\n').split('\n') if tag.strip()]
                                            normalized['tags'] = tags
                                        else:
                                            normalized['tags'] = v
                                    else:
                                        normalized[key] = v
                                data[field_name] = normalized
                            else:
                                data[field_name] = parsed
                        except (json.JSONDecodeError, TypeError) as e:
                            logging.warning(f"Failed to parse {field_name} as JSON: {e}. Raw value: {repr(field_value)}")
                            # Keep the original string value, let Pydantic handle the error
                    else:
                        # If it's already a dict, just log it
                        logging.debug(f"{field_name} is already a dict: {field_value}")
        return data


class InterviewRaw(BaseModel):
    """Raw interview block (optional; not used directly below)."""
    raw_text: str = Field(description="The raw text of the interview.")


# ---------------------------
# Interview logic
# ---------------------------

class Interview:
    def __init__(self, config: Config, interview_template: str = "default", image_file: Optional[str] = None):
        self.config = config

        # Logging the core inputs early helps a lot when debugging env issues
        logging.debug("Initializing Interview with template=%r, image_file=%r", interview_template, image_file)

        self.openai_client = self._get_openai_client()
        self.client = self._get_instructor_client()

        self.prompt = self._get_prompt(interview_template)

        # Only validate if provided; your code path might support text-only interviews later
        self.image_file = self._validate_image_file(image_file)

        self.interview_response: Optional[str] = None # the full text of the interview results
        self.interview_raw: Optional[dict] = None # the raw json of the interview request
        self.interview_parsed: Optional[InterviewResults] = None # the parsed results from the instructor module

        self.openrouter = Openrouter(self.config)

    def _get_instructor_client(self):
        """Return an instructor-patched OpenAI client."""
        logging.info("Patching OpenAI client with instructor")
        # If you need specific mode (e.g., JSON), this also works:
        # return instructor.patch(self.openai_client, mode=instructor.Mode.JSON)
        return instructor.from_openai(self.openai_client)

    def _get_openai_client(self) -> OpenAI:
        """Initialize the OpenAI client pointing at OpenRouter."""
        # Validate required config values
        if not getattr(self.config, "openrouter_api_key", None):
            logging.error("OPENROUTER_API_KEY environment variable is not set")
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")
        if not getattr(self.config, "openrouter_base_url", None):
            logging.error("OPENROUTER_BASE_URL environment variable is not set")
            raise ValueError("OPENROUTER_BASE_URL environment variable is not set")
        if not getattr(self.config, "openrouter_model", None):
            logging.error("OPENROUTER_MODEL environment variable is not set")
            raise ValueError("OPENROUTER_MODEL environment variable is not set")

        logging.info("Creating OpenAI client for model: %s", self.config.openrouter_model)

        # If your OpenRouter account requires headers like HTTP-Referer/X-Title,
        # you can add them via default_headers=... here.
        client = OpenAI(
            base_url=self.config.openrouter_base_url,
            api_key=self.config.openrouter_api_key,
        )
        return client

    def _validate_image_file(self, image_file: Optional[str]) -> Optional[str]:
        """Validate the image file if provided; otherwise return None."""
        if image_file is None:
            logging.info("No image_file provided; proceeding without image.")
            return None
        if not os.path.exists(image_file):
            logging.error("Image file not found: %s", image_file)
            raise FileNotFoundError(f"Image file not found: {image_file}")
        return image_file

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


    def interview_image(self):
        """Send the image + prompt to your OpenRouter wrapper and capture raw + text."""
        if not self.image_file:
            raise ValueError("interview_image() requires image_file to be set")

        try:
            logging.info("Interviewing image: %s", self.image_file)

            results = self.openrouter.chat_w_image(
                user_prompt=self.prompt,
                image_file_name=self.image_file
            )

            # Be defensive about payload shape
            if isinstance(results, dict):
                self.interview_response = results.get("text") or results.get("message") or ""
                self.interview_raw = results.get("raw", results)
            else:
                # If wrapper returns a string, treat it as the text
                self.interview_response = str(results)
                self.interview_raw = {"raw": results}

            if not self.interview_response:
                raise RuntimeError("OpenRouter chat returned no text response")

            logging.debug("Interview response (truncated): %s", self.interview_response[:500])

        except Exception as e:
            logging.exception("Error during parse_interview: %s", e)
            raise RuntimeError(f"parse_interview failed: {e}") from e

    def parse_interview(self):
        """Use Instructor to coerce the free text into the InterviewResults schema."""
        try:
            if not self.interview_response:
                raise ValueError("parse_interview() called before interview_response was set")

            logging.info("Parsing interview into structured schema")
            logging.debug("Raw interview response to parse: %s", self.interview_response)
            prompt = f"Extract the information from this interview text and structure it for marketplace posts:\n\n{self.interview_response}"

            # Text-only message must be a string, not a list
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]

            response: InterviewResults = self.client.chat.completions.create(
                messages=messages,
                # OpenRouter hint below is okay to keep; won’t break OpenAI SDK.
                extra_body={"provider": {"require_parameters": True}},
                response_model=InterviewResults,
                model=self.config.openrouter_model,
            )

            # Instructor returns a parsed instance (not the raw OpenAI object)
            self.interview_parsed = response
            logging.debug("Structured parse complete: %s", self.interview_parsed.model_dump())

        except Exception as e:
            logging.exception("Error during parse_interview: %s", e)
            # Log the raw response for debugging
            logging.error("Raw interview response that failed to parse: %s", self.interview_response[:500] + "..." if len(self.interview_response) > 500 else self.interview_response)
            raise RuntimeError(f"parse_interview failed: {e}") from e

    def save_raw_interview(self):
        """Save the raw interview data to a text file based on the image filename."""
        if not self.image_file:
            logging.error("Cannot save raw interview: image_file is not set")
            raise ValueError("Cannot save raw interview: image_file is not set")
        
        if not self.interview_raw:
            logging.error("Cannot save raw interview: interview_raw is not set")
            raise ValueError("Cannot save raw interview: interview_raw is not set")
        
        try:
            # Get the directory and basename of the image file
            image_dir = os.path.dirname(self.image_file)
            image_basename = os.path.splitext(os.path.basename(self.image_file))[0]
            
            # Create the output filename
            interview_raw_textfile = os.path.join(image_dir, f"{image_basename}_interview_raw.txt")
            
            # Convert interview_raw to string format for saving
            if isinstance(self.interview_raw, dict):
                raw_content = json.dumps(self.interview_raw, indent=2)
            else:
                raw_content = str(self.interview_raw)
            
            # Write the raw interview data to file
            with open(interview_raw_textfile, 'w', encoding='utf-8') as f:
                f.write(raw_content)
            
            logging.info("Raw interview saved to: %s", interview_raw_textfile)
            return interview_raw_textfile
            
        except Exception as e:
            logging.exception("Error saving raw interview: %s", e)
            raise RuntimeError(f"Failed to save raw interview: {e}") from e

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

    def save_json_interview(self):
        """Save the parsed interview data to a JSON file based on the image filename."""
        if not self.image_file:
            logging.error("Cannot save JSON interview: image_file is not set")
            raise ValueError("Cannot save JSON interview: image_file is not set")
        
        if not self.interview_parsed:
            logging.error("Cannot save JSON interview: interview_parsed is not set")
            raise ValueError("Cannot save JSON interview: interview_parsed is not set")
        
        try:
            # Get the directory and basename of the image file
            image_dir = os.path.dirname(self.image_file)
            image_basename = os.path.splitext(os.path.basename(self.image_file))[0]
            
            # Create the output filename
            interview_jsonfile = os.path.join(image_dir, f"{image_basename}_interview.json")
            
            # Convert interview_parsed to JSON string
            json_content = self.interview_parsed.model_dump_json(indent=2)
            
            # Write the JSON interview data to file
            with open(interview_jsonfile, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            logging.info("JSON interview saved to: %s", interview_jsonfile)
            return interview_jsonfile
            
        except Exception as e:
            logging.exception("Error saving JSON interview: %s", e)
            raise RuntimeError(f"Failed to save JSON interview: {e}") from e
        
    def save_all_files(self):
        
        logging.info("Interview Save All: Started")

        if not self.interview_response:
            logging.error("Interview Response not created yet.")
            return
        if not self.interview_raw:
            logging.error("Interview Raw not created yet.")
            return
        if not self.interview_parsed:
            logging.error("Interview Parsed not created yet.")
            return
        
        self.save_text_interview()
        self.save_raw_interview()
        self.save_json_interview()
        
        logging.info("Interview Save All: Complete")

        



# ---------------------------
# Example usage
# ---------------------------

if __name__ == "__main__":

    # Load configuration
    config = Config("./config/config.toml")  # Adjust path as needed
    if not config.load():
        print("Failed to load configuration")
        raise SystemExit(1)

    # Example image
    # image_file = r"E:\fooocus\images\new\2025-08-03_tmp\2025-08-03_00-05-54_8875\2025-08-03_00-05-54_8875_orig.png"
    image_file = r"E:\fooocus\images\new\2025-08-05\2025-08-05_05-40-52_2470\2025-08-05_05-40-52_2470_orig.png"

    interview = Interview(config=config, image_file=image_file)
    try:
        interview.interview_image()
        print("Interview response (truncated):", (interview.interview_response or "")[:400], "...\n")
        # interview.save_raw_interview()
        # interview.save_text_interview()

        interview.parse_interview()
        # Pretty-print the structured result
        print("Interview results (JSON):")
        print(interview.interview_parsed.model_dump_json(indent=2))
        # interview.save_json_interview()
        interview.save_all_files()

    except Exception as e:
        print(f"Error testing interview: {e}")
