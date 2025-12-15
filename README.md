# Image Catalog TUI

A terminal user interface (TUI) application for organizing and managing image collections.

## Features

- Organize images into image sets
- Extract metadata from EXIF data
- Support for Midjourney and Fooocus AI-generated images
- Generate HTML reports and indexes
- Interactive interview system for image metadata

## Installation

This application is distributed as a standalone executable. No installation is required.

### Development Setup

1. Clone the repository
2. Create a virtual environment using uv:
   ```
   uv venv
   ```
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. Install dependencies:
   ```
   uv pip install -e .
   ```

## Usage

```
img-catalog-tui --input_folder <path_to_images> [--config_file <path_to_config>]
```

## Database + TOML sync (explicit commands)

DB is authoritative. Use these explicit commands when you want to initialize the DB schema or import/export TOML.

```bash
# Initialize SQLite schema (creates tables/indexes)
uv run -m img_catalog_tui.db.sync init-db

# Import folders + imagesets from TOML/filesystem into DB (manual TOML edits supported)
uv run -m img_catalog_tui.db.sync import-toml

# Export folders + imagesets from DB into TOML files
uv run -m img_catalog_tui.db.sync export-toml
```

### Required Parameters:
- `--input_folder`: Path to the folder containing images to process

### Optional Parameters:
- `--config_file`: Path to configuration file (default: `.\config.toml`)

## Configuration

The application uses TOML files for configuration. See the documentation for details.

## License

MIT
