"""Main application class for ClickHouse Client."""

import time
import traceback

from dearpygui.dearpygui import *

from components.connection_manager import ConnectionManager
from components.credentials_ui import CredentialsUI
from components.splash_screen import SplashScreenManager
from components.table_browser_ui import TableBrowserUI
from components.ui_layout import UILayout
from config import (
    COLOR_ERROR,
    COLOR_SUCCESS,
    DEFAULT_DATABASE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_WIDTH,
    QUERY_INPUT_HEIGHT,
    STATUS_WINDOW_HEIGHT,
    TABLES_PANEL_WIDTH,
)
from credentials_manager import CredentialsManager
from data_explorer import DataExplorer
from database import DatabaseManager
from icon_manager import icon_manager
from theme_manager import ThemeManager
from ui_components import QueryInterface, StatusManager, TableBrowser
from utils import FontManager, UIHelpers, validate_connection_params


class ClickHouseClientApp:
    """Main application class that orchestrates all components."""

    def __init__(self):
        """Initialize application components."""
        # Initialize DearPyGUI first
        create_context()
        create_viewport(title=f"{icon_manager.get('database')} ClickHouse Client", width=MAIN_WINDOW_WIDTH, height=MAIN_WINDOW_HEIGHT)

        # Initialize and show splash screen
        self.splash_manager = SplashScreenManager()
        self.splash_manager.show_splash()
        self.splash_manager.next_step("Initializing DearPyGUI...")

        # Initialize theme manager and apply global theme
        self.theme_manager = ThemeManager()
        self.theme_manager.apply_global_theme()
        self.splash_manager.next_step("Loading theme manager...")

        # Core components
        self.db_manager = DatabaseManager()
        self.credentials_manager = CredentialsManager()
        self.splash_manager.next_step("Setting up database manager...")

        self.table_browser = TableBrowser(self.db_manager, self.theme_manager)
        self.query_interface = QueryInterface(self.db_manager, self.theme_manager)
        self.data_explorer = DataExplorer(self.db_manager, self.theme_manager)
        self.splash_manager.next_step("Configuring credentials manager...")

        # New refactored components
        self.connection_manager = ConnectionManager(
            self.db_manager, self.credentials_manager, self.theme_manager
        )
        self.table_browser_ui = TableBrowserUI(
            self.db_manager, self.credentials_manager, self.theme_manager
        )
        self.credentials_ui = CredentialsUI(
            self.credentials_manager, self.connection_manager, self.theme_manager
        )
        self.ui_layout = UILayout(
            self.theme_manager, self.table_browser_ui, self.data_explorer
        )
        self.splash_manager.next_step("Initializing UI components...")

        # Initialize stored credentials for auto-connect
        self.stored_credentials = None

        # Initialize status manager with theme
        StatusManager.set_theme_manager(self.theme_manager)
        self.splash_manager.next_step("Setting up callbacks...")

        # Set up callbacks between components
        self.table_browser.set_double_click_callback(self.data_explorer.open_explorer)
        self.table_browser.set_status_callback(StatusManager.show_status)
        self.query_interface.set_status_callback(StatusManager.show_status)

        # Set up double-click callback for the new table browser UI component
        self.table_browser_ui.set_double_click_callback(self._handle_table_double_click)

        # Connect table browser UI to connection callback
        self.table_browser_ui.connection_callback = self.connect_callback
        self.table_browser_ui.stored_credentials = None

    def setup_ui(self):
        """Setup the main user interface."""
        # Setup main UI layout using the new component
        self.ui_layout.setup_main_ui(
            show_connection_settings_callback=self.credentials_ui.show_connection_settings_modal,
            connect_callback=self.connect_callback,
            disconnect_callback=self.disconnect_callback,
        )

        # Connect callbacks after UI creation
        self.ui_layout.connect_callbacks_to_query_interface(self.query_interface)
        self.ui_layout.connect_callbacks_to_data_explorer(self.data_explorer)

        # Initialize status
        StatusManager.show_status("Not connected", error=True)

    def connect_callback(self, sender, data):
        """Handle database connection."""
        # Use stored credentials if available, otherwise get from form
        if self.stored_credentials:
            result = self.connection_manager.connect_with_credentials(
                self.stored_credentials
            )
        else:
            result = self.connection_manager.connect_callback(sender, data)

        if result:  # Connection successful
            # Update table browser UI
            current_search = UIHelpers.safe_get_value("table_search", "")
            self.table_browser_ui.filter_tables_callback(None, current_search)

        return result

    def disconnect_callback(self, sender, data):
        """Handle database disconnection."""
        result = self.connection_manager.disconnect_callback(sender, data)

        if result:  # Disconnection successful
            # Update UI components
            self.table_browser.clear_tables()
            self.data_explorer.close_explorer()
            # Clear state in table browser UI component
            self.table_browser_ui.clear_connection_state()
            self.table_browser_ui.show_saved_connections()

        return result

    def save_credentials_callback(self, sender, data):
        """Save current connection credentials with default name (legacy)."""
        # Delegate to credentials UI component
        self.credentials_ui.save_credentials_callback(sender, data)

    def save_named_credentials_callback(self, sender, data):
        """Save current connection credentials with specified name."""
        # Delegate to credentials UI component
        self.credentials_ui.save_named_credentials_callback(sender, data)

    def load_credentials_callback(self, sender, data):
        """Load saved connection credentials (legacy - loads first available)."""
        # Delegate to credentials UI component
        self.credentials_ui.load_credentials_callback(sender, data)

    def load_selected_credentials_callback(self, sender, data):
        """Load credentials selected from dropdown."""
        # Delegate to credentials UI component
        self.credentials_ui.load_selected_credentials_callback(sender, data)

    def refresh_credentials_callback(self, sender, data):
        """Refresh the credentials dropdown list."""
        # Delegate to credentials UI component
        self.credentials_ui.refresh_credentials_callback(sender, data)

    def delete_credentials_callback(self, sender, data):
        """Delete selected credentials."""
        # Delegate to credentials UI component
        self.credentials_ui.delete_credentials_callback(sender, data)

    def filter_tables_callback(self, sender, app_data):
        """Filter tables in the left panel based on the search query."""
        # Delegate to table browser UI component
        self.table_browser_ui.filter_tables_callback(sender, app_data)

    def select_table_callback(self, sender, app_data):
        """Handle table selection from the filtered list."""
        # Delegate to table browser UI component
        self.table_browser_ui.select_table_callback(sender, app_data)

    def _get_connection_display_name(self) -> str:
        """Get a formatted display name for the current connection."""
        # Delegate to connection manager component
        return self.connection_manager.get_connection_display_name()

    def _set_form_values(self, credentials: dict):
        """Set form values from credentials dictionary."""
        UIHelpers.safe_configure_item("host_input", default_value=credentials["host"])
        UIHelpers.safe_configure_item("port_input", default_value=credentials["port"])
        UIHelpers.safe_configure_item("username_input", default_value=credentials["user"])
        UIHelpers.safe_configure_item("password_input", default_value=credentials["password"])
        UIHelpers.safe_configure_item("database_input", default_value=credentials["database"])

    def _clear_form_values(self):
        """Clear all form values."""
        UIHelpers.safe_configure_item("host_input", default_value=DEFAULT_HOST)
        UIHelpers.safe_configure_item("port_input", default_value=DEFAULT_PORT)
        UIHelpers.safe_configure_item("username_input", default_value=DEFAULT_USERNAME)
        UIHelpers.safe_configure_item("password_input", default_value="")
        UIHelpers.safe_configure_item("database_input", default_value=DEFAULT_DATABASE)

    def auto_load_and_connect(self):
        """Auto-load credentials without attempting connection on startup."""
        # Delegate to connection manager component
        self.connection_manager.auto_load_and_connect()

    def show_connection_settings_modal(self):
        """Show a modal dialog for connection settings."""
        # Delegate to credentials UI component
        self.credentials_ui.show_connection_settings_modal()

    def run(self):
        """Run the application."""
        self.splash_manager.next_step("Finalizing setup...")
        self.setup_ui()

        setup_dearpygui()
        show_viewport()

        # Just load credentials without auto-connecting
        self.auto_load_and_connect()

        # Show saved connections in the left panel
        self.show_saved_connections()

        # Hide splash screen now that everything is ready
        self.splash_manager.complete()

        start_dearpygui()
        destroy_context()

    def _find_credential_name_for_connection(self) -> str:
        """Find the saved credential name that matches the current connection."""
        # Delegate to connection manager component
        return self.connection_manager.find_credential_name_for_connection()

    def toggle_connection_callback(self, sender, app_data):
        """Toggle the visibility of tables under a connection."""
        # Delegate to table browser UI component
        self.table_browser_ui.toggle_connection_callback(sender, app_data)

    def show_saved_connections(self):
        """Show all saved connections in the left panel."""
        # Delegate to table browser UI component
        self.table_browser_ui.show_saved_connections()

    def connect_to_saved_callback(self, sender, app_data, user_data):
        """Handle clicking on a saved connection to connect to it."""
        # Delegate to table browser UI component
        self.table_browser_ui.connect_to_saved_callback(sender, app_data, user_data)

    def _handle_table_double_click(self, table_name: str):
        """Handle double-click on table name to open data explorer."""
        self.data_explorer.open_explorer(table_name, StatusManager.show_status)
