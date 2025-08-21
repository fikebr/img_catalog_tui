"""
Configuration handling for the Image Catalog TUI application.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import toml


class Config:
    """
    Configuration manager for the application.
    
    Handles loading and accessing configuration from TOML files.
    """
    
    def __init__(self, config_file: str = "./config/config.toml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the main configuration file
        """
        self.config_file = config_file
        self.config_data: Dict[str, Any] = {}
        self.menu_config: Dict[str, Any] = {}
        self.config_dir = os.path.dirname(os.path.abspath(config_file))
        
    def load(self) -> bool:
        """
        Load the configuration from the specified file.
        
        Returns:
            bool: True if configuration was loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.config_file):
                logging.error(f"Configuration file not found: {self.config_file}")
                return False
                
            logging.info(f"Loading configuration from {self.config_file}")
            self.config_data = toml.load(self.config_file)
            
            # Load menu configuration
            paths_config = self.get("paths", {})
            menu_config_path = paths_config.get("menu_config", "./config/menu.toml")
            self.load_menu_config(menu_config_path)
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading configuration: {e}", exc_info=True)
            return False
    
    def load_menu_config(self, menu_config_path: str) -> bool:
        """
        Load the menu configuration from the specified file.
        
        Args:
            menu_config_path: Path to the menu configuration file
            
        Returns:
            bool: True if menu configuration was loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(menu_config_path):
                logging.error(f"Menu configuration file not found: {menu_config_path}")
                return False
                
            logging.info(f"Loading menu configuration from {menu_config_path}")
            self.menu_config = toml.load(menu_config_path)
            
            # Debug: Print loaded menu configuration
            logging.debug("Loaded menu config: %s", self.menu_config)
            
            # Check if we have the expected sections
            sections = self.get_menu_sections()
            logging.debug("Found menu sections: %s", sections)
            
            # Check subsections for each section
            for section in sections:
                subsections = self.get_menu_subsections(section)
                logging.debug("Section %s has subsections: %s", section, subsections)
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading menu configuration: {e}", exc_info=True)
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value by its dot-notation path.
        
        Args:
            key_path: Dot-notation path to the configuration value (e.g., "logging.level")
            default: Default value to return if the key doesn't exist
            
        Returns:
            The configuration value, or the default if not found
        """
        parts = key_path.split(".")
        current = self.config_data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
                
        return current
    
    def get_file_tags(self) -> List[str]:
        """
        Get the list of file tags from the configuration.
        
        Returns:
            List of file tags
        """
        return self.get("file_tags", ["orig", "thumb", "v2", "v3", "v4", "v5", "up2", "up3", "up4", "up6"])
    
    def get_menu_item(self, section: str, subsection: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a menu item from the menu configuration.
        
        Args:
            section: The main section of the menu (e.g., "folder")
            subsection: The subsection of the menu (e.g., "scan")
            
        Returns:
            Dictionary containing the menu item configuration
        """
        # Check if the section exists
        if section not in self.menu_config:
            logging.warning("Section %s not found in menu config", section)
            return {}
            
        # If no subsection, return the section data
        if subsection is None:
            section_data = self.menu_config[section]
            # Filter out nested dictionaries (subsections)
            return {k: v for k, v in section_data.items() if not isinstance(v, dict)}
            
        # Get the subsection data
        section_data = self.menu_config.get(section, {})
        if subsection in section_data:
            return section_data[subsection]
            
        logging.warning("Subsection %s not found in section %s", subsection, section)
        return {}
    
    def get_menu_sections(self) -> List[str]:
        """
        Get the list of top-level menu sections.
        
        Returns:
            List of section names
        """
        # Debug the menu config
        logging.debug("Menu config keys: %s", list(self.menu_config.keys()))
        
        # In TOML, nested tables are actually nested dictionaries
        # So we need to get the top-level keys that are dictionaries
        sections = []
        for key, value in self.menu_config.items():
            if isinstance(value, dict):
                sections.append(key)
                
        logging.debug("Found sections: %s", sections)
        return sections
    
    def get_menu_subsections(self, section: str) -> List[str]:
        """
        Get the subsections for a menu section.
        
        Args:
            section: The section to get subsections for
            
        Returns:
            List of subsection names
        """
        logging.debug("Getting subsections for section: %s", section)
        
        # Check if the section exists in the menu config
        if section not in self.menu_config:
            logging.warning("Section %s not found in menu config", section)
            return []
            
        # In TOML, nested tables become nested dictionaries
        # So we need to get the keys of the nested dictionary
        section_data = self.menu_config.get(section, {})
        logging.debug("Section data: %s", section_data)
        
        # Get all keys that are dictionaries (subsections)
        subsections = []
        for key, value in section_data.items():
            if isinstance(value, dict):
                subsections.append(key)
                
        logging.debug("Found subsections: %s", subsections)
        return subsections
