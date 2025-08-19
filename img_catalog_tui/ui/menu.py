"""
Menu system for the Image Catalog TUI application.
"""

import logging
import os
import sys
from typing import Dict, List, Any, Tuple, Optional, Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from img_catalog_tui.config import Config


class Menu:
    """
    Menu system for the TUI application.
    
    Handles displaying menus, getting user input, and navigating between menu levels.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the menu system.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.console = Console()
        self.current_section = None
        self.menu_stack = []
        self.input_handler = InputHandler()
        
    def display_main_menu(self) -> Tuple[str, Dict[str, Any]]:
        """
        Display the main menu and get user selection.
        
        Returns:
            Tuple containing (command, arguments)
        """
        self.current_section = None
        self.menu_stack = []
        
        sections = self.config.get_menu_sections()
        
        # Create menu options
        options = {}
        option_keys = {}
        
        # Add section options
        for i, section in enumerate(sections):
            # Use letters a-z (skipping x, u, h)
            key = chr(97 + i)  # ASCII 'a' is 97
            if key in ['x', 'u', 'h']:
                key = chr(97 + i + 3)  # Skip x, u, h
                
            section_data = self.config.get_menu_item(section)
            description = section_data.get('description', section.capitalize())
            options[key] = f"{description}"
            option_keys[key] = section
        
        # Add special options
        options['x'] = "Exit application"
        options['h'] = "Help"
        
        # Display menu
        self._display_menu("Main Menu", options)
        
        # Get user input
        choice = self.input_handler.get_choice(list(options.keys()))
        
        if choice == 'x':
            return 'x', {}
            
        if choice == 'h':
            self._display_help()
            return self.display_main_menu()
            
        # Navigate to section
        self.current_section = option_keys[choice]
        self.menu_stack.append(('main', None))
        return self.display_section_menu()
        
    def display_section_menu(self) -> Tuple[str, Dict[str, Any]]:
        """
        Display a section menu and get user selection.
        
        Returns:
            Tuple containing (command, arguments)
        """
        if not self.current_section:
            return self.display_main_menu()
            
        subsections = self.config.get_menu_subsections(self.current_section)
        
        # Create menu options
        options = {}
        option_keys = {}
        
        # Add subsection options
        for i, subsection in enumerate(subsections):
            # Use letters a-z (skipping x, u, h)
            key = chr(97 + i)  # ASCII 'a' is 97
            if key in ['x', 'u', 'h']:
                key = chr(97 + i + 3)  # Skip x, u, h
                
            subsection_data = self.config.get_menu_item(self.current_section, subsection)
            description = subsection_data.get('description', subsection.capitalize())
            options[key] = f"{description}"
            option_keys[key] = subsection
        
        # Add special options
        options['x'] = "Exit application"
        options['u'] = "Go up a level"
        options['h'] = "Help"
        
        # Display menu
        self._display_menu(f"{self.current_section.capitalize()} Menu", options)
        
        # Get user input
        choice = self.input_handler.get_choice(list(options.keys()))
        
        if choice == 'x':
            return 'x', {}
            
        if choice == 'u':
            prev_menu, _ = self.menu_stack.pop()
            if prev_menu == 'main':
                self.current_section = None
                return self.display_main_menu()
            else:
                self.current_section = prev_menu
                return self.display_section_menu()
                
        if choice == 'h':
            self._display_help()
            return self.display_section_menu()
            
        # Get command and questions
        subsection = option_keys[choice]
        logging.debug("Selected subsection: %s", subsection)
        
        subsection_data = self.config.get_menu_item(self.current_section, subsection)
        logging.debug("Subsection data: %s", subsection_data)
        
        command = subsection_data.get('command', '')
        questions = subsection_data.get('questions', [])
        logging.debug("Command: %s, Questions: %s", command, questions)
        
        # Ask questions
        args = {}
        for question in questions:
            parts = question.split('|')
            if len(parts) == 2:
                param_name, prompt = parts
                value = self.input_handler.get_input(prompt)
                args[param_name] = value
                
        return command, args
        
    def _display_menu(self, title: str, options: Dict[str, str]) -> None:
        """
        Display a menu with the given title and options.
        
        Args:
            title: Menu title
            options: Dictionary mapping option keys to descriptions
        """
        self.console.clear()
        
        # Create a table for the menu
        table = Table(title=title, show_header=False, box=None)
        table.add_column("Key", style="bold cyan")
        table.add_column("Description")
        
        # Add options to the table
        for key, description in options.items():
            table.add_row(key, description)
            
        # Display the table in a panel
        panel = Panel(table, title="Image Catalog TUI", border_style="blue")
        self.console.print(panel)
        
    def _display_help(self) -> None:
        """
        Display help information.
        """
        from img_catalog_tui.ui.help import display_help
        display_help(self.console, self.current_section, None, self.config)
        

class InputHandler:
    """
    Handles user input for the TUI application.
    """
    
    def __init__(self):
        """
        Initialize the input handler.
        """
        self.console = Console()
        
    def get_choice(self, valid_choices: List[str]) -> str:
        """
        Get a single character choice from the user.
        
        Args:
            valid_choices: List of valid character choices
            
        Returns:
            The user's choice
        """
        while True:
            self.console.print("Enter your choice: ", end="", style="bold yellow")
            choice = input().lower()
            
            if choice in valid_choices:
                return choice
                
            self.console.print(f"Invalid choice. Please enter one of: {', '.join(valid_choices)}", style="bold red")
            
    def get_input(self, prompt: str) -> str:
        """
        Get input from the user with the given prompt.
        
        Args:
            prompt: Prompt to display to the user
            
        Returns:
            The user's input
        """
        self.console.print(f"{prompt}: ", end="", style="bold yellow")
        return input()
        
    def get_any_key(self) -> None:
        """
        Wait for the user to press any key.
        """
        self.console.print("Press any key to continue...", style="italic")
        input()


def start_menu(config: Config) -> Tuple[str, Dict[str, Any]]:
    """
    Start the menu system.
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple containing (command, arguments)
    """
    # Debug: Print menu configuration
    logging.debug("Menu sections: %s", config.get_menu_sections())
    for section in config.get_menu_sections():
        logging.debug("Section %s subsections: %s", section, config.get_menu_subsections(section))
    
    menu = Menu(config)
    return menu.display_main_menu()
