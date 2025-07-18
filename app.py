"""Main application class for ClickHouse Client."""

import time
import traceback

from dearpygui.dearpygui import *

from components import QueryInterface, StatusManager, TableBrowser
from components.connection_manager import ConnectionManager
from components.credentials_ui import CredentialsUI
from components.table_browser_ui import TableBrowserUI
from components.ui_layout import UILayout
from config import (
    COLOR_CONNECTED,
    COLOR_DISCONNECTED,
    COLOR_ERROR,
    COLOR_SUCCESS,
    DEFAULT_DATABASE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_WIDTH,
    QUERY_INPUT_HEIGHT,
    TABLES_PANEL_WIDTH,
)
from credentials_manager import CredentialsManager
from data_explorer import DataExplorer
from database import DatabaseManager
from icon_manager import icon_manager
from theme_manager import ThemeManager
from utils import FontManager, UIHelpers, validate_connection_params


class ClickHouseClientApp:
    """Main application class that orchestrates all components."""

    def __init__(self):
        """Initialize application components."""
        # Initialize DearPyGUI first
        create_context()
        create_viewport(
            title=f"{icon_manager.get('database')} ClickHouse Client",
            width=MAIN_WINDOW_WIDTH,
            height=MAIN_WINDOW_HEIGHT,
        )

        # Initialize theme manager and apply global theme
        self.theme_manager = ThemeManager()
        self.theme_manager.apply_global_theme()

        # Components
        self.db_manager = DatabaseManager()
        self.credentials_manager = CredentialsManager()

        # Initialize connection manager
        self.connection_manager = ConnectionManager(
            self.db_manager, self.credentials_manager, self.theme_manager
        )

        # Initialize credentials UI
        self.credentials_ui = CredentialsUI(
            self.credentials_manager, self.connection_manager, self.theme_manager
        )

        # Set up credentials UI callback
        self.credentials_ui.on_credentials_saved = self._handle_credentials_saved

        self.table_browser = TableBrowser(self.db_manager, self.theme_manager)
        self.table_browser_ui = TableBrowserUI(
            self.db_manager,
            self.credentials_manager,
            self.theme_manager,
            self.connection_manager,
        )
        self.query_interface = QueryInterface(self.db_manager, self.theme_manager)
        self.data_explorer = DataExplorer(self.db_manager, self.theme_manager)

        # Initialize UI Layout with required components
        self.ui_layout = UILayout(
            self.theme_manager, self.table_browser_ui, self.data_explorer
        )

        # Set up callbacks for connection manager
        self.connection_manager.on_connect_success = self._handle_connect_success
        self.connection_manager.on_disconnect = self._handle_disconnect

        # Initialize stored credentials for auto-connect
        self.stored_credentials = None

        # Link stored credentials between app and connection manager
        self._sync_stored_credentials()

        # Initialize status manager with theme
        StatusManager.set_theme_manager(self.theme_manager)

        # Set up callbacks
        self.table_browser.set_double_click_callback(self.data_explorer.open_explorer)
        self.table_browser.set_status_callback(StatusManager.show_status)
        self.table_browser_ui.set_double_click_callback(
            self.data_explorer.open_explorer
        )
        self.table_browser_ui.connection_callback = (
            self.connection_manager.connect_callback
        )
        self.query_interface.set_status_callback(StatusManager.show_status)

    def setup_ui(self):
        """Setup the main user interface using UI Layout component."""
        # Use the UILayout component to setup the main UI
        self.ui_layout.setup_main_ui(
            show_connection_settings_callback=self.credentials_ui.show_connection_settings_modal,
            connect_callback=self.connection_manager.connect_callback,
            disconnect_callback=self.connection_manager.disconnect_callback,
        )

        # Connect callbacks after UI is created
        self.ui_layout.connect_callbacks_to_query_interface(self.query_interface)
        self.ui_layout.connect_callbacks_to_data_explorer(self.data_explorer)

        # Initialize status
        StatusManager.show_status("Not connected", error=True)

    def _handle_connect_success(self):
        """Handle additional tasks after successful connection."""
        try:
            # Auto-save credentials on successful connection
            self.credentials_ui.save_credentials_callback(None, None)

            # Automatically list tables after successful connection
            # Use table browser UI's filtering to display connection and tables
            current_search = UIHelpers.safe_get_value("table_search", "")
            self.table_browser_ui.filter_tables_callback(None, current_search)

        except Exception as e:
            print(f"[DEBUG] Error in connect success handler: {str(e)}")

    def _handle_disconnect(self):
        """Handle additional tasks after disconnection."""
        try:
            # Update UI
            self.table_browser.clear_tables()
            self.data_explorer.close_explorer()

            # Clear connection state in table browser UI
            self.table_browser_ui.clear_connection_state()

            # Refresh connection list in the left panel
            self.table_browser_ui.show_saved_connections()

        except Exception as e:
            print(f"[DEBUG] Error in disconnect handler: {str(e)}")

    def _sync_stored_credentials(self):
        """Sync stored credentials between app and connection manager."""
        # This can be called to sync credentials when they change
        if self.stored_credentials:
            self.connection_manager.stored_credentials = self.stored_credentials
        elif (
            hasattr(self.table_browser_ui, "stored_credentials")
            and self.table_browser_ui.stored_credentials
        ):
            self.connection_manager.stored_credentials = (
                self.table_browser_ui.stored_credentials
            )

    def _handle_credentials_saved(self):
        """Handle tasks after credentials are saved."""
        try:
            # Update the connections list in the table browser UI
            self.table_browser_ui.show_saved_connections()
        except Exception as e:
            print(f"[DEBUG] Error in credentials saved handler: {str(e)}")

    def filter_tables_callback(self, sender, app_data):
        """Delegate table filtering to TableBrowserUI component."""
        return self.table_browser_ui.filter_tables_callback(sender, app_data)

    def select_table_callback(self, sender, app_data):
        """Delegate table selection to TableBrowserUI component."""
        return self.table_browser_ui.select_table_callback(sender, app_data)

    def run(self):
        """Run the application."""
        self.setup_ui()

        setup_dearpygui()
        show_viewport()

        # Use connection manager for auto-loading credentials
        self.connection_manager.auto_load_and_connect()

        # Sync credentials after auto-loading
        if self.connection_manager.stored_credentials:
            self.stored_credentials = self.connection_manager.stored_credentials

        # Show saved connections in the left panel
        self.table_browser_ui.show_saved_connections()

        start_dearpygui()
        destroy_context()
