# 19-add-search Implementation Plan

## Objectives
- Provide a dedicated search workflow (search form + results view in new tab) that covers all requested search types and required table interactions.
- Keep the experience responsive for large result sets, while reusing existing folder/imageset abstractions and consistent logging/error-handling patterns.

## Current Context to Leverage
- Imageset metadata already lives in SQLite via `img_catalog_tui/db/*.py` with helpers such as `ImagesetsTable` for CRUD operations.
- Flask HTML routes (`img_catalog_tui/flask/views_html.py`) and API routes (`views_api.py`) deliver other management pages; `base.html` defines global layout and CSS in `static/css/main.css`.
- `img_catalog_tui/core/search.py` exists but is empty, giving us a natural place to centralize query orchestration.

## Backend Work
1. **Search query layer**
   - Implement `img_catalog_tui/core/search.py` with a `SearchService` (or similar) that accepts search type + criteria, performs validation, and executes SQLite queries via existing DB helpers.
   - Support search types listed in the spec (prompt, status/good_for/posted_to, folder exact match, imageset name contains, status+needs). Each search type should map to parameterized SQL with indexes where necessary.
   - Normalize outputs to a single DTO (folder_name, imagesetname, etc.) so the UI can consume consistent columns regardless of search type.
   - Add defensive logging (file + screen) for query execution time, parameter validation failures, and empty result sets; surface user-friendly error messages while logging stack traces for debugging.
2. **Bulk actions & mutations**
   - Reuse existing batch update pathways (`ImagesetBatch` and `views_api.batch_update`) by exposing helper endpoints that accept a list of imageset identifiers from the search results.
   - For "move" and "perform review" operations, identify whether existing API endpoints already cover these actions; otherwise outline new helper endpoints.

## Front-End (Flask Templates + JS)
1. **Search page (`templates/search.html`)**
   - Add navigation entry for Search.
   - Build sections for each search type with labeled inputs, inline validation, and a submit button that opens `/search/results?...` in a new tab (use `target="_blank"`).
   - Include quick presets or saved searches if helpful later (keep hooks in template for expansion).

2. **Results page (`templates/search_results.html`)**
   - Route submission posts criteria to a dedicated Flask view that invokes `SearchService`, stores criteria in session or signed token, and renders results server-side before sending HTML to the browser (still opened in a new tab).
   - Implement client-side table behavior (sorting, filtering, hide/unhide columns, multi-select checkboxes, responsive layout). A lightweight approach:
     - Use vanilla JS + CSS Grid/Flexbox for responsiveness.
     - Manage sorting/filtering in JS memory for now; if dataset size grows, round-trip through the same server-rendered route with updated parameters.
     - Provide column-visibility controls (checkbox list) that toggles `display: none` on column cells and persists preference per session.
   - Include a toolbar above the table for bulk actions and export triggers.

3. **Action buttons inside rows**
   - `Open imageset`: existing detail route `/folders/<foldername>/<imageset>`.
   - `Open edit pop-up`: reuse the edit form markup (e.g., from `imageset_edit.html`) inside a modal triggered by JS.
   - `Copy full folder path`: add a button that writes the path to the clipboard via `navigator.clipboard.writeText` and shows toast feedback.

## Bulk Actions UX
- Provide a select-all checkbox + per-row checkbox; maintain selected items in JS state.
- Bulk toolbar buttons:
  - **Move**: open modal to choose target folder, POST to a move endpoint (reuse folder utilities where possible).
  - **Perform review**: direct to existing review workflow with selected imagesets pre-populated; if existing review expects one imageset at a time, iterate through selections server-side or limit to single selection.
  - **Export data**: allow CSV export by reusing the server-side search view with `format=csv` flag (stream CSV) or by generating client-side CSV from the rendered dataset.

## Logging & Error Handling
- Ensure new service + views use `img_catalog_tui/logger.py` configuration so logs hit both file and stdout per user rule.
- Wrap DB/file interactions with try/except blocks that return actionable messages to the UI without exposing stack traces while logging full context.
- For client-side errors, show inline error banners and log them via an optional client-log view if needed (future enhancement).

## Testing & Validation
- Unit tests for `SearchService` covering each query type, parameter validation, and edge cases (empty criteria, missing folders, etc.).
- Integration tests (Flask test client) for the new search form/results views, ensuring correct status codes, rendered context, and error flows.
- Manual smoke test for UI: run Flask server, exercise search form, verify results page behavior (sorting/filtering/hiding columns, bulk actions, action buttons).
- Regression check on existing folder/imageset pages to ensure navigation additions do not break layout.

## Open Questions / Follow-ups
- Confirm whether search should run against live filesystem metadata or strictly the SQLite cache; plan above assumes DB-centric approach.
- Determine acceptable default pagination size and whether we need server-side filtering for extremely large datasets.
- Clarify specs for "perform a review" bulk action (sequential vs. aggregated workflow).
