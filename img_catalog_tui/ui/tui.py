import os
from typing import Dict, Any, Tuple, Optional

from rich.console import Console
from rich.panel import Panel
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Input, Label, Header, Footer, Static

from img_catalog_tui.config import Config
from img_catalog_tui.ui.menu import start_menu


class WelcomeApp(App):
    CSS = """
    .panel { background: $boost; border: round $panel-darken-2; padding: 2 3; }
    #wrap { height: 1fr; content-align: center middle; }
    Header, Footer { background: $panel; }
    .title { text-style: bold; }
    .muted { color: $muted; }
    """

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="wrap"):
            with Vertical(classes="panel"):
                yield Static("Image Catalog TUI", classes="title")
                yield Static(Panel(self.message))
                yield Static("Press Enter or click Continue", classes="muted")
                yield Button("Continue", variant="primary", id="continue_btn")
        yield Footer()

    @on(Button.Pressed, "#continue_btn")
    def _continue(self) -> None:
        self.exit()

    def on_key(self, event) -> None:  # quick keyboard submit
        if event.key == "enter":
            self.exit()


class TUI:
    """Terminal UI wrapper providing status helpers and startup flow."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console()

    def display_welcome(self) -> None:
        msg = (
            "This application helps you organize and manage your image collections.\n"
            "Use the left sidebar to choose a section, then pick an option on the right."
        )
        app = WelcomeApp(msg)
        app.run()

    def display_status(self, message: str, status_type: str = "info") -> None:
        style = {
            "info": "blue",
            "success": "green",
            "error": "red",
            "warning": "yellow",
        }.get(status_type, "white")
        self.console.print(f"[{style}]{message}[/{style}]")

    def display_error(self, message: str) -> None:
        self.display_status(f"Error: {message}", "error")

    def display_success(self, message: str) -> None:
        self.display_status(f"Success: {message}", "success")

    def display_working(self, message: str):
        return self.console.status(f"[bold blue]{message}...", spinner="dots")

    def clear(self) -> None:
        self.console.clear()

    def prompt_for_folder(self) -> str:
        # Keeping your existing logic; this is already decent UX.
        class FolderInputApp(App):
            CSS = """
            .panel { background: $boost; border: round $panel-darken-2; padding: 2 3; }
            Header, Footer { background: $panel; }
            #wrap { height: 1fr; content-align: center middle; }
            .error { color: $error; }
            """

            def __init__(self):
                super().__init__()
                self.result: Optional[str] = None

            def compose(self) -> ComposeResult:
                yield Header(show_clock=True)
                with Container(id="wrap"):
                    with Vertical(classes="panel"):
                        yield Label("Input folder not specified via command line.")
                        yield Label("Enter path to input folder:")
                        yield Input(placeholder="Type folder path here", id="folder_input")
                        yield Label("", id="error_message", classes="error")
                        yield Button("Submit", variant="primary", id="submit_btn")
                yield Footer()

            def on_mount(self) -> None:
                self.query_one(Input).focus()

            @on(Input.Submitted)
            @on(Button.Pressed, "#submit_btn")
            def _submit(self) -> None:
                import os
                folder = self.query_one("#folder_input", Input).value.strip()
                err = self.query_one("#error_message", Label)
                if not folder:
                    err.update("Folder path cannot be empty.")
                    return
                if not os.path.exists(folder):
                    err.update(f"Folder does not exist: {folder}")
                    return
                if not os.path.isdir(folder):
                    err.update(f"Not a directory: {folder}")
                    return
                self.result = folder
                self.exit()

        app = FolderInputApp()
        app.run()
        return app.result


def run_tui(config: Config, input_folder: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    tui = TUI(config)
    tui.clear()
    # Optional nice welcome—call if you want it
    # tui.display_welcome()

    command, args = start_menu(config)

    if command != "x" and "folder_name" not in args:
        args["folder_name"] = input_folder

    return command, args
