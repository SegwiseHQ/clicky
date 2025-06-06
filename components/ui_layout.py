"""UI layout component for ClickHouse Client."""

from dearpygui.dearpygui import *

from config import (
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_WIDTH,
    QUERY_INPUT_HEIGHT,
    STATUS_WINDOW_HEIGHT,
    TABLES_PANEL_WIDTH,
)
from icon_manager import icon_manager
from utils import FontManager


class UILayout:
    """Manages the main UI layout and setup."""

    def __init__(self, theme_manager, table_browser_ui, data_explorer):
        """Initialize UI layout manager."""
        self.theme_manager = theme_manager
        self.table_browser_ui = table_browser_ui
        self.data_explorer = data_explorer

    def setup_main_ui(self, show_connection_settings_callback, connect_callback, disconnect_callback):
        """Setup the main user interface."""
        # Main window setup
        with window(label="ClickHouse Client", tag="main_window", no_resize=True, no_move=True, no_collapse=True):
            # Add menu bar
            with menu_bar():
                with menu(label="File"):
                    add_menu_item(
                        label="Connection Settings",
                        callback=show_connection_settings_callback,
                    )
                    add_separator()
                    add_menu_item(
                        label="Connect",
                        callback=connect_callback,
                    )
                    add_menu_item(
                        label="Disconnect",
                        callback=disconnect_callback,
                    )

            with group(horizontal=True):
                # Left panel for tables - now fills full height to match right panels
                with child_window(label=f"{icon_manager.get('table')} Database Tables", width=TABLES_PANEL_WIDTH, height=-1, tag="tables_panel", border=True):
                    if self.theme_manager:
                        bind_item_theme("tables_panel", self.theme_manager.get_theme('tables_panel'))

                    add_text("Database Tables", color=(255, 255, 0), tag="database_tables_header")
                    if self.theme_manager:
                        bind_item_theme("database_tables_header", self.theme_manager.get_theme('header_text'))

                    # Add search bar for filtering table names
                    add_input_text(
                        tag="table_search",
                        hint="Search tables...",
                        callback=self.table_browser_ui.filter_tables_callback if self.table_browser_ui else None,
                        width=-1,
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            "table_search", self.theme_manager.get_theme("input_enhanced")
                        )

                    # Add group for table list
                    add_group(tag="tables_list")
                    # We'll populate this with saved connections in show_saved_connections()

                # Right panel for query and results
                with group(width=-1):
                    self._setup_status_section()
                    self._setup_query_section()
                    self._setup_explorer_section()

        # Make main window fill viewport
        set_primary_window("main_window", True)

        # Setup font
        FontManager.setup_monospace_font()

    def _setup_status_section(self):
        """Setup the status display section."""
        with child_window(label=f"{icon_manager.get('info')} Status", height=STATUS_WINDOW_HEIGHT, tag="status_window"):
            if self.theme_manager:
                bind_item_theme("status_window", self.theme_manager.get_theme('status_window'))
            add_text("Status:", color=(255, 255, 0))
            add_group(tag="status_text")
            # Status will be set by StatusManager

    def _setup_query_section(self):
        """Setup the query input and results section."""
        with group(tag="query_section"):
            add_text(f"{icon_manager.get('query')} Query", color=(255, 255, 0))
            add_input_text(tag="query_input", multiline=True, width=-1, height=QUERY_INPUT_HEIGHT)
            if self.theme_manager:
                bind_item_theme("query_input", self.theme_manager.get_theme('input_enhanced'))
            add_button(label=f"{icon_manager.get('query')} Run Query", tag="run_query_button")
            if self.theme_manager:
                bind_item_theme("run_query_button", self.theme_manager.get_theme('button_primary'))

            add_separator()

            # Results window - fills remaining vertical space
            with child_window(label=f"{icon_manager.get('table')} Results", tag="results_window", border=True, height=-1):
                pass  # Table will be added here dynamically

    def _setup_explorer_section(self):
        """Setup the data explorer section."""
        with group(tag="explorer_section", show=False):
            # Explorer header with close button
            with group(horizontal=True):
                add_text("", tag="explorer_title", color=(255, 255, 0))
                if self.theme_manager:
                    bind_item_theme("explorer_title", self.theme_manager.get_theme('header_text'))
                add_spacer()  # Push the close button to the right
                add_button(label="Close Explorer", tag="close_explorer_button", width=140, height=35)
                if self.theme_manager:
                    bind_item_theme("close_explorer_button", self.theme_manager.get_theme('button_danger'))

            # Filter section
            with collapsing_header(label=f"{icon_manager.get('filter')} Filters", default_open=False):
                add_text("Add filters for columns:")
                add_group(tag="explorer_filters")

            # Control buttons
            with group(horizontal=True):
                add_button(label="Clear Filters", tag="explorer_clear_filters_button")
                add_text("Limit:")
                add_input_text(tag="explorer_limit", default_value="100", width=80)
                add_button(label="Apply Limit", tag="explorer_apply_limit_button")

            add_separator()

            # Data window with horizontal split - fills remaining vertical space
            with child_window(label="Data", tag="explorer_data_window", border=True, height=-1):
                with group(horizontal=True):
                    # Left panel: Main data table
                    with child_window(
                        label="Table Data", 
                        tag="explorer_main_table", 
                        border=True, 
                        width=-410,  # Leave space for right panel + some margin
                        height=-1
                    ):
                        add_text("Loading data...", color=(128, 128, 128))

                    # Right panel: Row details
                    with child_window(
                        label="Row Details", 
                        tag="explorer_row_details", 
                        border=True, 
                        width=400,
                        height=-1
                    ):
                        add_text("Select a row to view details", color=(128, 128, 128), tag="row_details_placeholder")

    def connect_callbacks_to_query_interface(self, query_interface):
        """Connect the query interface callbacks after creation."""
        if query_interface:
            # Connect run query callback
            configure_item("run_query_button", callback=query_interface.run_query_callback)

    def connect_callbacks_to_data_explorer(self, data_explorer):
        """Connect the data explorer callbacks after creation."""
        if data_explorer:
            # Connect close explorer callback
            configure_item("close_explorer_button", callback=data_explorer.close_explorer)

            # Connect other explorer callbacks
            try:
                # Connect clear filters button
                configure_item("explorer_clear_filters_button", 
                               callback=data_explorer.clear_filters)

                # Connect apply limit button
                configure_item("explorer_apply_limit_button", 
                               callback=lambda: data_explorer.refresh_data())

            except Exception as e:
                print(f"Error connecting data explorer callbacks: {e}")
