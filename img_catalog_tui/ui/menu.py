from typing import Dict, List, Any, Tuple, Optional

from rich.console import Console
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.dom import NoMatches
from textual.screen import Screen
from textual.widgets import (
    Button,
    Input,
    Label,
    Header,
    Footer,
    Static,
    ListView,
    ListItem,
)

from img_catalog_tui.config import Config


class MenuApp(App):
    """Textual app for the menu system with a polished, navigable UI."""

    CSS = """
    /* Compatible Textual CSS (no :root or custom CSS vars) */

    Screen {
        layout: vertical;
    }

    Header {
        background: $panel; color: $text;
    }

    Footer {
        background: $panel; color: $text;
    }

    #chrome {
        height: 1fr;
    }

    .panel {
        background: $boost;
        border: round $panel-darken-2;
        padding: 1 2;
    }

    #sidebar {
        width: 32%;
        min-width: 28;
    }

    #content {
        width: 1fr;
    }

    #title {
        content-align: center middle;
        height: auto;
        padding-bottom: 1;
        color: $text;
    }

    .hint { color: $text-muted; }
    .error { color: $error; }

    ListView { height: 1fr; padding: 0; }
    ListItem { padding: 0 1; }
    .kbd { color: $accent; text-style: bold; }

    /* Question form */
    #form_panel { layout: vertical; }

    #form_grid {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto;
        grid-columns: 24 1fr;
    }

    #form_actions { content-align: right middle; }
    """

    BINDINGS = [
        Binding("x", "exit_app", "Exit"),
        Binding("h", "show_help", "Help"),
        Binding("u", "go_up", "Up"),
    ]

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.console = Console()

        self.current_section: Optional[str] = None
        self.menu_stack: List[tuple[str, Optional[str]]] = []

        self.command: Optional[str] = None
        self.args: Dict[str, Any] = {}

        # Widgets (late bound)
        self.section_list: ListView | None = None
        self.option_list: ListView | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="chrome"):
            with Vertical(id="sidebar", classes="panel"):
                yield Static("Main Sections", id="title")
                self.section_list = ListView(id="section_list")
                yield self.section_list
                yield Static("↑/↓ to move, Enter to select", classes="hint")

            with Vertical(id="content", classes="panel"):
                yield Static("Options", id="content_title")
                self.option_list = ListView(id="option_list")
                yield self.option_list
                yield Static("Press H for help · U to go up · X to exit", classes="hint")

        yield Footer()

    def on_mount(self) -> None:
        self._populate_sections()
        self._populate_options_for_section(None)
        self.set_focus(self.section_list)

    # ----------------- Data population -----------------
    def _populate_sections(self) -> None:
        assert self.section_list is not None
        self.section_list.clear()
        for section in self.config.get_menu_sections():
            label = section.replace("_", " ").title()
            item = ListItem(Label(label), id=f"sec__{section}")

            self.section_list.append(item)

        # Add a virtual Help/Exit row to sidebar for quick access
        self.section_list.append(ListItem(Label("Help (H)"), id="action__help"))
        self.section_list.append(ListItem(Label("Exit (X)"), id="action__exit"))


    def _populate_options_for_section(self, section: Optional[str]) -> None:
        assert self.option_list is not None
        self.option_list.clear()

        if section is None:
            # Landing content area instructions
            self.option_list.append(ListItem(Static("Select a section on the left to begin.")))
            return

        subsections = self.config.get_menu_subsections(section)
        for sub in subsections:
            item_data = self.config.get_menu_item(section, sub)
            desc = item_data.get("description", sub.replace("_", " ").title())
            label = Label(f"{sub.upper()}: {desc}")
            self.option_list.append(ListItem(label, id=f"cmd__{section}__{sub}"))

        # Helpful footer-like items in the list
        self.option_list.append(ListItem(Static("—")))
        self.option_list.append(ListItem(Label("Up (U)  ·  Help (H)  ·  Exit (X)")))

    # ----------------- Event handlers -----------------
    @on(ListView.Highlighted, "#section_list")
    def _on_section_highlight(self, event: ListView.Highlighted) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("sec__"):
            section = item_id.split("__", 1)[1]
            self.current_section = section
            # Do NOT populate here to avoid duplicate IDs on quick highlight->select
            # self._populate_options_for_section(section)  # ← remove this line

    @on(ListView.Selected, "#section_list")
    def _on_section_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == "action__help":
            self.action_show_help()
            return
        if item_id == "action__exit":
            self.action_exit_app()
            return
        if item_id.startswith("sec__"):
            section = item_id.split("__", 1)[1]
            self.current_section = section
            self.menu_stack.append(("main", None))
            self._populate_options_for_section(section)
            self.set_focus(self.option_list)

    @on(ListView.Selected, "#option_list")
    def _on_option_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if not item_id or not item_id.startswith("cmd__"):
            return
        _, section, subsection = item_id.split("__", 2)
        subsection_data = self.config.get_menu_item(section, subsection)
        command = subsection_data.get("command", "")
        questions = subsection_data.get("questions", [])

        if questions:
            self.push_screen(QuestionScreen(command, questions, self))
        else:
            self.command = command
            self.args = {}
            self.exit()

    # ----------------- Actions / key bindings -----------------
    def action_exit_app(self) -> None:
        self.command = "x"
        self.args = {}
        self.exit()

    def action_show_help(self) -> None:
        from img_catalog_tui.ui.help import display_help
        display_help(self.console, self.current_section, None, self.config)

    def action_go_up(self) -> None:
        if not self.menu_stack:
            # Back to landing state
            self.current_section = None
            self._populate_options_for_section(None)
            self.set_focus(self.section_list)
            return
        prev_menu, _ = self.menu_stack.pop()
        if prev_menu == "main":
            self.current_section = None
            self._populate_options_for_section(None)
            self.set_focus(self.section_list)


