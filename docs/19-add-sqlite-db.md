# Database Schema Analysis

## Overview
This document outlines the database schema requirements for migrating from TOML-based storage to SQLite. The analysis is based on the current application structure and data models.

## Table: `folders`

Stores registered folder paths that contain imagesets.

### Fields:
- **id** (INTEGER PRIMARY KEY AUTOINCREMENT) - Unique identifier
- **name** (TEXT NOT NULL UNIQUE) - Folder basename (e.g., "2025-08-17")
- **path** (TEXT NOT NULL) - Full filesystem path to the folder
- **created_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - When folder was registered
- **updated_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - Last update time

### Indexes:
- `idx_folders_name` on `name`
- `idx_folders_path` on `path`

### Notes:
- Currently stored as `dict[str, str]` in `folders.toml` where key=name, value=path
- Used by `Folders` class to manage folder registry

---

## Table: `imagesets`

Stores metadata about each imageset (a folder containing related images).

### Fields:
- **id** (INTEGER PRIMARY KEY AUTOINCREMENT) - Unique identifier
- **folder_id** (INTEGER NOT NULL) - Foreign key to `folders.id`
- **name** (TEXT NOT NULL) - Imageset name (folder basename)
- **folder_path** (TEXT NOT NULL) - Full path to parent folder (denormalized for performance)
- **imageset_folder_path** (TEXT NOT NULL) - Full path to imageset folder
- **status** (TEXT) - Current status: "new", "keep", "edit", "working", "posted", "archive"
- **edits** (TEXT) - Comma-separated list: "creative", "photoshop", "rmbg", "up", "vector"
- **needs** (TEXT) - Comma-separated list: "orig", "thumbnail", "interview", "mockups"
- **good_for** (TEXT) - Comma-separated list: "stock", "rb", "poster", "sticker"
- **source** (TEXT) - Image source: "midjourney", "fooocus", "freepik", "other", "unknown"
- **prompt** (TEXT) - Main prompt text (from source-specific section)
- **cover_image_path** (TEXT) - Full path to cover image file
- **orig_image_path** (TEXT) - Full path to original image file
- **created_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - When imageset was created
- **updated_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - Last update time

### Foreign Keys:
- `folder_id` REFERENCES `folders(id)` ON DELETE CASCADE

### Indexes:
- `idx_imagesets_folder_id` on `folder_id`
- `idx_imagesets_name` on `name`
- `idx_imagesets_status` on `status`
- `idx_imagesets_source` on `source`
- `idx_imagesets_folder_name` on `folder_id, name` (composite, for lookups)

### Notes:
- Currently stored in `{imageset_name}.toml` files within each imageset folder
- Top-level fields: imageset, source, status, edits, needs
- `folder_path` and `imageset_folder_path` are denormalized for quick access without joins
- `cover_image_path` and `orig_image_path` are computed properties but cached here for performance

---

## Table: `imageset_sections`

Stores section-based metadata for imagesets (replaces TOML sections like `[biz]`, `[midjourney]`, `[fooocus]`, etc.).

### Fields:
- **id** (INTEGER PRIMARY KEY AUTOINCREMENT) - Unique identifier
- **imageset_id** (INTEGER NOT NULL) - Foreign key to `imagesets.id`
- **section_name** (TEXT NOT NULL) - Section name: "biz", "review", "interview", "midjourney", "fooocus", "other"
- **section_data** (TEXT) - JSON string containing all key-value pairs for this section
- **created_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - When section was created
- **updated_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - Last update time

### Foreign Keys:
- `imageset_id` REFERENCES `imagesets(id)` ON DELETE CASCADE

### Indexes:
- `idx_imageset_sections_imageset_id` on `imageset_id`
- `idx_imageset_sections_name` on `section_name`
- `idx_imageset_sections_imageset_name` on `imageset_id, section_name` (composite, unique)

### Unique Constraints:
- `(imageset_id, section_name)` - One section of each type per imageset

### Notes:
- Stores flexible JSON data for source-specific metadata (midjourney, fooocus, etc.)
- Common sections:
  - `[biz]`: good_for, posted_to
  - `[review]`: needs
  - `[interview]`: interview_date, template_used, title, description
  - `[midjourney]`: description, prompt, jobid, and other midjourney-specific fields
  - `[fooocus]`: Prompt, Negative Prompt, Performance, Resolution, Base Model, etc.

---

## Table: `interviews`

Stores AI-generated interview data for imagesets.

