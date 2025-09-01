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
        # self.openai_client = self._get_openai_client()
        # self.client = self._get_client()
        # self.prompt = self._get_prompt(interview_template)
        # self.image_file = self._validate_image_file(image_file)
        # self.interview_response = None
        # self.interview_parsed = None

    def chat_w_image(self, user_prompt: str, image_file_name: str, system_prompt: str = "", timeout: int = 60) -> Dict[str, str]:
        
        api_key = self.config.openrouter_api_key
        ai_model = self.config.openrouter_model
        
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
            # Optional but recommended by OpenRouter:
            # "HTTP-Referer": "https://your-app.example",
            # "X-Title": "Your App Name",
        }
                
        try:
            resp = requests.post(f"{self.config.openrouter_base_url}/chat/completions", headers=headers, json=payload, timeout=timeout)
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