class QuestionScreen(Screen):
    """Screen for asking all questions at once with clean grid form."""

    def __init__(self, command: str, questions: List[str], parent_app: MenuApp):
        super().__init__()
        self.command = command
        self.questions = questions
        self.parent_app = parent_app
        self.param_names: List[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="form_panel", classes="panel"):
            yield Label(f"Command: [bold]{self.command}")
            with Grid(id="form_grid"):
                for i, question in enumerate(self.questions):
                    parts = question.split("|")
                    if len(parts) != 2:
                        continue
                    param, prompt = parts
                    self.param_names.append(param)
                    yield Label(prompt, id=f"lbl_{i}")
                    yield Input(placeholder="", id=f"inp_{i}")
            with Horizontal(id="form_actions"):
                yield Button("Cancel", id="btn_cancel")
                yield Button("Submit", variant="primary", id="btn_submit")
        yield Footer()

    def on_mount(self) -> None:
        # Focus first input if present
        try:
            first = self.query_one("#inp_0", Input)
        except NoMatches:
            first = None
        if first:
            first.focus()

    @on(Button.Pressed, "#btn_cancel")
    def cancel(self) -> None:
        # Simply pop back to menu
        self.app.pop_screen()

    @on(Button.Pressed, "#btn_submit")
    def submit(self) -> None:
        args: Dict[str, Any] = {}
        for i, name in enumerate(self.param_names):
            value = self.query_one(f"#inp_{i}", Input).value.strip()
            args[name] = value
        self.parent_app.command = self.command
        self.parent_app.args = args
        self.parent_app.exit()

    @on(Input.Submitted)
    def next_or_submit(self, event: Input.Submitted) -> None:
        # Move focus, or submit if last
        try:
            idx = int(event.input.id.split("_")[1])
        except Exception:
            idx = -1
        try:
            next_inp = self.query_one(f"#inp_{idx+1}", Input)
        except NoMatches:
            next_inp = None

        if next_inp:
            next_inp.focus()
        else:
            self.submit()



def start_menu(config: Config) -> Tuple[str, Dict[str, Any]]:
    """Create and run the menu app and return the selected command and args."""
    app = MenuApp(config)
    app.run()
    return app.command or "x", app.args or {}

