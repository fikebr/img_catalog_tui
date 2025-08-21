"""
Terminal UI implementation for the Image Catalog TUI application.
"""

import os
from typing import Dict, Any, Tuple, Optional

from rich.console import Console
from rich.status import Status

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Header, Footer

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
        class WelcomeScreen(Screen):
            """
            Welcome screen for the application.
            """
            def compose(self) -> ComposeResult:
                """Create and yield widgets for the screen."""
                yield Header(show_clock=True)
                yield Container(
                    Label("Welcome to Image Catalog TUI"),
                    Label(""),
                    Label("This application helps you organize and manage your image collections."),
                    Label("Use the menu to navigate and select options."),
                    Label(""),
                    Button("Continue", variant="primary", id="continue_btn"),
                    classes="welcome_container",
                )
                yield Footer()

            @on(Button.Pressed, "#continue_btn")
            def on_continue(self, event) -> None:
                """Handle the continue button press."""
                self.app.exit()

        class WelcomeApp(App):
            """
            Simple app to display welcome message.
            """
            def on_mount(self):
                """Mount the welcome screen."""
                self.push_screen(WelcomeScreen())

        # Run the welcome app
        app = WelcomeApp()
        app.run()
        
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
        class FolderInputScreen(Screen):
            """
            Screen for getting a folder path from the user.
            """
            def __init__(self, callback=None, **kwargs):
                super().__init__(**kwargs)
                self.callback = callback
                self.result = None
                self.error_message = ""

            def compose(self) -> ComposeResult:
                """Create and yield widgets for the screen."""
                yield Header(show_clock=True)
                yield Container(
                    Label("Input folder not specified via command line."),
                    Label("Enter path to input folder:"),
                    Input(placeholder="Type folder path here", id="folder_input"),
                    Label(id="error_message", classes="error"),
                    Button("Submit", variant="primary", id="submit_btn"),
                    classes="input_container",
                )
                yield Footer()

            def on_mount(self) -> None:
                """Focus the input widget when the screen is mounted."""
                self.query_one(Input).focus()

            @on(Input.Submitted)
            @on(Button.Pressed, "#submit_btn")
            def on_submit(self, event) -> None:
                """Handle the submit event."""
                folder = self.query_one("#folder_input").value.strip()
                
                if not folder:
                    self.query_one("#error_message").update("Folder path cannot be empty.")
                    return
                    
                if not os.path.exists(folder):
                    self.query_one("#error_message").update(f"Folder does not exist: {folder}")
                    return
                    
                if not os.path.isdir(folder):
                    self.query_one("#error_message").update(f"Not a directory: {folder}")
                    return
                
                self.result = folder
                self.app.exit()

        class FolderInputApp(App):
            """
            Simple app to get folder input.
            """
            def __init__(self):
                super().__init__()
                self.result = None
                
            def on_mount(self):
                """Mount the folder input screen."""
                self.screen = FolderInputScreen()
                self.push_screen(self.screen)
                
            def on_screen_resume(self) -> None:
                """Handle screen resume event."""
                if hasattr(self.screen, 'result') and self.screen.result:
                    self.result = self.screen.result
        
        # Run the app to get folder input
        app = FolderInputApp()
        app.run()
        
        return app.result


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
