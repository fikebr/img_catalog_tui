"""
Command handlers for the Image Catalog TUI application.
"""

import logging
from typing import Dict, Any, Callable

from img_catalog_tui.config import Config
from img_catalog_tui.core.folder import folder_scan
from img_catalog_tui.core.folder_index import folder_index
from img_catalog_tui.core.imageset_commands import generate_html_report, process_interview


# Command handler type
CommandHandler = Callable[[Dict[str, Any], Config], bool]


# Command registry
COMMANDS: Dict[str, CommandHandler] = {}


def register_command(name: str) -> Callable[[CommandHandler], CommandHandler]:
    """
    Decorator to register a command handler.
    
    Args:
        name: Name of the command
        
    Returns:
        Decorator function
    """
    def decorator(func: CommandHandler) -> CommandHandler:
        COMMANDS[name] = func
        return func
    return decorator


def handle_command(command: str, args: Dict[str, Any], config: Config) -> bool:
    """
    Handle a command.
    
    Args:
        command: Name of the command
        args: Command arguments
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    if command == "x":
        logging.info("Exit command received")
        return False
        
    if command not in COMMANDS:
        logging.error(f"Unknown command: {command}")
        return True
        
    try:
        handler = COMMANDS[command]
        result = handler(args, config)
        
        if result:
            logging.info(f"Command {command} executed successfully")
        else:
            logging.error(f"Command {command} failed")
            
        return True
        
    except Exception as e:
        logging.error(f"Error handling command {command}: {e}", exc_info=True)
        return True


@register_command("folder_scan")
def handle_folder_scan(args: Dict[str, Any], config: Config) -> bool:
    """
    Handle folder scan command.
    
    Args:
        args: Command arguments
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    return folder_scan(args, config)


@register_command("folder_index")
def handle_folder_index(args: Dict[str, Any], config: Config) -> bool:
    """
    Handle folder index command.
    
    Args:
        args: Command arguments
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    return folder_index(args, config)


@register_command("imageset_html")
def handle_imageset_html(args: Dict[str, Any], config: Config) -> bool:
    """
    Handle imageset HTML report command.
    
    Args:
        args: Command arguments
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    folder_name = args.get("folder_name")
    imageset = args.get("imageset")
    
    if not folder_name or not imageset:
        logging.error("Missing required arguments for imageset_html command")
        return False
        
    return generate_html_report(folder_name, imageset, config)


@register_command("imageset_interview")
def handle_imageset_interview(args: Dict[str, Any], config: Config) -> bool:
    """
    Handle imageset interview command.
    
    Args:
        args: Command arguments
        config: Application configuration
        
    Returns:
        True if successful, False otherwise
    """
    folder_name = args.get("folder_name")
    imageset = args.get("imageset")
    interview_template = args.get("interview_template")
    
    if not folder_name or not imageset or not interview_template:
        logging.error("Missing required arguments for imageset_interview command")
        return False
        
    return process_interview(folder_name, imageset, interview_template, config)