### Fields:
- **id** (INTEGER PRIMARY KEY AUTOINCREMENT) - Unique identifier
- **imageset_id** (INTEGER NOT NULL) - Foreign key to `imagesets.id`
- **interview_template** (TEXT NOT NULL) - Template name used (e.g., "default", "basic")
- **image_file_path** (TEXT NOT NULL) - Full path to image file used for interview
- **interview_response** (TEXT) - Full text response from AI interview
- **interview_raw** (TEXT) - Raw JSON response from API (stored as JSON string)
- **interview_parsed** (TEXT) - Parsed JSON results (stored as JSON string)
  - Contains: `etsy_post` (title, description, tags)
  - Contains: `redbubble_post` (title, description, tags)
- **created_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - When interview was created
- **updated_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - Last update time

### Foreign Keys:
- `imageset_id` REFERENCES `imagesets(id)` ON DELETE CASCADE

### Indexes:
- `idx_interviews_imageset_id` on `imageset_id`
- `idx_interviews_template` on `interview_template`
- `idx_interviews_created_at` on `created_at`

### Notes:
- Currently stored as files: `{image_file}_interview.txt`, `{image_file}_interview_raw.txt`, `{image_file}_interview.json`
- One interview per imageset (or multiple if different templates are used)
- `interview_parsed` contains structured data for Etsy and Redbubble posts
- Related data also stored in `imageset_sections` with section_name="interview"

---

## Table: `imagesetfiles`

Stores information about files within each imageset folder.

### Fields:
- **id** (INTEGER PRIMARY KEY AUTOINCREMENT) - Unique identifier
- **imageset_id** (INTEGER NOT NULL) - Foreign key to `imagesets.id`
- **filename** (TEXT NOT NULL) - Filename (basename only)
- **fullpath** (TEXT NOT NULL) - Full filesystem path to file
- **extension** (TEXT) - File extension (e.g., ".png", ".jpg", ".toml")
- **file_type** (TEXT) - Type classification: "image", "toml", "text", "interview", "other"
- **file_size** (INTEGER) - File size in bytes
- **created_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - When file was discovered/added
- **updated_at** (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) - Last update time

### Foreign Keys:
- `imageset_id` REFERENCES `imagesets(id)` ON DELETE CASCADE

### Indexes:
- `idx_imagesetfiles_imageset_id` on `imageset_id`
- `idx_imagesetfiles_filename` on `filename`
- `idx_imagesetfiles_file_type` on `file_type`
- `idx_imagesetfiles_imageset_filename` on `imageset_id, filename` (composite, unique)

### Unique Constraints:
- `(imageset_id, filename)` - One file per name per imageset

### Notes:
- Currently stored in memory as `dict{filename: dict{fullpath, ext, tags, file_type}}`
- Files are scanned from filesystem on imageset initialization
- File tags (orig, thumb, v2, etc.) are extracted from filename patterns

---

## Table: `imagesetfile_tags`

Junction table for many-to-many relationship between files and tags.

### Fields:
- **id** (INTEGER PRIMARY KEY AUTOINCREMENT) - Unique identifier
- **imagesetfile_id** (INTEGER NOT NULL) - Foreign key to `imagesetfiles.id`
- **tag** (TEXT NOT NULL) - Tag name: "orig", "thumb", "v2", "v3", "v4", "v5", "up2", "up3", "up4", "up6", "interview", "raw", "watermark"

### Foreign Keys:
- `imagesetfile_id` REFERENCES `imagesetfiles(id)` ON DELETE CASCADE

### Indexes:
- `idx_imagesetfile_tags_file_id` on `imagesetfile_id`
- `idx_imagesetfile_tags_tag` on `tag`
- `idx_imagesetfile_tags_file_tag` on `imagesetfile_id, tag` (composite, unique)

### Unique Constraints:
- `(imagesetfile_id, tag)` - One tag per file per tag type

### Notes:
- Tags are extracted from filename patterns like `_{tag}_` or `_{tag}.`
- Currently stored as `tags: list[str]` in the files dict
- Normalized into separate table for better querying and indexing

---

## Relationships Summary

```
folders (1) ──< (many) imagesets
imagesets (1) ──< (many) imageset_sections
imagesets (1) ──< (many) interviews
imagesets (1) ──< (many) imagesetfiles
imagesetfiles (1) ──< (many) imagesetfile_tags
```

---

## Migration Considerations

