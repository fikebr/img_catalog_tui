# 19 – Add Search Implementation Guide

This document explains how to run the one-time database migration, verify the new search service, and use the HTML search + results experience introduced for issue 19.

## 1. Database Preparation

1. Ensure the application virtual environment is active.
2. Run the migration with `uv run scripts/migrate_posted_to.py`.
   - The script adds the `posted_to` column (if missing) and backfills all records by reading each imageset’s TOML file.
   - Logging goes to both the configured log file and stdout. Any rows that fail to backfill are reported at the end so you can retry after fixing the underlying issue.
3. If you clone the project onto a fresh machine, the same script can safely be re-run; it detects existing columns automatically.

## 2. Verification & Tests

- Execute `uv run pytest` to run the new `tests/test_search_service.py` suite. The fixture provisions a scratch SQLite database, seeds representative data, and validates every search permutation (prompt, folder, name, and both status-based workflows).
- For manual smoke tests, visit `/search`, run each form, and confirm the results page renders data pulled directly from the SQLite tables (not from TOML files).

## 3. Search Form Overview (`/search`)

The catalog search page contains five discrete forms, each rendered in its own card:

| Card | Description | Required Fields |
| --- | --- | --- |
| Prompt Contains | `prompt` column contains the supplied substring | Prompt text |
| Status + Good For + Posted To | `status == X`, `good_for LIKE Y`, `posted_to` does *not* contain Z | Status, Good For tag, Posted To exclusion tag |
| Folder Lookup | Finds every imageset linked to a folder name or absolute path | Folder name or path |
| Imageset Name Contains | Fuzzy match on `imagesets.name` | Partial name |
| Status + Needs | Matches status and optionally a needs substring. If no substring is provided, all non-empty needs entries for that status are returned. | Status (needs substring optional) |

Each form uses `GET` and `target="_blank"` so you can open multiple result tabs without losing your in-progress filters.

## 4. Results Grid (`/search/results`)

- **Table controls** – Column-level filters, sortable headers, hide/unhide toggles, and responsive layout for narrow screens.
- **Row actions** – Direct links to the detail view, edit modal (popup), move dialog, and a copy-to-clipboard shortcut for the filesystem path.
- **Bulk actions** – Select rows with the leftmost checkboxes to enable:
  - *Move Selected*: generates links that open each `imageset_move_form` page in new tabs (existing move workflow).
  - *Review Selected*: produces one link per folder pointing to the review list UI so you can launch the current review flow.
  - *Export CSV*: downloads either the selected rows or every visible row (when nothing is selected) into a CSV snapshot.

All client-side logic includes guardrails and console logging so future API-based implementations can replace the stubs with minimal churn.

## 5. Operational Notes

- The migration script and the search service both rely on the shared logging configuration, so failures are easy to triage in `logs/app.log`.
- Because the search service sits in `img_catalog_tui/services/search.py`, backend callers (HTML views or future APIs) can import `SearchService` without duplicating SQL.
- If you add new search forms later, wire them into `SearchService` first, then expose them in `/search` so all filtering stays consistent and testable.

