#!/usr/bin/env python3
# Python 3.12+ (no typing module; uses only built-in type hints)

import argparse
import json
import os
from dataclasses import dataclass, fields, is_dataclass

import outlines
from outlines.inputs import Chat, Image as OLImage
from PIL import Image as PILImage
from openai import OpenAI


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


# -------------------- Utils --------------------
def dict_to_dataclass(cls, data: dict):
    if not is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass")

    kwargs = {}
    fdefs = {f.name: f for f in fields(cls)}
    for name, fdef in fdefs.items():
        if name not in data:
            raise KeyError(f"Missing field '{name}' for {cls.__name__}")
        val = data[name]
        ftype = fdef.type

        # Nested dataclass
        if hasattr(ftype, "__dataclass_fields__"):
            kwargs[name] = dict_to_dataclass(ftype, val)
        # List[T] where T may be dataclass or primitive
        elif getattr(ftype, "__origin__", None) is list or isinstance(val, list):
            # Try to detect inner type; if not available, just pass through
            inner = getattr(ftype, "__args__", [None])[0] if hasattr(ftype, "__args__") else None
            if inner is not None and hasattr(inner, "__dataclass_fields__"):
                kwargs[name] = [dict_to_dataclass(inner, x) for x in val]
            else:
                kwargs[name] = list(val)
        else:
            kwargs[name] = val
    return cls(**kwargs)

def load_prompt_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def load_local_image(path: str) -> PILImage.Image:
    """Preserve transparency: always return RGBA."""
    img = PILImage.open(path)
    return img.convert("RGBA")

def build_model(provider: str, model_name: str):
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


# -------------------- Pass 1: image → raw caption --------------------
def run_raw_caption(model, prompt_text: str, image: PILImage.Image) -> str:
    chat = Chat()
    chat.add_system_message("You are a careful visual describer. Output a detailed description.")
    chat.add_user_message([prompt_text, OLImage(image)])
    raw_caption = model(chat, max_new_tokens=800)   # free text
    return raw_caption.strip()


# -------------------- Pass 2: raw caption → structured --------------------
def _structured_attempt(model, raw_caption: str) -> InterviewResults:
    chat = Chat()
    chat.add_system_message(
        "You are a meticulous product copywriter. "
        "Always return ONLY valid JSON for the requested schema. No markdown fences, no commentary."
    )
    chat.add_user_message(
        "Convert the following interview text into an InterviewResults object.\n"
        "Rules:\n"
        "1) Output JSON only.\n"
        "2) For each post, produce title (string), description (string), and tags (array of 15–20 strings).\n"
        "3) Tags should be SEO-friendly and relevant.\n\n"
        f"Interview text:\n{raw_caption}"
    )
    return model(chat, InterviewResults, max_new_tokens=1200)  # schema enforced

def run_structured_pass_with_retry(model, raw_caption: str, max_attempts: int = 3) -> InterviewResults:
    last_error_msg = ""

    for attempt in range(1, max_attempts + 1):
        try:
            return _structured_attempt(model, raw_caption)
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


# -------------------- CLI --------------------
def parse_args():
    p = argparse.ArgumentParser(description="Vision → caption → structured InterviewResults with Outlines")
    p.add_argument("--provider-vision", choices=["openai", "openrouter"], required=True)
    p.add_argument("--model-vision", required=True, help="Vision model (e.g., openai: gpt-4o-mini; openrouter: qwen/qwen-2.5-vl-7b-instruct)")
    p.add_argument("--provider-text", choices=["openai", "openrouter"], required=True)
    p.add_argument("--model-text", required=True, help="Cheap text model for pass 2 (no image)")
    p.add_argument("--image", required=True, help="Path to local image")
    p.add_argument("--prompt-file", required=True, help="Path to text prompt file")
    p.add_argument("--dump-json", help="Optional path to save final JSON")
    return p.parse_args()

def main():
    args = parse_args()

    model_vision = build_model(args.provider_vision, args.model_vision)
    model_text   = build_model(args.provider_text, args.model_text)

    prompt_text = load_prompt_text(args.prompt_file)
    pil_image   = load_local_image(args.image)

    # Pass 1: image → caption
    raw_caption = run_raw_caption(model_vision, prompt_text, pil_image)
    print("\n--- RAW CAPTION ---\n")
    print(raw_caption)

    # Pass 2: caption → structured dataclasses (with auto-retry/repair)
    results = run_structured_pass_with_retry(model_text, raw_caption, max_attempts=3)

    # Print final JSON (friendly)
    out = {
        "etsy_post": {
            "title": results.etsy_post.title,
            "description": results.etsy_post.description,
            "tags": results.etsy_post.tags,
        },
        "redbubble_post": {
            "title": results.redbubble_post.title,
            "description": results.redbubble_post.description,
            "tags": results.redbubble_post.tags,
        },
    }
    print("\n--- INTERVIEW RESULTS ---\n")
    print(json.dumps(out, ensure_ascii=False, indent=2))

    if args.dump_json:
        with open(args.dump_json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
