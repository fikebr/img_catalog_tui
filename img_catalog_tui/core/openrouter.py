import base64
from typing import Any, Dict
import logging
import json
from pathlib import Path
import requests


from img_catalog_tui.config import Config
from img_catalog_tui.logger import setup_logging

logger = setup_logging()


class Openrouter():
    
    def __init__(self, config: Config):
        self.config = config
        
        # Verify API key is loaded
        if not self.config.openrouter_api_key:
            logger.warning("OpenRouter API key not found in environment variables")
        else:
            logger.info("OpenRouter API key loaded successfully")
            
        # Log other config values (without exposing sensitive data)
        logger.info(f"OpenRouter base URL: {self.config.openrouter_base_url}")
        logger.info(f"Vision model: {self.config.openrouter_model_vision}")
        logger.info(f"Text model: {self.config.openrouter_model_text}")

        # Example schema for InterviewResults / ProductPost
        self.interview_results_schema = {
            "name": "interview_results",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "etsy_post": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 15,
                                "maxItems": 20
                            }
                        },
                        "required": ["title", "description", "tags"],
                        "additionalProperties": False
                    },
                    "redbubble_post": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 15,
                                "maxItems": 20
                            }
                        },
                        "required": ["title", "description", "tags"],
                        "additionalProperties": False
                    }
                },
                "required": ["etsy_post", "redbubble_post"],
                "additionalProperties": False
            }
        }



    def chat_w_schema(self, prompt: str, schema: dict):
        """Send a structured-output query to OpenRouter using a given JSON schema."""

        api_key = self.config.openrouter_api_key
        ai_model = self.config.openrouter_model_text
        openrouter_url = f"{self.config.openrouter_base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        system_prompt = f"""
            ## ROLE & GOAL
            You are a data formatter. Given a plain-text description of an image, you must return a **single JSON object** that strictly conforms to the provided JSON Schema.

            ## OUTPUT RULES

            * Return **only** JSON (no prose, no Markdown fences)
            * Use **valid UTF-8**, double-quoted strings, and no trailing commas.
            * Populate every **required** field.
            * If a value is missing/unknowable, use `null`
            * Unless the schema allows it, **do not add extra keys** (`"additionalProperties": false` is enforced).
            * Strip leading/trailing whitespace.
            * Ensure arrays meet `minItems`/`maxItems`; fill with best, non-duplicate candidates.
            * Prefer concise, specific language; avoid repetition and filler.

            ## VALIDATION & QUALITY

            * Obey all schema constraints (types, enums, formats, regex patterns, min/max lengths).
            * Keep numbers realistic when inferring.
            * Use American English for spelling
            * Never fabricate facts that contradict the input

            ## JSON SCHEMA

            {schema}
        """
        
        user_prompt = f"""
            ## INPUT DESCRIPTION
            {prompt}

            ## INSTRUCTIONS

            * Extract and infer only what the schema requires.
            * Keep within all length limits.
            * Return exactly one JSON object and nothing else.
        """


        payload = {
            "model": ai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": schema
            }
        }

        try:
            resp = requests.post(openrouter_url, headers=headers, json=payload)
            resp.raise_for_status()
            raw = self._safe_json(resp)
            text = self._extract_content_text(raw)
            return {"text": text, "raw": raw}
        except requests.HTTPError as e:
            # Try to surface API error details
            detail = None
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:500]
            raise RuntimeError(f"HTTP error {resp.status_code}: {detail}") from e
        except requests.RequestException as e:
            raise RuntimeError(f"Network error: {e}") from e


    def chat_w_image(self, user_prompt: str, image_file_name: str, system_prompt: str = "", timeout: int = 60) -> Dict[str, str]:
        
        api_key = self.config.openrouter_api_key
        ai_model = self.config.openrouter_model_vision
        openrouter_url = f"{self.config.openrouter_base_url}/chat/completions"
        
        # Build the user content with a data URL image
        image_data_url = self._convert_image_file_to_base64_data_url(image_file_name)
        user_content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]

        payload = {
            "model": ai_model,
            "messages": [
                {"role": "system", "content": system_prompt},     # system as plain string
                {"role": "user", "content": user_content},        # user as typed parts
            ],
            # "max_tokens": 512,  # optionally control output size
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
                
        try:
            resp = requests.post(openrouter_url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            raw = self._safe_json(resp)
            text = self._extract_content_text(raw)
            return {"text": text, "raw": raw}
        except requests.HTTPError as e:
            # Try to surface API error details
            detail = None
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:500]
            raise RuntimeError(f"HTTP error {resp.status_code}: {detail}") from e
        except requests.RequestException as e:
            raise RuntimeError(f"Network error: {e}") from e


    def _safe_json(self, resp: requests.Response) -> Dict[str, Any]:
        try:
            return resp.json()
        except json.JSONDecodeError:
            # Fallback if a proxy returned HTML/text
            return {"non_json_body": resp.text}


    def _extract_content_text(self, payload: Dict[str, Any]) -> str:
        """
        Defensive extractor that works for OpenAI-style chat/completions and some variants.
        """
        # OpenAI / OpenRouter chat-completions
        if "choices" in payload and payload["choices"]:
            msg = payload["choices"][0].get("message", {})
            content = msg.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for p in content:
                    if p.get("type") in {"text", "output_text"}:
                        # Some providers use {'type': 'text', 'text': '...'}
                        parts.append(p.get("text") or "")
                return "\n".join(filter(None, parts))

        # Responses-like shape
        if "output_text" in payload and isinstance(payload["output_text"], str):
            return payload["output_text"]

        return ""


    def _convert_image_file_to_base64_data_url(self, image_path: str) -> str:
        """
        Convert a local image file (jpg/jpeg/png) to a base64 data URL.
        """
        if not image_path:
            raise ValueError("Image path cannot be empty")

        p = Path(image_path)
        if not p.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        if not p.is_file():
            raise ValueError(f"Path is not a file: {image_path}")

        valid_exts = {".jpg", ".jpeg", ".png"}
        ext = p.suffix.lower()
        if ext not in valid_exts:
            raise ValueError(f"Unsupported image format. Must be one of: {', '.join(sorted(valid_exts))}")

        try:
            data = p.read_bytes()
            if not data:
                raise ValueError("Image file is empty")

            b64 = base64.b64encode(data).decode("utf-8")
            mime = "image/png" if ext == ".png" else "image/jpeg"
            return f"data:{mime};base64,{b64}"
        except (OSError, IOError) as e:
            raise IOError(f"Error reading image file: {e}") from e
        
    def save_output(self, image_file: str, text: str | dict, file_tag: str, file_ext: str = "txt") -> bool:
        """Save text output to a file based on the image file path and tag."""
        try:
            # Get the filename to write to based on the image_file
            image_path = Path(image_file)
            output_filename = f"{image_path.stem}_{file_tag}.{file_ext}"
            output_path = image_path.parent / output_filename
            
            # Convert data to string format
            if isinstance(text, dict):
                # Pretty print JSON with indentation
                content = json.dumps(text, indent=2, ensure_ascii=False)
            else:
                content = str(text)
            
            # Write content to the file (overwrite if necessary)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully saved output to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving output file: {e}")
            return False
        



if __name__ == "__main__":

    # Load configuration
    config = Config("./config/config.toml")  # Adjust path as needed

    openrouter = Openrouter(config=config)
    
    
    image_file = r"C:\Users\bradf\Downloads\2025-09-24 - Working Whale\2025-09-24 - Working Whale_up2.jpg"
    system_prompt = ""
    user_prompt = "describe this image"

    results = openrouter.chat_w_image(user_prompt=user_prompt, image_file_name=image_file, system_prompt=system_prompt)
    openrouter.save_output(image_file=image_file, text=results["text"], file_tag="interview")
    openrouter.save_output(image_file=image_file, text=results["raw"], file_tag="interview_raw")

    results_json = openrouter.chat_w_schema(prompt=results["text"], schema=openrouter.interview_results_schema)
    openrouter.save_output(image_file=image_file, text=results_json["text"], file_tag="interview", file_ext="json")

    print(results)
    