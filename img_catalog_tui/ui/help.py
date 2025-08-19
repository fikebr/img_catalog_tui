"""
Help system for the Image Catalog TUI application.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from img_catalog_tui.config import Config


def display_help(console: Console, section: str = None, subsection: str = None, config: Config = None) -> None:
    """
    Display help information.
    
    Args:
        console: Rich console for output
        section: Current menu section (if any)
        subsection: Current menu subsection (if any)
        config: Application configuration
    """
    console.clear()
    
    if section and subsection and config:
        # Display help for a specific command
        display_command_help(console, section, subsection, config)
    elif section and config:
        # Display help for a section
        display_section_help(console, section, config)
    else:
        # Display general help
        display_general_help(console)
        
    # Wait for any key
    console.print("Press Enter to return...", style="italic")
    input()


def display_general_help(console: Console) -> None:
    """
    Display general help information.
    
    Args:
        console: Rich console for output
    """
    help_text = """
    Image Catalog TUI Help
    
    Navigation Keys:
    - x: Exit application
    - u: Go up a level in the menu
    - h: Display this help screen
    
    Menu Navigation:
    - Use the letter keys shown to select menu options
    - Follow the prompts to provide input when requested
    
    General Commands:
    - Folder operations: Scan and index folders of images
    - Image set operations: Work with individual image sets
    """
    
    panel = Panel(help_text.strip(), title="General Help", border_style="green")
    console.print(panel)


def display_section_help(console: Console, section: str, config: Config) -> None:
    """
    Display help for a specific section.
    
    Args:
        console: Rich console for output
        section: Section to display help for
        config: Application configuration
    """
    section_data = config.get_menu_item(section)
    description = section_data.get('description', section.capitalize())
    
    # Get subsections
    subsections = config.get_menu_subsections(section)
    
    # Create a table for the subsections
    table = Table(title=f"{description} Commands", show_header=True)
    table.add_column("Command", style="bold cyan")
    table.add_column("Description")
    
    # Add subsections to the table
    for subsection in subsections:
        subsection_data = config.get_menu_item(section, subsection)
        subsection_desc = subsection_data.get('description', subsection.capitalize())
        table.add_row(subsection, subsection_desc)
        
    # Display the table in a panel
    panel = Panel(table, title=f"{section.capitalize()} Help", border_style="blue")
    console.print(panel)


def display_command_help(console: Console, section: str, subsection: str, config: Config) -> None:
    """
    Display help for a specific command.
    
    Args:
        console: Rich console for output
        section: Section containing the command
        subsection: Subsection/command to display help for
        config: Application configuration
    """
    subsection_data = config.get_menu_item(section, subsection)
    description = subsection_data.get('description', subsection.capitalize())
    command = subsection_data.get('command', '')
    questions = subsection_data.get('questions', [])
    
    # Create a table for the command parameters
    table = Table(title=f"{description} Parameters", show_header=True)
    table.add_column("Parameter", style="bold cyan")
    table.add_column("Description")
    
    # Add parameters to the table
    for question in questions:
        parts = question.split('|')
        if len(parts) == 2:
            param_name, prompt = parts
            table.add_row(param_name, prompt)
            
    # Display the table in a panel
    panel = Panel(table, title=f"{subsection.capitalize()} Help", border_style="blue")
    console.print(panel)
