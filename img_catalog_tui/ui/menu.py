"""
Menu system for the Image Catalog TUI application.
"""

import logging
from typing import Dict, List, Any, Tuple

from rich.console import Console

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Header, Footer

from img_catalog_tui.config import Config


class MenuApp(App):
    """
    Textual app for the menu system.
    """
    CSS = """
    .menu-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    .menu-title {
        text-align: center;
        margin-bottom: 1;
    }
    
    .menu-option {
        margin-bottom: 1;
    }
    
    .menu-option-key {
        color: cyan;
        text-style: bold;
    }
    
    .menu-input {
        margin-top: 1;
        border: solid yellow;
        padding: 1;
    }
    
    .error {
        color: red;
    }
    
    #input_container {
        margin-top: 1;
    }
    
    .question_container {
        width: 100%;
        padding: 1;
    }
    
    .question_item {
        margin-bottom: 1;
        padding: 1;
        border: solid blue;
    }
    """
    
    def __init__(self, config: Config):
        """
        Initialize the menu app.
        
        Args:
            config: Application configuration
        """
        super().__init__()
        self.config = config
        self.current_section = None
        self.menu_stack = []
        self.command = None
        self.args = {}
        self.valid_choices = []
        
    def compose(self) -> ComposeResult:
        """Create and yield widgets for the app."""
        yield Header(show_clock=True)
        yield Container(id="menu_container")
        yield Container(
            Label("Enter your choice:", id="input_label"),
            Input(placeholder="Type your choice here", id="choice_input"),
            Label(id="error_message", classes="error"),
            id="input_container",
            classes="menu-input"
        )
        yield Footer()
        
    def on_mount(self) -> None:
        """Handle the mount event."""
        # Start with the main menu
        self.display_main_menu()
        self.query_one("#choice_input").focus()
        
    def display_main_menu(self) -> None:
        """Display the main menu."""
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
        
        # Update valid choices
        self.valid_choices = list(options.keys())
        
        # Update the menu container
        self._update_menu_container("Main Menu", options, option_keys)
        
    def display_section_menu(self) -> None:
        """Display a section menu."""
        if not self.current_section:
            self.display_main_menu()
            return
            
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
        
        # Update valid choices
        self.valid_choices = list(options.keys())
        
        # Update the menu container
        self._update_menu_container(f"{self.current_section.capitalize()} Menu", options, option_keys)
        
    def _update_menu_container(self, title: str, options: Dict[str, str], option_keys: Dict[str, str] = None) -> None:
        """
        Update the menu container with the given options.
        
        Args:
            title: Menu title
            options: Dictionary mapping option keys to descriptions
            option_keys: Dictionary mapping keys to section/subsection names
        """
        # Clear the container
        menu_container = self.query_one("#menu_container")
        menu_container.remove_children()
        
        # Create all widgets first
        widgets = []
        
        # Add title
        widgets.append(Label(title, classes="menu-title"))
        
        # Separate regular options from hardcoded options
        regular_options = {}
        hardcoded_options = {}
        
        for key, description in options.items():
            if key in ['x', 'u', 'h']:
                hardcoded_options[key] = description
            else:
                regular_options[key] = description
        
        # Add regular options
        for key, description in regular_options.items():
            # If we have option_keys, format with menu name
            if option_keys and key in option_keys:
                menu_name = option_keys[key].upper()
                widgets.append(Label(f"{key}: {menu_name}: {description}", classes="menu-option"))
            else:
                # Fallback if no option_keys provided
                widgets.append(Label(f"{key}: {description}", classes="menu-option"))
        
        # Create footer text with hardcoded options
        footer_items = []
        if 'x' in hardcoded_options:
            footer_items.append("[x] Exit")
        if 'u' in hardcoded_options:
            footer_items.append("[u] Up")
        if 'h' in hardcoded_options:
            footer_items.append("[h] Help")
            
        # Update the footer
        footer = self.query_one(Footer)
        # Join the items with separators
        footer_text = " ".join(footer_items)
        # Set the footer text directly
        footer.styles.content = footer_text
        
        # Mount all widgets at once
        menu_container.mount(*widgets)
        
    @on(Input.Submitted, "#choice_input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        choice = self.query_one("#choice_input").value.lower()
        self.query_one("#choice_input").value = ""
        
        if choice not in self.valid_choices:
            self.query_one("#error_message").update(f"Invalid choice. Please enter one of: {', '.join(self.valid_choices)}")
            return
            
        self.query_one("#error_message").update("")
        self.handle_choice(choice)
        
    def handle_choice(self, choice: str) -> None:
        """
        Handle a menu choice.
        
        Args:
            choice: The selected menu option
        """
        if choice == 'x':
            self.command = 'x'
            self.args = {}
            self.exit()
            return
            
        if self.current_section is None:
            # Main menu
            if choice == 'h':
                self._display_help()
                return
                
            # Get the selected section
            sections = self.config.get_menu_sections()
            for i, section in enumerate(sections):
                key = chr(97 + i)
                if key in ['x', 'u', 'h']:
                    key = chr(97 + i + 3)
                    
                if key == choice:
                    self.current_section = section
                    self.menu_stack.append(('main', None))
                    self.display_section_menu()
                    return
        else:
            # Section menu
            if choice == 'h':
                self._display_help()
                return
                
            if choice == 'u':
                prev_menu, _ = self.menu_stack.pop()
                if prev_menu == 'main':
                    self.current_section = None
                    self.display_main_menu()
                else:
                    self.current_section = prev_menu
                    self.display_section_menu()
                return
                
            # Get the selected subsection
            subsections = self.config.get_menu_subsections(self.current_section)
            for i, subsection in enumerate(subsections):
                key = chr(97 + i)
                if key in ['x', 'u', 'h']:
                    key = chr(97 + i + 3)
                    
                if key == choice:
                    # Get command and questions
                    subsection_data = self.config.get_menu_item(self.current_section, subsection)
                    command = subsection_data.get('command', '')
                    questions = subsection_data.get('questions', [])
                    
                    if questions:
                        # Show question input screen
                        self.show_question_screen(command, questions)
                    else:
                        # No questions, return command directly
                        self.command = command
                        self.args = {}
                        self.exit()
                    return
                    
    def show_question_screen(self, command: str, questions: List[str]) -> None:
        """
        Show a screen with all questions for a command at once.
        
        Args:
            command: The command to execute
            questions: List of questions to ask
        """
        class QuestionScreen(Screen):
            """Screen for asking all questions at once."""
            
            def __init__(self, command: str, questions: List[str], app):
                super().__init__()
                self.command = command
                self.questions = questions
                self.parent_app = app
                self.param_names = []
                
            def compose(self) -> ComposeResult:
                """Create and yield widgets for the screen."""
                yield Header(show_clock=True)
                
                # Create the main container with command label
                yield Container(
                    Label(f"Command: {self.command}", id="command_label"),
                    *self._create_question_widgets(),
                    Button("Submit All", variant="primary", id="submit_all_btn"),
                    classes="question_container",
                )
                
                yield Footer()
                
            def _create_question_widgets(self) -> List:
                """Create widgets for all questions."""
                widgets = []
                
                # Process all questions
                for i, question in enumerate(self.questions):
                    parts = question.split('|')
                    if len(parts) == 2:
                        param_name, prompt = parts
                        self.param_names.append(param_name)
                        
                        # Create a container for this question with its widgets
                        widgets.append(
                            Container(
                                Label(prompt, id=f"question_label_{i}"),
                                Input(id=f"question_input_{i}"),
                                classes="question_item"
                            )
                        )
                
                return widgets
                
            def on_mount(self) -> None:
                """Handle mount event."""
                # Focus the first input field
                if self.questions:
                    self.query_one("#question_input_0").focus()
                
            @on(Button.Pressed, "#submit_all_btn")
            def on_submit_all(self, event) -> None:
                """Handle submit all button press."""
                args = {}
                
                # Collect all input values
                for i, param_name in enumerate(self.param_names):
                    input_widget = self.query_one(f"#question_input_{i}")
                    args[param_name] = input_widget.value
                
                # Return the command and args
                self.parent_app.command = self.command
                self.parent_app.args = args
                self.parent_app.exit()
            
            # Also allow submitting with Enter key on the last input field
            @on(Input.Submitted)
            def on_input_submitted(self, event: Input.Submitted) -> None:
                """Handle input submission."""
                # If it's the last input, submit the form
                if event.input.id == f"question_input_{len(self.questions)-1}":
                    self.on_submit_all(event)
                # Otherwise, focus the next input
                else:
                    for i in range(len(self.questions)-1):
                        if event.input.id == f"question_input_{i}":
                            self.query_one(f"#question_input_{i+1}").focus()
                            break
                
        self.push_screen(QuestionScreen(command, questions, self))
        
    def _display_help(self) -> None:
        """Display help information."""
        from img_catalog_tui.ui.help import display_help
        # Create a console for the help display
        console = Console()
        display_help(console, self.current_section, None, self.config)
        # After displaying help, refocus the input
        self.query_one("#choice_input").focus()





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
    
    # Create and run the menu app directly
    app = MenuApp(config)
    app.run()
    
    # Return the result
    return app.command or 'x', app.args or {}