1. **Data Migration**: Need to migrate existing TOML files to SQLite
   - `folders.toml` → `folders` table
   - `{imageset_name}.toml` → `imagesets` + `imageset_sections` tables
   - File system scan → `imagesetfiles` + `imagesetfile_tags` tables
   - Interview files → `interviews` table

2. **Backward Compatibility**: Application currently supports both TOML and SQLite backends
   - Storage backend selection via config: `toml`, `sqlite`, or `dual`
   - Dual mode allows gradual migration

3. **Performance**: 
   - Denormalized paths in `imagesets` table for faster lookups
   - Indexes on commonly queried fields (status, source, folder_id)
   - JSON storage for flexible section data

4. **Data Integrity**:
   - Foreign key constraints ensure referential integrity
   - Unique constraints prevent duplicates
   - Cascade deletes maintain consistency

5. **File System Sync**:
   - `imagesetfiles` table needs periodic refresh when files change
   - Consider triggers or background sync jobs

---

## Additional Notes

- Timestamps (`created_at`, `updated_at`) are useful for auditing and change tracking
- JSON fields (`section_data`, `interview_raw`, `interview_parsed`) allow flexible schema evolution
- File paths are stored as TEXT to support cross-platform compatibility
- Consider adding a `deleted_at` timestamp for soft deletes if needed
- Consider adding a `version` field to `imagesets` for optimistic locking if concurrent updates are expected

---

## Implementation

### Database Modules

All database operations are encapsulated in modules within `img_catalog_tui/db/`:

#### Core Modules

1. **`utils.py`** - Database utilities and initialization
   - `get_db_path(config)` - Get database path from config
   - `init_database(config)` - Initialize database with all tables and indexes
   - `get_connection(config)` - Context manager for database connections
   - `close_connection(conn)` - Safely close database connections

2. **`folders.py`** - `FoldersTable` class
   - CRUD operations for folders table
   - Methods: `create()`, `get_by_id()`, `get_by_name()`, `get_by_path()`, `get_all()`, `get_all_dict()`, `update()`, `delete()`, `delete_by_name()`

3. **`imagesets.py`** - `ImagesetsTable` class
   - CRUD operations for imagesets table
   - Methods: `create()`, `get_by_id()`, `get_by_folder_and_name()`, `get_by_folder_path_and_name()`, `get_by_folder_id()`, `get_by_status()`, `update_field()`, `update()`, `delete()`

4. **`imageset_sections.py`** - `ImagesetSectionsTable` class
   - CRUD operations for imageset_sections table
   - Handles JSON serialization/deserialization for flexible section data
   - Methods: `create()`, `get_by_id()`, `get_by_imageset_and_section()`, `get_by_imageset_id()`, `get_section_dict()`, `get_field()`, `update()`, `set_field()`, `delete()`, `delete_by_imageset_id()`

5. **`interviews.py`** - `InterviewsTable` class
   - CRUD operations for interviews table
   - Handles JSON serialization for interview_raw and interview_parsed
   - Methods: `create()`, `get_by_id()`, `get_by_imageset_id()`, `get_latest_by_imageset_id()`, `get_by_template()`, `update()`, `delete()`, `delete_by_imageset_id()`

6. **`imagesetfiles.py`** - `ImagesetFilesTable` class
   - CRUD operations for imagesetfiles table
   - Filesystem synchronization support
   - Methods: `create()`, `get_by_id()`, `get_by_imageset_and_filename()`, `get_by_imageset_id()`, `get_by_file_type()`, `get_files_dict()`, `update()`, `delete()`, `delete_by_imageset_id()`, `sync_from_filesystem()`

7. **`imagesetfile_tags.py`** - `ImagesetFileTagsTable` class
   - CRUD operations for imagesetfile_tags junction table
   - Methods: `create()`, `get_by_id()`, `get_tags_by_file_id()`, `get_files_by_tag()`, `set_tags_for_file()`, `add_tag()`, `remove_tag()`, `delete_by_file_id()`

8. **`sync.py`** - Synchronization functions
   - Bidirectional sync between TOML files and database
   - Functions:
     - `sync_folders_toml_to_db(config)` - Sync folders from TOML to database
     - `sync_folders_db_to_toml(config)` - Sync folders from database to TOML
     - `sync_imageset_toml_to_db(config, folder_path, imageset_name)` - Sync single imageset from TOML to database
     - `sync_imageset_db_to_toml(config, folder_path, imageset_name)` - Sync single imageset from database to TOML
     - `sync_all_imagesets_toml_to_db(config, folder_path=None)` - Sync all imagesets from TOML to database
     - `sync_interview_db_to_files(config, imageset_id, imageset_folder_path)` - Sync interview from database to filesystem

