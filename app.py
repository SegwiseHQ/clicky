"""Main application class for ClickHouse Client."""

import time
import traceback

from dearpygui.dearpygui import *

from components import QueryInterface, StatusManager, TableBrowser
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
    STATUS_WINDOW_HEIGHT,
    TABLES_PANEL_WIDTH,
)
from credentials_manager import CredentialsManager
from data_explorer import DataExplorer
from database import DatabaseManager
from icon_manager import icon_manager
from theme_manager import ThemeManager
from utils import (
    FontManager,
    UIHelpers,
    format_connection_string,
    validate_connection_params,
)


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
        self.table_browser = TableBrowser(self.db_manager, self.theme_manager)
        self.table_browser_ui = TableBrowserUI(
            self.db_manager, self.credentials_manager, self.theme_manager
        )
        self.query_interface = QueryInterface(self.db_manager, self.theme_manager)
        self.data_explorer = DataExplorer(self.db_manager, self.theme_manager)

        # Initialize UI Layout with required components
        self.ui_layout = UILayout(
            self.theme_manager, self.table_browser_ui, self.data_explorer
        )

        # Initialize stored credentials for auto-connect
        self.stored_credentials = None

        # Initialize status manager with theme
        StatusManager.set_theme_manager(self.theme_manager)

        # Set up callbacks
        self.table_browser.set_double_click_callback(self.data_explorer.open_explorer)
        self.table_browser.set_status_callback(StatusManager.show_status)
        self.table_browser_ui.set_double_click_callback(
            self.data_explorer.open_explorer
        )
        self.table_browser_ui.connection_callback = self.connect_callback
        self.query_interface.set_status_callback(StatusManager.show_status)

    def setup_ui(self):
        """Setup the main user interface using UI Layout component."""
        # Use the UILayout component to setup the main UI
        self.ui_layout.setup_main_ui(
            show_connection_settings_callback=self.show_connection_settings_modal,
            connect_callback=self.connect_callback,
            disconnect_callback=self.disconnect_callback,
        )

        # Connect callbacks after UI is created
        self.ui_layout.connect_callbacks_to_query_interface(self.query_interface)
        self.ui_layout.connect_callbacks_to_data_explorer(self.data_explorer)

        # Initialize status
        StatusManager.show_status("Not connected", error=True)

    def connect_callback(self, sender, data):
        """Handle database connection."""
        # Disable connect button and show connecting status
        UIHelpers.safe_configure_item("connect_button", enabled=False)
        StatusManager.show_status("Connecting... Please wait", error=False)

        try:
            # Get connection parameters - check multiple sources for stored credentials
            stored_credentials = None
            if self.stored_credentials:
                stored_credentials = self.stored_credentials
                print("[DEBUG] Using app stored credentials for connection")
            elif (
                hasattr(self.table_browser_ui, "stored_credentials")
                and self.table_browser_ui.stored_credentials
            ):
                stored_credentials = self.table_browser_ui.stored_credentials
                print(
                    "[DEBUG] Using table browser UI stored credentials for connection"
                )

            if stored_credentials:
                host = stored_credentials.get("host", DEFAULT_HOST)
                port = stored_credentials.get("port", DEFAULT_PORT)
                username = stored_credentials.get("user", DEFAULT_USERNAME)
                password = stored_credentials.get("password", "")
                database = stored_credentials.get("database", DEFAULT_DATABASE)
            else:
                print("[DEBUG] Using form values for connection")
                host = UIHelpers.safe_get_value("host_input", DEFAULT_HOST)
                port = UIHelpers.safe_get_value("port_input", DEFAULT_PORT)
                username = UIHelpers.safe_get_value("username_input", DEFAULT_USERNAME)
                password = UIHelpers.safe_get_value("password_input", "")
                database = UIHelpers.safe_get_value("database_input", DEFAULT_DATABASE)

            print(
                f"[DEBUG] Connection parameters: host={host}, port={port}, username={username}, database={database}"
            )

            # Validate parameters
            is_valid, error_msg = validate_connection_params(
                host, port, username, database
            )
            if not is_valid:
                raise ValueError(error_msg)

            print("[DEBUG] Connection parameters validated successfully")

            # Attempt connection
            success, message = self.db_manager.connect(
                host, int(port), username, password, database
            )
            print(
                f"[DEBUG] Connection attempt result: success={success}, message={message}"
            )

            if success:
                StatusManager.show_status(message)
                UIHelpers.safe_configure_item(
                    "connection_indicator", color=COLOR_SUCCESS
                )
                # Apply connected theme to connection indicator
                connected_theme = self.theme_manager.create_connection_indicator_theme(
                    True
                )
                UIHelpers.safe_bind_item_theme("connection_indicator", connected_theme)

                # Cache tables for autocomplete after successful connection
                self.query_interface.autocomplete_manager.cache_tables()

                self.save_credentials_callback(
                    None, None
                )  # Auto-save on successful connection

                # Automatically list tables after successful connection
                # Use table browser UI's filtering to display connection and tables
                current_search = UIHelpers.safe_get_value("table_search", "")
                self.table_browser_ui.filter_tables_callback(None, current_search)

                # Update button states
                UIHelpers.safe_configure_item("connect_button", enabled=True)
                UIHelpers.safe_configure_item("disconnect_button", enabled=True)
            else:
                raise Exception(message)

        except Exception as e:
            error_msg = f"Connection failed:\n{str(e)}"
            if hasattr(e, "__traceback__"):
                error_msg += f"\nDetails:\n{traceback.format_exc()}"
            StatusManager.show_status(error_msg, error=True)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            # Apply disconnected theme to connection indicator
            disconnected_theme = self.theme_manager.create_connection_indicator_theme(
                False
            )
            UIHelpers.safe_bind_item_theme("connection_indicator", disconnected_theme)
        finally:
            # Re-enable connect button
            UIHelpers.safe_configure_item("connect_button", enabled=True)

    def disconnect_callback(self, sender, data):
        """Handle database disconnection."""
        try:
            message = self.db_manager.disconnect()

            # Clear autocomplete cache
            self.query_interface.autocomplete_manager.clear_cache()

            # Update UI
            self.table_browser.clear_tables()
            self.data_explorer.close_explorer()

            # Clear connection state in table browser UI
            self.table_browser_ui.clear_connection_state()

            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            # Apply disconnected theme to connection indicator
            disconnected_theme = self.theme_manager.create_connection_indicator_theme(
                False
            )
            UIHelpers.safe_bind_item_theme("connection_indicator", disconnected_theme)

            StatusManager.show_status(message)

            # Update button states
            UIHelpers.safe_configure_item("connect_button", enabled=True)
            UIHelpers.safe_configure_item("disconnect_button", enabled=False)

            # Refresh connection list in the left panel
            self.table_browser_ui.show_saved_connections()

        except Exception as e:
            StatusManager.show_status(f"Error during disconnect: {str(e)}", error=True)

    def save_credentials_callback(self, sender, data):
        """Save current connection credentials with default name (legacy)."""
        try:
            host = UIHelpers.safe_get_value("host_input", DEFAULT_HOST)
            port = UIHelpers.safe_get_value("port_input", DEFAULT_PORT)
            username = UIHelpers.safe_get_value("username_input", DEFAULT_USERNAME)
            password = UIHelpers.safe_get_value("password_input", "")
            database = UIHelpers.safe_get_value("database_input", DEFAULT_DATABASE)

            success, message = self.credentials_manager.save_credentials_legacy(
                host, port, username, password, database
            )
            StatusManager.show_status(message, error=not success)

            if success:
                self.refresh_credentials_callback(None, None)

        except Exception as e:
            StatusManager.show_status(f"Error saving credentials: {str(e)}", error=True)

    def save_named_credentials_callback(self, sender, data):
        """Save current connection credentials with specified name."""
        try:
            name = UIHelpers.safe_get_value("credential_name_input", "").strip()
            if not name:
                StatusManager.show_status("Please enter a credential name", error=True)
                return

            host = UIHelpers.safe_get_value("host_input", DEFAULT_HOST)
            port = UIHelpers.safe_get_value("port_input", DEFAULT_PORT)
            username = UIHelpers.safe_get_value("username_input", DEFAULT_USERNAME)
            password = UIHelpers.safe_get_value("password_input", "")
            database = UIHelpers.safe_get_value("database_input", DEFAULT_DATABASE)

            success, message = self.credentials_manager.save_credentials(
                name, host, port, username, password, database
            )
            StatusManager.show_status(message, error=not success)

            if success:
                self.refresh_credentials_callback(None, None)
                # Clear the name input
                UIHelpers.safe_configure_item("credential_name_input", default_value="")
                # Update the connections list
                self.table_browser_ui.show_saved_connections()

        except Exception as e:
            StatusManager.show_status(f"Error saving credentials: {str(e)}", error=True)

    def load_credentials_callback(self, sender, data):
        """Load saved connection credentials (legacy - loads first available)."""
        try:
            success, credentials, message = (
                self.credentials_manager.load_credentials_legacy()
            )

            if success and credentials:
                self._set_form_values(credentials)

            StatusManager.show_status(message, error=not success)

        except Exception as e:
            StatusManager.show_status(
                f"Error loading credentials: {str(e)}", error=True
            )

    def load_selected_credentials_callback(self, sender, data):
        """Load credentials selected from dropdown."""
        try:
            selected_name = UIHelpers.safe_get_value("credentials_combo", "")
            if not selected_name:
                return

            success, credentials, message = self.credentials_manager.load_credentials(
                selected_name
            )

            if success and credentials:
                self._set_form_values(credentials)
                StatusManager.show_status(message, error=False)
            else:
                StatusManager.show_status(message, error=True)

        except Exception as e:
            StatusManager.show_status(
                f"Error loading credentials: {str(e)}", error=True
            )

    def refresh_credentials_callback(self, sender, data):
        """Refresh the credentials dropdown list."""
        try:
            names = self.credentials_manager.get_credential_names()
            UIHelpers.safe_configure_item("credentials_combo", items=names)

            if names:
                StatusManager.show_status(
                    f"Found {len(names)} saved credential sets", error=False
                )
            else:
                StatusManager.show_status("No saved credentials found", error=False)

        except Exception as e:
            StatusManager.show_status(
                f"Error refreshing credentials: {str(e)}", error=True
            )

    def delete_credentials_callback(self, sender, data):
        """Delete selected credentials."""
        try:
            selected_name = UIHelpers.safe_get_value("credentials_combo", "")
            if not selected_name:
                StatusManager.show_status(
                    "Please select credentials to delete", error=True
                )
                return

            success, message = self.credentials_manager.delete_credentials(
                selected_name
            )
            StatusManager.show_status(message, error=not success)

            if success:
                self.refresh_credentials_callback(None, None)
                # Clear form if deleted credentials were loaded
                current_name = UIHelpers.safe_get_value("credential_name_input", "")
                if current_name == selected_name:
                    self._clear_form_values()

        except Exception as e:
            StatusManager.show_status(
                f"Error deleting credentials: {str(e)}", error=True
            )

    def filter_tables_callback(self, sender, app_data):
        """Delegate table filtering to TableBrowserUI component."""
        return self.table_browser_ui.filter_tables_callback(sender, app_data)

    def select_table_callback(self, sender, app_data):
        """Delegate table selection to TableBrowserUI component."""
        return self.table_browser_ui.select_table_callback(sender, app_data)

    def _set_form_values(self, credentials: dict):
        """Set form values from credentials dictionary."""
        UIHelpers.safe_configure_item("host_input", default_value=credentials["host"])
        UIHelpers.safe_configure_item("port_input", default_value=credentials["port"])
        UIHelpers.safe_configure_item(
            "username_input", default_value=credentials["user"]
        )
        UIHelpers.safe_configure_item(
            "password_input", default_value=credentials["password"]
        )
        UIHelpers.safe_configure_item(
            "database_input", default_value=credentials["database"]
        )

    def _clear_form_values(self):
        """Clear all form values."""
        UIHelpers.safe_configure_item("host_input", default_value=DEFAULT_HOST)
        UIHelpers.safe_configure_item("port_input", default_value=DEFAULT_PORT)
        UIHelpers.safe_configure_item("username_input", default_value=DEFAULT_USERNAME)
        UIHelpers.safe_configure_item("password_input", default_value="")
        UIHelpers.safe_configure_item("database_input", default_value=DEFAULT_DATABASE)

    def auto_load_and_connect(self):
        """Auto-load credentials without attempting connection on startup."""
        try:
            print("[DEBUG] Starting auto_load_credentials")

            # Refresh credentials list first
            self.refresh_credentials_callback(None, None)

            # Try to load the first available credentials
            success, credentials, message = (
                self.credentials_manager.load_credentials_legacy()
            )
            print(
                f"[DEBUG] Load credentials result: success={success}, message={message}"
            )

            if credentials:
                print(f"[DEBUG] Credentials found: {credentials}")

            if success and credentials:
                StatusManager.show_status(
                    "Credentials loaded automatically. Click 'Connect' to establish connection."
                )

                # Store the credentials for later use
                self.stored_credentials = credentials

                # Set form values without connecting
                self._set_form_values(credentials)

                # No auto-connecting anymore
                print(f"[DEBUG] Credentials loaded but not auto-connecting")
            else:
                print("[DEBUG] No credentials found or load failed")
                StatusManager.show_status(
                    "No saved credentials found. Please enter connection details.",
                    error=False,
                )

        except Exception as e:
            print(f"[DEBUG] Auto-load exception: {str(e)}")
            StatusManager.show_status(f"Auto-load failed: {str(e)}", error=True)

    def show_connection_settings_modal(self):
        """Show a modal dialog for connection settings."""
        # Check if modal already exists and delete it to avoid tag conflicts
        try:
            if does_item_exist("connection_settings_modal"):
                delete_item("connection_settings_modal")
        except:
            pass

        with window(
            label="Connection Settings",
            modal=True,
            tag="connection_settings_modal",
            width=500,
            height=600,
        ):
            add_text(
                "ClickHouse Connection Settings", color=(255, 193, 7)
            )  # Yellow header
            add_separator()

            # Credential management section
            add_text("Saved Connections:", color=(255, 255, 0))
            with group(horizontal=True):
                add_combo(
                    label="Saved Credentials",
                    tag="credentials_combo",
                    callback=self.load_selected_credentials_callback,
                    width=250,
                )
                bind_item_theme(
                    "credentials_combo", self.theme_manager.get_theme("combo_enhanced")
                )
                add_button(
                    label="Refresh",
                    callback=self.refresh_credentials_callback,
                    width=80,
                    tag="refresh_button",
                )
                bind_item_theme(
                    "refresh_button", self.theme_manager.get_theme("button_secondary")
                )

            add_text("Save New Connection:")
            with group(horizontal=True):
                add_input_text(
                    tag="credential_name_input", width=200, hint="Connection name"
                )
                bind_item_theme(
                    "credential_name_input",
                    self.theme_manager.get_theme("input_enhanced"),
                )
                add_button(
                    label="Save As",
                    callback=self.save_named_credentials_callback,
                    width=80,
                    tag="save_as_button",
                )
                bind_item_theme(
                    "save_as_button", self.theme_manager.get_theme("button_success")
                )
                add_button(
                    label="Delete",
                    callback=self.delete_credentials_callback,
                    width=80,
                    tag="delete_button",
                )
                bind_item_theme(
                    "delete_button", self.theme_manager.get_theme("button_danger")
                )

            add_separator()

            # Connection parameters with left-aligned labels
            add_text("Host/Server Address:")
            add_input_text(
                default_value=DEFAULT_HOST,
                tag="host_input",
                hint="e.g., localhost, 192.168.1.100, clickhouse.example.com",
            )
            bind_item_theme(
                "host_input", self.theme_manager.get_theme("input_enhanced")
            )

            add_text("Port Number:")
            add_input_text(
                default_value=DEFAULT_PORT,
                tag="port_input",
                hint="Default: 9000 (Native), 8123 (HTTP)",
            )
            bind_item_theme(
                "port_input", self.theme_manager.get_theme("input_enhanced")
            )

            add_text("Username:")
            add_input_text(
                default_value=DEFAULT_USERNAME,
                tag="username_input",
                hint="ClickHouse user account name",
            )
            bind_item_theme(
                "username_input", self.theme_manager.get_theme("input_enhanced")
            )

            add_text("Password:")
            add_input_text(
                password=True,
                tag="password_input",
                hint="Leave empty if no password required",
            )
            bind_item_theme(
                "password_input", self.theme_manager.get_theme("input_enhanced")
            )

            add_text("Database Name:")
            add_input_text(
                default_value=DEFAULT_DATABASE,
                tag="database_input",
                hint="Target database to connect to",
            )
            bind_item_theme(
                "database_input", self.theme_manager.get_theme("input_enhanced")
            )

            add_separator()

            # Connection status and control buttons
            with group(horizontal=True):
                add_button(
                    label="Connect",
                    callback=self.connect_callback,
                    tag="connect_button",
                    width=100,
                )
                bind_item_theme(
                    "connect_button", self.theme_manager.get_theme("button_primary")
                )
                add_button(
                    label="Disconnect",
                    callback=self.disconnect_callback,
                    tag="disconnect_button",
                    width=120,
                    enabled=False,
                )
                bind_item_theme(
                    "disconnect_button", self.theme_manager.get_theme("button_danger")
                )
                add_text("Disconnected", tag="connection_indicator", color=COLOR_ERROR)

            add_separator()

            # Close button
            add_button(
                label="Close", callback=lambda: delete_item("connection_settings_modal")
            )

            # Auto-refresh credentials when modal opens
            self.refresh_credentials_callback(None, None)

            # If we have stored credentials, populate the form
            if self.stored_credentials:
                self._set_form_values(self.stored_credentials)

    def run(self):
        """Run the application."""
        self.setup_ui()

        setup_dearpygui()
        show_viewport()

        # Just load credentials without auto-connecting
        self.auto_load_and_connect()

        # Show saved connections in the left panel
        self.table_browser_ui.show_saved_connections()

        start_dearpygui()
        destroy_context()
