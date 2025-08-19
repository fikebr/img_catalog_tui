# Image Catalog TUI - Product Requirements Document

## Overview
A terminal user interface (TUI) application that presents users with a menu of actions to manage and organize image collections.

## Technical Stack
- **Language**: Python
- **Package Management**: uv
- **Core Dependencies**: 
  - toml (0.10.2)
  - pillow
  - rich
  - textual
  - argparse
- **Distribution**: pyinstaller (for executable creation)

## Core Requirements

### Application Flow
- Load configuration and set up logging
- Parse command line arguments
- Load menu configuration from TOML file
- Present menu and handle user commands
- Execute selected operations with provided parameters

### User Interface
- Menu-driven TUI with single character selection keys (a-z)
- Reserved keys:
  - x: exit application
  - u: go up one level in menu hierarchy
  - h: display help
- Do not use x, u, or h for other menu options
- Keep menu logic separate from business logic to support future interface additions

### Command Line Parameters
- **input_folder**: (string) Required parameter with no default
- **config_file**: (string) Optional parameter with default value of `.\config.toml`

### Configuration Parameters
- **file_tags**: List of recognized tags for image files
  - Default tags: orig, thumb, v2, v3, v4, v5, up2, up3, up4, up6

### Menu Structure
1. **Folder Operations**
   - Scan: Analyze folder structure and organize images
   - Index: Generate index of images and create index.json and index.html

2. **Image Set Operations**
   - HTML: Create an HTML report of the imageset
   - Interview: Perform an interview for the imageset using a template

### Menu Configuration
The menu structure is defined in a TOML configuration file (`menu.toml`) with the following format:

```toml
[folder]

[folder.scan]
description = "scan a new folder of images"
command = "folder_scan"
questions = ["folder_name|What folder to scan?"]

[folder.index]
description = "index a folder that has already been scanned and create a index.json and a index.html"
command = "folder_index"
questions = ["folder_name|What folder to scan?"]

[imageset]

[imageset.html]
description = "Create an HTML report of the imageset"
command = "imageset_html"
questions = ["folder_name|What folder to scan?", "imageset|What imageset?"]

[imageset.interview]
description = "Perform an interview for the imageset."
command = "imageset_interview"
questions = ["folder_name|What folder to scan?", "imageset|What imageset?", "interview_template|What template to use for the interview?"]
```

Each menu option includes:
- A descriptive name
- The command to execute
- A list of questions to ask the user, with parameter name and prompt text

### Core Functionality

#### Folder Scanning
- Identify image sets within a folder
- Delete abandoned folders (those without image files)
- Tag original files in each image set
- Extract EXIF metadata from original images
- Generate/update TOML configuration files

#### Metadata Handling
- Support for different image sources:
  - Midjourney
  - Fooocus
  - Other sources (freepik, etc.)
- Parse source-specific metadata formats
- Store metadata in standardized TOML format

#### File Organization
- Group related images into image set folders
- Apply consistent naming and tagging conventions
- Identify and mark original source images

### Logging
- Comprehensive logging to both file and screen
- Graceful error handling throughout the application

## Data Structures

### Imageset TOML file.
```toml
imageset = "[image_set_name]"
source = "[source_type]"  # midjourney, fooocus, freepik, other

[review]
needs = ""

[biz]
good_for = ""
posted_to = ""

[interview]
interview_date = ""
template_used = ""
title = ""
description = ""

# Source-specific metadata sections
[midjourney]
description = "a 35mm photography shot of a deserted beach at sunrise, with footprints leading to the water, soft waves washing ashore, and a few distant sailboats; the color temperature is warm with natural lighting, capturing the peaceful solitude of the early morning --ar 3:4 --v 7 Job ID: 758b8376-b799-4065-ac91-90d109ab15a8"
prompt = "a 35mm photography shot of a deserted beach at sunrise, with footprints leading to the water, soft waves washing ashore, and a few distant sailboats; the color temperature is warm with natural lighting, capturing the peaceful solitude of the early morning --ar 3:4 --v 7"
jobid = "758b8376-b799-4065-ac91-90d109ab15a8"

[fooocus]
Prompt = "a pen and ink children's story graphic novel page | in the style of Kelly Freas"
"Negative Prompt" = "ugly face, deformed hands, watermark, signature"
"Fooocus V2 Expansion" = ""
Styles = "[]"
Performance = "Quality"
Resolution = "(896, 1152)"
"Guidance Scale" = "6"
Sharpness = "6"
"ADM Guidance" = "(1.5, 0.8, 0.3)"
"Base Model" = "hotart_2.safetensors"
"Refiner Model" = "None"
"Refiner Switch" = "0.5"
"CLIP Skip" = "2"
Sampler = "dpmpp_3m_sde_gpu"
Scheduler = "karras"
VAE = "Default (model)"
Seed = "5034843562244127231"
"Metadata Scheme" = "False"
Version = "Fooocus v2.4.3"
"Full raw prompt" = "Positivea pen and ink children's story graphic novel page | in the style of Kelly Freas\nNegativeugly face, deformed hands, watermark, signature"
```