### Usage Examples

#### Initialize Database

Using the command line:
```bash
# Initialize empty database with tables and indexes
uv run -m img_catalog_tui.db.utils
```

Or using Python code:
```python
from img_catalog_tui.config import Config
from img_catalog_tui.db.utils import init_database

config = Config()
init_database(config)
```

#### Sync TOML Data to Database

Load all existing TOML data into the database:
```bash
# Sync folders and all imagesets from TOML files to database
uv run -m img_catalog_tui.db.sync
```

This will:
- Sync all folders from `folders.toml` to the database
- Scan all registered folders for imagesets
- Sync each imageset's TOML data to the database
- Sync files and tags from the filesystem
- Sync interview files if they exist

#### Working with Folders

```python
from img_catalog_tui.db.folders import FoldersTable

folders_table = FoldersTable(config)

# Create a folder
folder_id = folders_table.create("2025-01-15", "/path/to/folder")

# Get folder by name
folder = folders_table.get_by_name("2025-01-15")

# Get all folders as dict
folders_dict = folders_table.get_all_dict()  # {name: path, ...}
```

#### Working with Imagesets

```python
from img_catalog_tui.db.imagesets import ImagesetsTable

imagesets_table = ImagesetsTable(config)

# Create an imageset
imageset_id = imagesets_table.create(
    folder_id=folder_id,
    name="my_imageset",
    folder_path="/path/to/folder",
    imageset_folder_path="/path/to/folder/my_imageset",
    status="new",
    source="fooocus"
)

# Get imageset by folder and name
imageset = imagesets_table.get_by_folder_path_and_name(
    "/path/to/folder", 
    "my_imageset"
)

# Update a field
imagesets_table.update_field(imageset_id, "status", "working")
```

#### Working with Sections

```python
from img_catalog_tui.db.imageset_sections import ImagesetSectionsTable

sections_table = ImagesetSectionsTable(config)

# Create/update a section
biz_data = {
    "good_for": "stock,rb",
    "posted_to": "etsy,redbubble"
}
sections_table.update(imageset_id, "biz", biz_data)

# Get a section
biz_section = sections_table.get_section_dict(imageset_id, "biz")

# Get a specific field
good_for = sections_table.get_field(imageset_id, "biz", "good_for")
```

#### Working with Files

```python
from img_catalog_tui.db.imagesetfiles import ImagesetFilesTable
from img_catalog_tui.db.imagesetfile_tags import ImagesetFileTagsTable

files_table = ImagesetFilesTable(config)
tags_table = ImagesetFileTagsTable(config)

# Sync files from filesystem
files_table.sync_from_filesystem(imageset_id, imageset_folder_path, config)

# Get files as dict (compatible with Imageset.files structure)
files_dict = files_table.get_files_dict(imageset_id)

# Add tags to a file
file_record = files_table.get_by_imageset_and_filename(imageset_id, "image.png")
tags_table.set_tags_for_file(file_record['id'], ["orig", "thumb"])
```

#### Synchronization

```python
from img_catalog_tui.db.sync import (
    sync_folders_toml_to_db,
    sync_all_imagesets_toml_to_db,
    sync_imageset_db_to_toml
)

# Sync all folders from TOML to database
sync_folders_toml_to_db(config)

# Sync all imagesets from TOML to database
count = sync_all_imagesets_toml_to_db(config)

# Sync a specific imageset from database back to TOML
sync_imageset_db_to_toml(config, "/path/to/folder", "my_imageset")
```

### Connection Management

All database operations use a context manager for safe connection handling:

```python
from img_catalog_tui.db.utils import get_connection

with get_connection(config) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM folders")
    rows = cursor.fetchall()
    # Connection automatically committed and closed
```

### Error Handling

All modules implement comprehensive error handling with logging:
- Database errors are logged with full stack traces
- Methods return `None` or `False` on failure
- Exceptions are caught and logged, not re-raised (for graceful degradation)

### Features

- **Foreign Key Constraints**: Cascade deletes maintain referential integrity
- **Indexes**: Optimized for common query patterns
- **JSON Support**: Flexible storage for sections and interview data
- **Filesystem Sync**: Automatic synchronization of file metadata
- **Bidirectional Sync**: TOML ↔ Database migration support
- **Context Managers**: Safe connection handling
- **Logging**: Comprehensive logging for debugging and auditing

