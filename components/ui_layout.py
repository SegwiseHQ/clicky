"""UI layout component for ClickHouse Client."""

from dearpygui.dearpygui import *

from config import (
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_WIDTH,
    QUERY_INPUT_HEIGHT,
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

    def setup_main_ui(
        self, show_connection_settings_callback, connect_callback, disconnect_callback
    ):
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
                # Left panel container
                with group(width=TABLES_PANEL_WIDTH):
                    # Tables section with scroll - takes most of the space
                    with child_window(
                        label=f"{icon_manager.get('table')} Database Tables",
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

                        # Add search bar for filtering table names
                        add_input_text(
                            tag="table_search",
                            hint="Search tables...",
                            callback=(
                                self.table_browser_ui.filter_tables_callback
                                if self.table_browser_ui
                                else None
                            ),
                            width=-1,
                        )
                        if self.theme_manager:
                            bind_item_theme(
                                "table_search",
                                self.theme_manager.get_theme("input_enhanced"),
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
        """Setup the query input and results section."""
        with group(tag="query_section"):
            add_text(f"{icon_manager.get('query')} Query", color=(220, 220, 220))
            add_input_text(
                tag="query_input", multiline=True, width=-1, height=QUERY_INPUT_HEIGHT
            )
            if self.theme_manager:
                bind_item_theme(
                    "query_input", self.theme_manager.get_theme("input_enhanced")
                )

            # Run Query button
            add_button(
                label=f"{icon_manager.get('query')} Run Query", tag="run_query_button"
            )
            if self.theme_manager:
                bind_item_theme(
                    "run_query_button", self.theme_manager.get_theme("button_primary")
                )

            # Save as JSON button - positioned below Run Query button
            add_button(
                label=f"{icon_manager.get('export')} Save as JSON",
                tag="save_json_button",
                show=False,  # Initially hidden
            )
            if self.theme_manager:
                bind_item_theme(
                    "save_json_button", self.theme_manager.get_theme("button_primary")
                )

            add_separator()

            # Results window - fills remaining vertical space
            with child_window(
                label=f"{icon_manager.get('table')} Results",
                tag="results_window",
                border=True,
                height=-1,
            ):
                pass  # Table will be added here dynamically

    def _setup_explorer_section(self):
        """Setup the data explorer section."""
        with group(tag="explorer_section", show=False):
            # Explorer header
            with group(horizontal=True):
                add_text("", tag="explorer_title", color=(220, 220, 220))
                if self.theme_manager:
                    bind_item_theme(
                        "explorer_title", self.theme_manager.get_theme("header_text")
                    )

            # Simple WHERE filter section
            with group(horizontal=True):
                add_text("WHERE:")
                add_input_text(
                    tag="explorer_where",
                    hint="Enter WHERE condition - Press Enter to apply",
                    width=-150,
                    on_enter=True,  # Only trigger callback on Enter key
                    callback=lambda s, d: None,  # Will be connected later
                )
                add_text("  Limit:")
                add_input_text(
                    tag="explorer_limit",
                    default_value="100",
                    width=80,
                    on_enter=True,  # Only trigger callback on Enter key
                    callback=lambda s, d: None,  # Will be connected later
                )

            # Button controls row (moved closer to reduce spacing)
            with table(header_row=False, tag="button_table"):
                add_table_column(width_fixed=True, init_width_or_weight=150)
                add_table_column(width_fixed=True, init_width_or_weight=150)

                with table_row():
                    with table_cell():
                        add_button(
                            label="Close Explorer",
                            tag="close_explorer_button",
                            width=140,
                            height=35,
                        )
                    with table_cell():
                        add_button(
                            label="Toggle Row Details",
                            tag="explorer_toggle_details_button",
                            width=140,
                            height=35,
                        )

            # Apply themes to all fields at once
            if self.theme_manager:
                bind_item_theme(
                    "explorer_where",
                    self.theme_manager.get_theme("input_enhanced"),
                )
                bind_item_theme(
                    "explorer_limit",
                    self.theme_manager.get_theme("input_enhanced"),
                )
                bind_item_theme(
                    "close_explorer_button",
                    self.theme_manager.get_theme("button_danger"),
                )
                bind_item_theme(
                    "explorer_toggle_details_button",
                    self.theme_manager.get_theme("button_primary"),
                )

            # Data window with horizontal split - fills remaining vertical space
            with child_window(
                label="Data", tag="explorer_data_window", border=True, height=-1
            ):
                with group(horizontal=True, tag="explorer_data_layout"):
                    # Left panel: Main data table
                    with child_window(
                        label="Table Data",
                        tag="explorer_main_table",
                        border=True,
                        width=-410,  # Leave space for right panel + some margin
                        height=-1,
                    ):
                        add_text("Loading data...", color=(128, 128, 128))

                    # Right panel: Row details (initially visible)
                    with child_window(
                        label="Row Details",
                        tag="explorer_row_details",
                        border=True,
                        width=400,
                        height=-1,
                        show=True,  # Initially visible
                    ):
                        add_text(
                            "Select a row to view details",
                            color=(128, 128, 128),
                            tag="row_details_placeholder",
                        )

    def connect_callbacks_to_query_interface(self, query_interface):
        """Connect the query interface callbacks after creation."""
        if query_interface:
            # Connect run query callback
            configure_item(
                "run_query_button", callback=query_interface.run_query_callback
            )

            # Connect save as JSON callback
            configure_item(
                "save_json_button", callback=query_interface.save_as_json_callback
            )

    def connect_callbacks_to_data_explorer(self, data_explorer):
        """Connect the data explorer callbacks after creation."""
        if data_explorer:
            # Connect close explorer callback
            configure_item(
                "close_explorer_button", callback=data_explorer.close_explorer
            )

            # Connect other explorer callbacks
            try:
                # Connect WHERE and limit input callbacks
                configure_item(
                    "explorer_where", callback=data_explorer._on_where_change
                )

                # Connect toggle details button
                configure_item(
                    "explorer_toggle_details_button",
                    callback=self._toggle_row_details_panel,
                )

            except Exception as e:
                print(f"Error connecting data explorer callbacks: {e}")

    def _toggle_row_details_panel(self):
        """Toggle the visibility of the row details panel."""
        try:
            # Get current visibility state
            is_visible = get_item_configuration("explorer_row_details")["show"]

            # Toggle visibility
            configure_item("explorer_row_details", show=not is_visible)

            # Adjust main table width based on panel visibility
            if is_visible:
                # Panel is being hidden - expand main table to full width
                configure_item("explorer_main_table", width=-1)
            else:
                # Panel is being shown - leave space for it
                configure_item("explorer_main_table", width=-410)

        except Exception as e:
            print(f"Error toggling row details panel: {e}")
