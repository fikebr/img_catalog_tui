"""
One-time helper to backfill the posted_to column in the imagesets table.

Usage:
    uv run scripts/migrate_posted_to.py
"""

from __future__ import annotations

import logging
import sys

from img_catalog_tui.config import Config
from img_catalog_tui.core.imageset import Imageset
from img_catalog_tui.db.imagesets import ImagesetsTable
from img_catalog_tui.db.utils import get_connection
from img_catalog_tui.logger import setup_logging


def ensure_posted_to_column(config: Config) -> None:
    """Add the posted_to column to imagesets if it does not already exist."""
    try:
        with get_connection(config) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(imagesets)")
            column_names = {row["name"] for row in cursor.fetchall()}
            if "posted_to" in column_names:
                logging.info("posted_to column already exists on imagesets table")
                return

            cursor.execute("ALTER TABLE imagesets ADD COLUMN posted_to TEXT")
            logging.info("Added posted_to column to imagesets table")
    except Exception as exc:
        logging.error("Failed to ensure posted_to column exists: %s", exc, exc_info=True)
        raise


def fetch_imageset_rows(config: Config) -> list[dict]:
    """Fetch lightweight imageset records from the database."""
    try:
        with get_connection(config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, folder_path, name, posted_to FROM imagesets ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as exc:
        logging.error("Failed to load imageset rows: %s", exc, exc_info=True)
        raise


def read_posted_to_from_toml(config: Config, folder_path: str, imageset_name: str) -> str | None:
    """Read posted_to from the TOML file; returns None when it cannot be loaded."""
    try:
        imageset_obj = Imageset(config=config, folder_name=folder_path, imageset_name=imageset_name)
        value = imageset_obj.posted_to or ""
        return value.strip()
    except FileNotFoundError:
        logging.warning(
            "Skipping imageset '%s' because folder path was not found: %s",
            imageset_name,
            folder_path,
        )
    except Exception as exc:
        logging.error(
            "Failed to read posted_to for '%s' (%s): %s",
            imageset_name,
            folder_path,
            exc,
            exc_info=True,
        )
    return None


def migrate_posted_to() -> int:
    """Perform the posted_to migration and return a non-zero status code on failures."""
    config = Config()
    ensure_posted_to_column(config)

    rows = fetch_imageset_rows(config)
    if not rows:
        logging.info("No imagesets found; nothing to migrate.")
        return 0

    table = ImagesetsTable(config)
    updated = 0
    skipped = 0
    failures = 0

    for row in rows:
        imageset_id = row["id"]
        folder_path = row["folder_path"]
        imageset_name = row["name"]
        toml_value = read_posted_to_from_toml(config, folder_path, imageset_name)

        if toml_value is None:
            skipped += 1
            continue

        current_value = (row.get("posted_to") or "").strip()
        if current_value == toml_value:
            skipped += 1
            continue

        try:
            success = table.update_field(imageset_id, "posted_to", toml_value)
            if success:
                updated += 1
                logging.debug(
                    "Backfilled posted_to for imageset id=%s (%s): '%s'",
                    imageset_id,
                    imageset_name,
                    toml_value,
                )
            else:
                failures += 1
                logging.error(
                    "Database update returned False when setting posted_to for id=%s (%s)",
                    imageset_id,
                    imageset_name,
                )
        except Exception as exc:
            failures += 1
            logging.error(
                "Failed to update posted_to for id=%s (%s): %s",
                imageset_id,
                imageset_name,
                exc,
                exc_info=True,
            )

    logging.info(
        "posted_to migration complete. updated=%s, skipped=%s, failures=%s",
        updated,
        skipped,
        failures,
    )
    return 0 if failures == 0 else 1


def main() -> None:
    """CLI entry point."""
    setup_logging()

    try:
        exit_code = migrate_posted_to()
    except Exception as exc:
        logging.error("posted_to migration failed: %s", exc, exc_info=True)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

