import logging
import os
from datetime import datetime

import jinja2

from img_catalog_tui.config import Config
from img_catalog_tui.core.folders import Folders
from img_catalog_tui.core.imageset import Imageset


def _resolve_folder_path(config: Config, folder_input: str) -> str:
    """
    Resolve a folder identifier into a filesystem path.

    Accepts either:
    - a DB folder registry name (folders.name), or
    - a full filesystem path.
    """
    value = (folder_input or "").strip()
    if not value:
        raise ValueError("folder_name is required")

    folders = Folders(config=config)
    if value in folders.folders:
        return folders.folders[value]

    return value


def _template_dir(config: Config) -> str:
    # `config.config_dir` is the directory containing config.toml
    return os.path.join(config.config_dir, "templates")


def _read_text_file(path: str) -> str:
    if not path:
        return ""
    try:
        if not os.path.exists(path) or not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.warning("Failed reading text file %s: %s", path, e)
        return ""


def generate_html_report(folder_name: str, imageset_name: str, config: Config) -> bool:
    """
    Create a static HTML report for one imageset.

    Writes: {imageset_folder}/{imageset_name}.html
    """
    try:
        folder_path = _resolve_folder_path(config, folder_name)
        imageset_folder = os.path.join(folder_path, imageset_name)

        if not os.path.isdir(imageset_folder):
            logging.error("Imageset folder does not exist: %s", imageset_folder)
            return False

        # Ensure DB file records are current enough for cover/orig selection.
        imageset = Imageset(config=config, folder_name=folder_path, imageset_name=imageset_name)
        try:
            imageset.refresh_files_from_fs()
        except Exception:
            # best-effort only
            pass

        data = imageset.to_dict()

        cover_basename = os.path.basename(data.get("cover_image") or "")
        orig_basename = os.path.basename(imageset.orig_image) if imageset.orig_image else ""

        interview_path = imageset.get_file_interview()
        interview_text = _read_text_file(interview_path)

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(_template_dir(config)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )

        template = env.get_template("imageset_report.html")

        html = template.render(
            imageset=data,
            folder_path=folder_path,
            imageset_name=imageset_name,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cover_basename=cover_basename,
            orig_basename=orig_basename,
            interview_text=interview_text,
        )

        out_path = os.path.join(imageset_folder, f"{imageset_name}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        logging.info("Wrote imageset report: %s", out_path)
        return True

    except jinja2.exceptions.TemplateNotFound:
        logging.error("Template not found: %s", os.path.join(_template_dir(config), "imageset_report.html"))
        return False
    except Exception as e:
        logging.error("generate_html_report failed: %s", e, exc_info=True)
        return False


def process_interview(folder_name: str, imageset_name: str, interview_template: str, config: Config) -> bool:
    """
    Run an interview for an imageset, then regenerate the static HTML report.
    """
    try:
        folder_path = _resolve_folder_path(config, folder_name)
        imageset_folder = os.path.join(folder_path, imageset_name)
        if not os.path.isdir(imageset_folder):
            logging.error("Imageset folder does not exist: %s", imageset_folder)
            return False

        imageset = Imageset(config=config, folder_name=folder_path, imageset_name=imageset_name)
        result = imageset.interview_image(version="orig", interview_template=interview_template)
        if not result:
            logging.error("Interview returned no result for imageset: %s", imageset_name)
            return False

        # Update report so the interview output is visible.
        return generate_html_report(folder_path, imageset_name, config)

    except Exception as e:
        logging.error("process_interview failed: %s", e, exc_info=True)
        return False

