"""
Terminal UI implementation for the Image Catalog TUI application.
"""

import logging
import os
import sys
from typing import Dict, List, Any, Tuple, Optional, Callable

from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.table import Table
from rich.text import Text

from img_catalog_tui.config import Config
from img_catalog_tui.ui.menu import start_menu


class TUI:
    """
    Terminal UI for the application.
    
    Handles the overall UI flow and status display.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the TUI.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.console = Console()
        
    def display_welcome(self) -> None:
        """
        Display a welcome message.
        """
        self.console.clear()
        
        welcome_text = """
        Welcome to Image Catalog TUI
        
        This application helps you organize and manage your image collections.
        Use the menu to navigate and select options.
        
        Press any key to continue...
        """
        
        panel = Panel(welcome_text.strip(), title="Welcome", border_style="green")
        self.console.print(panel)
        
        # Wait for any key
        input()
        
    def display_status(self, message: str, status_type: str = "info") -> None:
        """
        Display a status message.
        
        Args:
            message: Status message to display
            status_type: Type of status (info, success, error, warning)
        """
        style = {
            "info": "blue",
            "success": "green",
            "error": "red",
            "warning": "yellow"
        }.get(status_type, "white")
        
        self.console.print(f"[{style}]{message}[/{style}]")
        
    def display_error(self, message: str) -> None:
        """
        Display an error message.
        
        Args:
            message: Error message to display
        """
        self.display_status(f"Error: {message}", "error")
        
    def display_success(self, message: str) -> None:
        """
        Display a success message.
        
        Args:
            message: Success message to display
        """
        self.display_status(f"Success: {message}", "success")
        
    def display_working(self, message: str) -> Status:
        """
        Display a working status indicator.
        
        Args:
            message: Message to display
            
        Returns:
            Status object that can be updated or stopped
        """
        return self.console.status(f"[bold blue]{message}...", spinner="dots")
        
    def clear(self) -> None:
        """
        Clear the screen.
        """
        self.console.clear()
        
    def prompt_for_folder(self) -> str:
        """
        Prompt the user for an input folder if not provided via command line.
        
        Returns:
            Path to the input folder
        """
        self.console.print("Input folder not specified via command line.", style="yellow")
        
        while True:
            self.console.print("Enter path to input folder: ", end="", style="bold yellow")
            folder = input().strip()
            
            if not folder:
                self.console.print("Folder path cannot be empty.", style="red")
                continue
                
            if not os.path.exists(folder):
                self.console.print(f"Folder does not exist: {folder}", style="red")
                continue
                
            if not os.path.isdir(folder):
                self.console.print(f"Not a directory: {folder}", style="red")
                continue
                
            return folder


def run_tui(config: Config, input_folder: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Run the TUI application.
    
    Args:
        config: Application configuration
        input_folder: Path to input folder (if provided via command line)
        
    Returns:
        Tuple containing (command, arguments)
    """
    tui = TUI(config)
    
    # Clear the screen for a clean start
    tui.clear()
    
    # Start menu system directly
    command, args = start_menu(config)
    
    # Add input folder to args if not already present
    if command != 'x' and 'folder_name' not in args:
        args['folder_name'] = input_folder
        
    return command, args