## Error Handling
- Implement graceful error catching throughout the application
- Log errors to both file and console
- Provide user-friendly error messages

## Performance Considerations
- Efficient handling of large image collections
- Optimize file operations for speed and reliability

## Project Structure

```
img_catalog_tui/
├── config/
│   ├── config.toml       # Main application configuration
│   ├── menu.toml         # Menu structure definition
│   └── templates/        # Interview templates
│       └── *.tmpl
│
├── docs/
│   ├── notes.md          # Development notes
│   └── PRD.md            # Product Requirements Document
│
├── img_catalog_tui/      # Main package
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── cli.py            # Command line argument parsing
│   ├── config.py         # Configuration handling
│   ├── logger.py         # Logging setup
│   │
│   ├── ui/               # User interface components
│   │   ├── __init__.py
│   │   ├── menu.py       # Menu system
│   │   └── tui.py        # Terminal UI implementation
│   │
│   ├── core/             # Business logic
│   │   ├── __init__.py
│   │   ├── commands.py   # Command handlers
│   │   ├── folder.py     # Folder operations
│   │   ├── imageset.py   # Image set operations
│   │   └── metadata.py   # Metadata extraction and handling
│   │
│   └── utils/            # Utility functions
│       ├── __init__.py
│       ├── file_utils.py # File operations
│       └── exif.py       # EXIF data handling
│
├── logs/                 # Log files
│
├── tests/                # Unit and integration tests
│   ├── __init__.py
│   ├── test_folder.py
│   └── test_metadata.py
│
├── pyproject.toml        # Project metadata and dependencies
├── README.md             # Project documentation
└── main.py               # Application entry point
```

### Data Organization

For the image collections being managed, the following structure is expected:

```
<input_folder>/
├── <imageset_1>/         # Image set folder
│   ├── <imageset_1>.toml # Metadata file
│   ├── <imageset_1>_orig.png  # Original image
│   ├── <imageset_1>_thumb.png # Thumbnail
│   └── <imageset_1>_v2.png    # Variant
│
├── <imageset_2>/
│   ├── <imageset_2>.toml
│   └── <imageset_2>_orig.png
│
└── _index/               # Generated index files
    ├── index.json        # JSON index of all imagesets
    └── index.html        # HTML gallery view
```

## Deployment

### Executable Creation
- PyInstaller will be used to package the application into a standalone executable
- The executable will include all necessary dependencies and resources
- Target platforms: Windows (primary), with potential for Linux and macOS

#### PyInstaller Configuration
```
pyinstaller --name="img_catalog_tui" ^
            --onefile ^
            --windowed ^
            --icon=resources/icon.ico ^
            --add-data="config;config" ^
            --hidden-import=PIL ^
            --hidden-import=toml ^
            --hidden-import=rich ^
            --hidden-import=textual ^
            main.py
```

#### Distribution Package
The distribution package will include:
- The standalone executable (`img_catalog_tui.exe`)
- A sample configuration file
- Basic documentation (README)
- Sample templates for interviews

### Installation
- No installation required - the application will run as a standalone executable
- Configuration files can be edited directly by users
- Templates can be added to the templates directory

## Future Extensions
- Support for additional image sources
- Alternative interfaces beyond TUI
- Enhanced metadata extraction capabilities
