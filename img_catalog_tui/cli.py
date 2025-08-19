"""
Command-line argument parsing for the Image Catalog TUI application.
"""

import argparse
import logging
import os
from typing import Dict, NamedTuple


class Args(NamedTuple):
    """
    Parsed command-line arguments.
    """
    input_folder: str = None
    config_file: str = "config/config.toml"


def parse_args() -> Args:
    """
    Parse command-line arguments.
    
    Returns:
        Args: Parsed command-line arguments
    
    Raises:
        SystemExit: If required arguments are missing or invalid
    """
    parser = argparse.ArgumentParser(
        description="Image Catalog TUI - A terminal user interface for organizing and managing image collections"
    )
    
    parser.add_argument(
        "--input_folder",
        type=str,
        required=False,
        help="Path to the folder containing images to process (optional, can be set in TUI)"
    )
    
    parser.add_argument(
        "--config_file",
        type=str,
        default="config/config.toml",
        help="Path to the configuration file (default: config/config.toml)"
    )
    
    args = parser.parse_args()
    
    # Validate input folder if provided
    if args.input_folder and not os.path.exists(args.input_folder):
        logging.error(f"Input folder does not exist: {args.input_folder}")
        parser.error(f"Input folder does not exist: {args.input_folder}")
    
    # Validate config file
    if not os.path.exists(args.config_file):
        logging.warning(f"Config file does not exist: {args.config_file}")
        logging.warning("Using default configuration")
    
    return Args(
        input_folder=args.input_folder,
        config_file=args.config_file
    )
