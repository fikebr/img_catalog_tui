"""Database-backed search helpers for imagesets."""

import logging
import os

from img_catalog_tui.config import Config
from img_catalog_tui.db.utils import get_connection


class SearchService:
    """Encapsulates DB-only search workflows."""

    _BASE_SELECT = """
        SELECT
            imagesets.id,
            imagesets.folder_id,
            folders.name AS folder_name,
            imagesets.name AS imageset_name,
            imagesets.folder_path,
            imagesets.imageset_folder_path,
            imagesets.status,
            imagesets.edits,
            imagesets.needs,
            imagesets.good_for,
            imagesets.posted_to,
            imagesets.prompt,
            imagesets.cover_image_path,
            imagesets.orig_image_path,
            imagesets.updated_at
        FROM imagesets
        LEFT JOIN folders ON folders.id = imagesets.folder_id
    """

    def __init__(self, config: Config):
        self.config = config

    def search_by_prompt(self, prompt_text: str) -> list[dict]:
        """Search imagesets whose prompt contains the provided text."""
        value = prompt_text.strip().lower()
        if not value:
            logging.warning("search_by_prompt called with empty prompt_text")
            return []

        clause = "imagesets.prompt IS NOT NULL AND LOWER(imagesets.prompt) LIKE ?"
        params = (self._like_param(value),)
        return self._run_query(clause, params)

    def search_status_good_for_posted_to(
        self,
        status: str,
        good_for_contains: str,
        posted_to_excludes: str,
    ) -> list[dict]:
        """Search by status + good_for must contain + posted_to must not contain."""
        status_value = status.strip().lower()
        good_for_value = good_for_contains.strip().lower()
        exclude_value = posted_to_excludes.strip().lower()

        if not status_value or not good_for_value or not exclude_value:
            logging.warning("search_status_good_for_posted_to missing required filters")
            return []

        clause = (
            "LOWER(imagesets.status) = ? "
            "AND imagesets.good_for IS NOT NULL "
            "AND LOWER(imagesets.good_for) LIKE ? "
            "AND (imagesets.posted_to IS NULL "
            "     OR TRIM(imagesets.posted_to) = '' "
            "     OR LOWER(imagesets.posted_to) NOT LIKE ?)"
        )
        params = (
            status_value,
            self._like_param(good_for_value),
            self._like_param(exclude_value),
        )
        return self._run_query(clause, params)

    def search_by_folder(self, folder_identifier: str) -> list[dict]:
        """Search all imagesets that belong to a folder name or path."""
        identifier = folder_identifier.strip().lower()
        if not identifier:
            logging.warning("search_by_folder called with empty identifier")
            return []

        clause = (
            "LOWER(folders.name) = ? "
            "OR LOWER(imagesets.folder_path) = ? "
            "OR LOWER(imagesets.folder_path) LIKE ?"
        )
        params = (identifier, identifier, self._contains_anywhere(identifier))
        return self._run_query(clause, params, order_by="ORDER BY imagesets.name ASC")

    def search_imageset_name(self, name_contains: str) -> list[dict]:
        """Search imagesets whose name contains the provided text."""
        value = name_contains.strip().lower()
        if not value:
            logging.warning("search_imageset_name called with empty value")
            return []

        clause = "LOWER(imagesets.name) LIKE ?"
        params = (self._like_param(value),)
        return self._run_query(clause, params)

    def search_status_and_needs(self, status: str, needs_contains: str | None = None) -> list[dict]:
        """Search by status plus needs contains (or anything non-null if no value)."""
        status_value = status.strip().lower()
        if not status_value:
            logging.warning("search_status_and_needs called with empty status")
            return []

        clause = "LOWER(imagesets.status) = ? AND "
        params: list[str] = [status_value]

        if needs_contains and needs_contains.strip():
            needs_value = needs_contains.strip().lower()
            clause += "LOWER(imagesets.needs) LIKE ?"
            params.append(self._like_param(needs_value))
        else:
            clause += "(imagesets.needs IS NOT NULL AND TRIM(imagesets.needs) <> '')"

        return self._run_query(clause, tuple(params))

    def _run_query(self, where_clause: str, params: tuple, order_by: str | None = None) -> list[dict]:
        sql = self._BASE_SELECT
        if where_clause:
            sql = f"{sql} WHERE {where_clause}"
        if order_by:
            sql = f"{sql} {order_by}"
        else:
            sql = f"{sql} ORDER BY imagesets.updated_at DESC, imagesets.name ASC"

        try:
            with get_connection(self.config) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                normalized = [self._normalize_row(dict(row)) for row in rows]
                logging.debug("Search returned %s rows", len(normalized))
                return normalized
        except Exception as exc:
            logging.error("Search query failed: %s", exc, exc_info=True)
            return []

    @staticmethod
    def _like_param(value: str) -> str:
        return f"%{value}%"

    @staticmethod
    def _contains_anywhere(value: str) -> str:
        return f"%{value}%"

    @staticmethod
    def _derive_folder_name(folder_path: str) -> str:
        normalized_path = folder_path.rstrip("\\/") if folder_path else ""
        return os.path.basename(normalized_path) if normalized_path else ""

    def _normalize_row(self, row: dict) -> dict:
        folder_path = row.get("folder_path") or ""
        folder_name = row.get("folder_name") or self._derive_folder_name(folder_path)

        return {
            "id": row.get("id"),
            "folder_id": row.get("folder_id"),
            "folder_name": folder_name,
            "folder_path": folder_path,
            "imageset_folder_path": row.get("imageset_folder_path") or "",
            "imageset_name": row.get("imageset_name") or "",
            "status": row.get("status") or "",
            "edits": row.get("edits") or "",
            "needs": row.get("needs") or "",
            "good_for": row.get("good_for") or "",
            "posted_to": row.get("posted_to") or "",
            "prompt": row.get("prompt") or "",
            "cover_image_path": row.get("cover_image_path") or "",
            "orig_image_path": row.get("orig_image_path") or "",
        }

