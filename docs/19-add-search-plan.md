# 19-add-search-plan

## Overview

Implement DB-only search workflows with a dedicated search & results experience, bulk result actions, and the missing `posted_to` persistence. Focus on HTML/TUI views and backend helpers; defer API-specific work per spec.

## Steps

1. **DB & Model Schema**

   - Extend the SQLite schema (e.g., `db/schema.sql`) and DAO in [`img_catalog_tui/db/imagesets.py`](img_catalog_tui/db/imagesets.py) to include a nullable `posted_to` column across `create`, `update`, `update_field`, fetch helpers, and row serialization. This ties in with the existing TOML-only property:
```290:298:img_catalog_tui/core/imageset.py
    def posted_to(self) -> str:
        return self.toml.get(section="biz", key="posted_to")
```

   - Ensure setters sync DB + TOML without duplicating validation, and add logging for both success and failure paths (loggers already configured to file/screen).

2. **One-Time Migration Script**

   - Add `scripts/migrate_posted_to.py` (or similar) that uses `uv run ...` to: add the column (ALTER TABLE if missing), hydrate each row from the TOML-backed `Imageset` objects, and report successes/failures with graceful error capture so the script can resume or exit cleanly.
   - Document execution steps in `docs/19-add-search-plan.md` plus README snippet so the user can run it once.

3. **Search Query Service**

   - Introduce a dedicated module (e.g., [`img_catalog_tui/services/search.py`](img_catalog_tui/services/search.py)) that composes SQL queries for each search type listed in the doc (prompt substring, status/good_for/posted_to combo, folder exact, imageset_name substring, status/needs logic). Keep logic DB-only, return normalized result dicts, and add structured logging and try/except guards.
   - Provide unit tests around these query builders using the existing SQLite test harness to ensure filtering, negations, and null-handling work as expected.

4. **HTML Views & Templates**

   - Add search routes/pages in [`img_catalog_tui/flask/views_html.py`](img_catalog_tui/flask/views_html.py) without touching API routes. Create `templates/search.html` for the search form (each search type in its own accordion/section) and `templates/search_results.html` for the results grid. Ensure both pages stream logs and gracefully show validation errors instead of 500s.
   - Wire the search form to open results in a new tab (target `_blank`) and submit to the new search-results view, ensuring CSRF/session patterns match existing pages.

5. **Results UX Enhancements**

   - Implement a client-side table (existing JS stack or lightweight vanilla) supporting column sorting, filtering, hide/unhide toggles, selection checkboxes, and bulk actions (move, review, export). Hook bulk actions into existing review/export flows; stub any future API hooks with TODOs but keep behavior limited to DB-backed operations.
   - Add row-level actions: open imageset, open edit modal, copy folder path. Reuse existing modal/components where possible to avoid duplication.

6. **Logging, Errors, and Config**

   - Confirm new modules reuse the shared logging config so entries go to both file and stdout/stderr. Wrap DB/file I/O in try/except blocks that emit actionable error messages to the UI and logs. Surface user-facing flash messages for recoverable issues.

7. **Documentation & Validation**

   - Capture usage notes, script instructions, and any new config toggles in the new [`docs/19-add-search-plan.md`](docs/19-add-search-plan.md) file. Include test plan bullets covering migration dry-run, search cases, and bulk actions.
   - Update existing docs (e.g., PRD or README) if terminology or workflows change.

## Initial Todos

- `db-schema`: Add `posted_to` column + DAO wiring
- `migration-script`: Build one-off `posted_to` backfill script
- `search-service`: Implement DB search helpers + tests
- `search-ui`: Create search/results pages with UX requirements
- `docs-plan`: Write `docs/19-add-search-plan.md` with steps/tests