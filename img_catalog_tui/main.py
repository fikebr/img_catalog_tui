"""
Main entry point for the Image Catalog TUI application.
"""

import logging
import sys
from typing import Dict, Any, Tuple, Optional

from img_catalog_tui.cli import parse_args
from img_catalog_tui.config import Config
from img_catalog_tui.core.commands import handle_command
from img_catalog_tui.logger import setup_logging


def start_menu(config: Config, input_folder: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Start the menu system.
    
    Args:
        config: Application configuration
        input_folder: Path to input folder (if provided via command line)
        
    Returns:
        Tuple containing (command, arguments)
    """
    from img_catalog_tui.ui.tui import run_tui
    return run_tui(config, input_folder)


def main():
    """
    Main entry point for the application.
    
    Initializes logging, loads configuration, and starts the application.
    """
    # Set up logging
    logger = setup_logging()
    logging.getLogger().setLevel(logging.DEBUG)  # Set to DEBUG level for troubleshooting
    
    try:
        logging.info("Starting Image Catalog TUI")
        
        # Parse command line arguments
        args = parse_args()
        if args.input_folder:
            logging.info(f"Input folder from command line: {args.input_folder}")
        logging.info(f"Config file: {args.config_file}")
        
        # Load configuration
        config = Config(args.config_file)
        if not config.load():
            logging.error("Failed to load configuration")
            return 1
        
        logging.info("Configuration loaded successfully")
        logging.info(f"File tags: {config.get_file_tags()}")
        
        # Display available menu sections
        menu_sections = config.get_menu_sections()
        logging.info(f"Available menu sections: {', '.join(menu_sections)}")
        
        for section in menu_sections:
            subsections = config.get_menu_subsections(section)
            logging.info(f"Menu section '{section}' has subsections: {', '.join(subsections)}")
        
        logging.info("Application initialized successfully")
        
        # Main application loop
        while True:
            command, c_args = start_menu(config, args.input_folder)
            
            if command == "x":
                logging.info("Exiting application")
                break
                
            if not handle_command(command, c_args, config):
                logging.info("Command handler requested exit")
                break
        
    except Exception as e:
        logging.error(f"Error during application execution: {e}", exc_info=True)
        return 1
    
    logging.debug("Application terminated normally")
    return 0


if __name__ == "__main__":
    sys.exit(main())
