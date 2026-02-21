"""UI layout component for ClickHouse Client."""

from dearpygui.dearpygui import *

from config import TABLES_PANEL_WIDTH
from icon_manager import icon_manager
from utils import FontManager


class UILayout:
    """Manages the main UI layout and setup."""

    def __init__(self, theme_manager, table_browser_ui):
        """Initialize UI layout manager."""
        self.theme_manager = theme_manager
        self.table_browser_ui = table_browser_ui

    def setup_main_ui(self, show_connection_settings_callback, connect_callback):
        """Setup the main user interface."""
        # Main window setup
        with window(
            label="ClickHouse Client",
            tag="main_window",
            no_resize=True,
            no_move=True,
            no_collapse=True,
        ):
            # Add menu bar
            with menu_bar(), menu(label="File"):
                add_menu_item(
                    label="Connection Settings",
                    callback=show_connection_settings_callback,
                )
                add_separator()
                add_menu_item(
                    label="Connect",
                    callback=connect_callback,
                )

            with group(horizontal=True):
                # Left panel container
                with group(width=TABLES_PANEL_WIDTH):
                    # Header and search bar (fixed at top)
                    add_text(
                        "Database Tables",
                        color=(220, 220, 220),
                        tag="database_tables_header",
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            "database_tables_header",
                            self.theme_manager.get_theme("header_text"),
                        )

                    # Add search bar for filtering table names (fixed at top)
                    add_input_text(
                        tag="table_search",
                        hint="Search tables...",
                        callback=(
                            self.table_browser_ui.filter_tables_callback
                            if self.table_browser_ui
                            else None
                        ),
                        width=TABLES_PANEL_WIDTH - 20,  # Account for padding
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            "table_search",
                            self.theme_manager.get_theme("input_enhanced"),
                        )

                    # Tables section with scroll - takes remaining space
                    with child_window(
                        label="",  # No label since header is outside
                        width=TABLES_PANEL_WIDTH,
                        height=-120,  # Leave space for status section at bottom
                        tag="tables_panel",
                        border=True,
                    ):
                        if self.theme_manager:
                            bind_item_theme(
                                "tables_panel",
                                self.theme_manager.get_theme("tables_panel"),
                            )

                        # Add group for table list
                        add_group(tag="tables_list")
                        # We'll populate this with saved connections in show_saved_connections()

                    # Status section fixed at bottom
                    with child_window(
                        label=f"{icon_manager.get('info')} Status",
                        width=TABLES_PANEL_WIDTH,
                        height=100,  # Fixed height for status
                        tag="status_panel",
                        border=True,
                    ):
                        if self.theme_manager:
                            bind_item_theme(
                                "status_panel",
                                self.theme_manager.get_theme("status_window"),
                            )
                        self._setup_status_section()

                # Right panel for query and results
                with group(width=-1):
                    self._setup_query_section()
                    self._setup_explorer_section()

        # Make main window fill viewport
        set_primary_window("main_window", True)

        # Setup font
        FontManager.setup_monospace_font()

    def _setup_status_section(self):
        """Setup the status display section."""
        add_text("Status:", color=(240, 240, 240))
        add_group(tag="status_text")
        # Status will be set by StatusManager

    def _setup_query_section(self):
        """Setup the tabbed query section."""
        with group(tag="query_section"):
            add_text(f"{icon_manager.get('query')} Query", color=(220, 220, 220))
            add_tab_bar(tag="query_tab_bar")
            self._add_tab_button_id = add_tab_button(
                label=" + ", parent="query_tab_bar", callback=None
            )

    def _setup_explorer_section(self):
        """Setup the data explorer section (tab bar only; per-tab UI built in DataExplorer.create_ui)."""
        with group(tag="explorer_section", show=False):
            add_text(f"{icon_manager.get('query')} Explorer", color=(220, 220, 220))
            add_tab_bar(tag="explorer_tab_bar")

    def connect_callbacks_to_query_interface(self, tabbed_query_interface):
        """Wire the '+' tab button and create the initial tab."""
        if tabbed_query_interface:
            configure_item(
                self._add_tab_button_id,
                callback=lambda s, d: tabbed_query_interface.create_tab(),
            )
            tabbed_query_interface.create_tab()
