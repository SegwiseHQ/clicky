"""Main application class for ClickHouse Client."""

import time
import traceback

from dearpygui.dearpygui import *

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
from ui_components import QueryInterface, StatusManager, TableBrowser
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
        create_viewport(title=f"{icon_manager.get('database')} ClickHouse Client", width=MAIN_WINDOW_WIDTH, height=MAIN_WINDOW_HEIGHT)

        # Initialize theme manager and apply global theme
        self.theme_manager = ThemeManager()
        self.theme_manager.apply_global_theme()

        # Components
        self.db_manager = DatabaseManager()
        self.credentials_manager = CredentialsManager()
        self.table_browser = TableBrowser(self.db_manager, self.theme_manager)
        self.query_interface = QueryInterface(self.db_manager, self.theme_manager)
        self.data_explorer = DataExplorer(self.db_manager, self.theme_manager)

        # Track connection expansion state (initialized as expanded)
        self.connections_expanded = set(["current"])

        # Initialize stored credentials for auto-connect
        self.stored_credentials = None

        # Initialize status manager with theme
        StatusManager.set_theme_manager(self.theme_manager)

        # Set up callbacks
        self.table_browser.set_double_click_callback(self.data_explorer.open_explorer)
        self.table_browser.set_status_callback(StatusManager.show_status)
        self.query_interface.set_status_callback(StatusManager.show_status)

    def setup_ui(self):
        """Setup the main user interface."""
        # Main window setup
        with window(label="ClickHouse Client", tag="main_window", no_resize=True, no_move=True, no_collapse=True):
            # Add menu bar
            with menu_bar():
                with menu(label="File"):
                    add_menu_item(
                        label="Connection Settings",
                        callback=self.show_connection_settings_modal,
                    )
                    add_separator()
                    add_menu_item(
                        label="Connect",
                        callback=self.connect_callback,
                    )
                    add_menu_item(
                        label="Disconnect",
                        callback=self.disconnect_callback,
                    )

            with group(horizontal=True):
                # Left panel for tables - now fills full height to match right panels
                with child_window(label=f"{icon_manager.get('table')} Database Tables", width=TABLES_PANEL_WIDTH, height=-1, tag="tables_panel", border=True):
                    bind_item_theme("tables_panel", self.theme_manager.get_theme('tables_panel'))
                    add_text("Database Tables", color=(255, 255, 0), tag="database_tables_header")
                    bind_item_theme("database_tables_header", self.theme_manager.get_theme('header_text'))

                    # Add search bar for filtering table names
                    add_input_text(
                        tag="table_search",
                        hint="Search tables...",
                        callback=self.filter_tables_callback,
                        width=-1,
                    )
                    bind_item_theme(
                        "table_search", self.theme_manager.get_theme("input_enhanced")
                    )

                    # Add group for table list
                    add_group(tag="tables_list")
                    add_text("Connect to see tables", parent="tables_list", color=(128, 128, 128))

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
            bind_item_theme("status_window", self.theme_manager.get_theme('status_window'))
            add_text("Status:", color=(255, 255, 0))
            add_group(tag="status_text")
            StatusManager.show_status("Not connected", error=True)

    def _setup_query_section(self):
        """Setup the query input and results section."""
        with group(tag="query_section"):
            add_text(f"{icon_manager.get('query')} Query", color=(255, 255, 0))
            add_input_text(tag="query_input", multiline=True, width=-1, height=QUERY_INPUT_HEIGHT)
            bind_item_theme("query_input", self.theme_manager.get_theme('input_enhanced'))
            add_button(label=f"{icon_manager.get('query')} Run Query", callback=self.query_interface.run_query_callback, 
                      tag="run_query_button")
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
                bind_item_theme("explorer_title", self.theme_manager.get_theme('header_text'))
                add_spacer()  # Push the close button to the right
                add_button(label="Close Explorer", callback=self.data_explorer.close_explorer, 
                          tag="close_explorer_button", width=140, height=35)
                bind_item_theme("close_explorer_button", self.theme_manager.get_theme('button_danger'))

            # Filter section
            with collapsing_header(label=f"{icon_manager.get('filter')} Filters", default_open=False):
                add_text("Add filters for columns:")
                add_group(tag="explorer_filters")

            # Control buttons
            with group(horizontal=True):
                add_button(label="Clear Filters", callback=self.data_explorer.clear_filters)
                add_text("Limit:")
                add_input_text(tag="explorer_limit", default_value="100", width=80)
                add_button(label="Apply Limit", callback=lambda: self.data_explorer.refresh_data(StatusManager.show_status))

            add_separator()

            # Data window - fills remaining vertical space
            with child_window(label="Data", tag="explorer_data_window", border=True, height=-1):
                add_text("Loading data...", color=(128, 128, 128))

    def connect_callback(self, sender, data):
        """Handle database connection."""
        # Disable connect button and show connecting status
        UIHelpers.safe_configure_item("connect_button", enabled=False)
        StatusManager.show_status("Connecting... Please wait", error=False)

        try:
            # Get connection parameters - use stored credentials if available, otherwise form values
            if self.stored_credentials:
                print("[DEBUG] Using stored credentials for connection")
                host = self.stored_credentials.get("host", DEFAULT_HOST)
                port = self.stored_credentials.get("port", DEFAULT_PORT)
                username = self.stored_credentials.get("user", DEFAULT_USERNAME)
                password = self.stored_credentials.get("password", "")
                database = self.stored_credentials.get("database", DEFAULT_DATABASE)
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
            is_valid, error_msg = validate_connection_params(host, port, username, database)
            if not is_valid:
                raise ValueError(error_msg)

            print("[DEBUG] Connection parameters validated successfully")

            # Attempt connection
            success, message = self.db_manager.connect(host, int(port), username, password, database)
            print(
                f"[DEBUG] Connection attempt result: success={success}, message={message}"
            )

            if success:
                StatusManager.show_status(message)
                UIHelpers.safe_configure_item("connection_indicator", color=COLOR_SUCCESS)
                # Apply connected theme to connection indicator
                connected_theme = self.theme_manager.create_connection_indicator_theme(True)
                UIHelpers.safe_bind_item_theme("connection_indicator", connected_theme)

                self.save_credentials_callback(None, None)  # Auto-save on successful connection

                # Automatically list tables after successful connection
                # Use our custom filtering to display connection and tables
                current_search = UIHelpers.safe_get_value("table_search", "")
                self.filter_tables_callback(None, current_search)

                # Update button states
                UIHelpers.safe_configure_item("connect_button", enabled=True)
                UIHelpers.safe_configure_item("disconnect_button", enabled=True)
            else:
                raise Exception(message)

        except Exception as e:
            error_msg = f"Connection failed:\n{str(e)}"
            if hasattr(e, '__traceback__'):
                error_msg += f"\nDetails:\n{traceback.format_exc()}"
            StatusManager.show_status(error_msg, error=True)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            # Apply disconnected theme to connection indicator
            disconnected_theme = self.theme_manager.create_connection_indicator_theme(False)
            UIHelpers.safe_bind_item_theme("connection_indicator", disconnected_theme)
        finally:
            # Re-enable connect button
            UIHelpers.safe_configure_item("connect_button", enabled=True)

    def disconnect_callback(self, sender, data):
        """Handle database disconnection."""
        try:
            message = self.db_manager.disconnect()

            # Update UI
            self.table_browser.clear_tables()
            self.data_explorer.close_explorer()

            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            # Apply disconnected theme to connection indicator
            disconnected_theme = self.theme_manager.create_connection_indicator_theme(False)
            UIHelpers.safe_bind_item_theme("connection_indicator", disconnected_theme)

            StatusManager.show_status(message)

            # Update button states
            UIHelpers.safe_configure_item("connect_button", enabled=True)
            UIHelpers.safe_configure_item("disconnect_button", enabled=False)

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

        except Exception as e:
            StatusManager.show_status(f"Error saving credentials: {str(e)}", error=True)

    def load_credentials_callback(self, sender, data):
        """Load saved connection credentials (legacy - loads first available)."""
        try:
            success, credentials, message = self.credentials_manager.load_credentials_legacy()

            if success and credentials:
                self._set_form_values(credentials)

            StatusManager.show_status(message, error=not success)

        except Exception as e:
            StatusManager.show_status(f"Error loading credentials: {str(e)}", error=True)

    def load_selected_credentials_callback(self, sender, data):
        """Load credentials selected from dropdown."""
        try:
            selected_name = UIHelpers.safe_get_value("credentials_combo", "")
            if not selected_name:
                return

            success, credentials, message = self.credentials_manager.load_credentials(selected_name)

            if success and credentials:
                self._set_form_values(credentials)
                StatusManager.show_status(message, error=False)
            else:
                StatusManager.show_status(message, error=True)

        except Exception as e:
            StatusManager.show_status(f"Error loading credentials: {str(e)}", error=True)

    def refresh_credentials_callback(self, sender, data):
        """Refresh the credentials dropdown list."""
        try:
            names = self.credentials_manager.get_credential_names()
            UIHelpers.safe_configure_item("credentials_combo", items=names)

            if names:
                StatusManager.show_status(f"Found {len(names)} saved credential sets", error=False)
            else:
                StatusManager.show_status("No saved credentials found", error=False)

        except Exception as e:
            StatusManager.show_status(f"Error refreshing credentials: {str(e)}", error=True)

    def delete_credentials_callback(self, sender, data):
        """Delete selected credentials."""
        try:
            selected_name = UIHelpers.safe_get_value("credentials_combo", "")
            if not selected_name:
                StatusManager.show_status("Please select credentials to delete", error=True)
                return

            success, message = self.credentials_manager.delete_credentials(selected_name)
            StatusManager.show_status(message, error=not success)

            if success:
                self.refresh_credentials_callback(None, None)
                # Clear form if deleted credentials were loaded
                current_name = UIHelpers.safe_get_value("credential_name_input", "")
                if current_name == selected_name:
                    self._clear_form_values()

        except Exception as e:
            StatusManager.show_status(f"Error deleting credentials: {str(e)}", error=True)

    def filter_tables_callback(self, sender, app_data):
        """Filter tables in the left panel based on the search query."""
        search_query = app_data.strip().lower()
        delete_item("tables_list", children_only=True)

        if not self.db_manager.is_connected:
            add_text(
                "Connect to see tables", parent="tables_list", color=(128, 128, 128)
            )
            return

        # Get connection name for the parent node
        connection_name = self._get_connection_display_name()

        # Get all table names and filter them
        all_tables = self.db_manager.get_tables()
        filtered_tables = [
            table for table in all_tables if search_query in table.lower()
        ]

        # Check if tables should be visible based on expand/collapse state
        is_expanded = "current" in self.connections_expanded

        # Get the appropriate visual indicator for expanded/collapsed state
        expand_icon = "[-]" if is_expanded else "[+]"

        # Add connection name as parent with clickable button and indicator
        connection_button = f"connection_header_{int(time.time() * 1000)}"
        add_button(
            label=f"{expand_icon} {connection_name}",
            parent="tables_list",
            callback=self.toggle_connection_callback,
            width=-1,
            height=30,
            tag=connection_button,
        )

        # Apply the table_button theme to the connection button
        bind_item_theme(connection_button, self.theme_manager.get_theme("table_button"))

        # Only show tables if connection is expanded and we have tables
        if is_expanded:
            if not filtered_tables:
                # Display message when no tables match search criteria
                add_text("  No tables found", parent="tables_list", color=(255, 0, 0))
            else:
                # Add filtered tables as children with indentation
                for table in filtered_tables:
                    add_button(
                        label=f"  {table}",  # Indent to show hierarchy
                        parent="tables_list",
                        callback=self.select_table_callback,
                    )

    def select_table_callback(self, sender, app_data):
        """Handle table selection from the filtered list."""
        selected_table = get_item_label(sender)

        # Remove the indentation spaces if present
        if selected_table.startswith("  "):
            selected_table = selected_table.strip()

        self.data_explorer.open_explorer(selected_table, StatusManager.show_status)

    def _get_connection_display_name(self) -> str:
        """Get a formatted display name for the current connection."""
        if not self.db_manager.is_connected or not self.db_manager.connection_info:
            return "Not Connected"

        # Try to find the saved credential name for this connection
        connection_name = self._find_credential_name_for_connection()

        # If we found a saved name, use it as the display name
        if connection_name:
            # Use the saved name directly without emojis
            return connection_name

        # Fallback to technical connection info if no saved name is found
        info = self.db_manager.connection_info
        host = info.get("host", "Unknown")
        port = info.get("port", "Unknown")
        database = info.get("database", "Unknown")

        # Create a readable connection name without emojis
        if "clickhouse.cloud" in str(host).lower():
            # For cloud connections, show a cleaner name
            return f"{host}/{database}"
        elif host in ["localhost", "127.0.0.1"]:
            # For local connections
            return f"Local ({database})"
        else:
            # For other remote connections
            return f"{host}:{port}/{database}"

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
        """Auto-load credentials and attempt connection on startup."""
        try:
            print("[DEBUG] Starting auto_load_and_connect")

            # Refresh credentials list first
            self.refresh_credentials_callback(None, None)

            # Try to load the first available credentials
            success, credentials, message = self.credentials_manager.load_credentials_legacy()
            print(
                f"[DEBUG] Load credentials result: success={success}, message={message}"
            )

            if credentials:
                print(f"[DEBUG] Credentials found: {credentials}")

            if success and credentials:
                StatusManager.show_status("Credentials loaded automatically on startup")

                # Store the credentials for later use
                self.stored_credentials = credentials

                # Only auto-connect if we have valid credentials
                if all([credentials["host"], credentials["port"], credentials["user"], credentials["database"]]):
                    print("[DEBUG] Valid credentials found, attempting auto-connect")
                    print(
                        f"[DEBUG] Auto-connect credentials: host={credentials['host']}, port={credentials['port']}, user={credentials['user']}, database={credentials['database']}"
                    )
                    StatusManager.show_status("Attempting automatic connection...")
                    self.connect_callback(None, None)
                else:
                    print(f"[DEBUG] Invalid credentials: {credentials}")
            else:
                print("[DEBUG] No credentials found or load failed")
                StatusManager.show_status("No saved credentials found", error=False)

        except Exception as e:
            print(f"[DEBUG] Auto-connect exception: {str(e)}")
            StatusManager.show_status(f"Auto-connect failed: {str(e)}", error=True)

    def show_connection_settings_modal(self):
        """Show a modal dialog for connection settings."""
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
                    tag="save_as_button",
                )
                bind_item_theme(
                    "save_as_button", self.theme_manager.get_theme("button_secondary")
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

        # Auto-connect after UI is fully initialized
        self.auto_load_and_connect()

        start_dearpygui()
        destroy_context()

    def _find_credential_name_for_connection(self) -> str:
        """Find the saved credential name that matches the current connection."""
        if not self.db_manager.is_connected or not self.db_manager.connection_info:
            return ""

        # Get current connection info
        current = self.db_manager.connection_info
        current_host = current.get("host", "")
        current_port = str(current.get("port", ""))
        current_user = current.get("username", "")  # DatabaseManager uses "username"
        current_db = current.get("database", "")

        print(
            f"[DEBUG] Current connection: host={current_host}, port={current_port}, user={current_user}, db={current_db}"
        )

        # Get all credential names
        credential_names = self.credentials_manager.get_credential_names()
        print(f"[DEBUG] Available credential names: {credential_names}")

        # Check each saved credential for a match
        for name in credential_names:
            success, cred, _ = self.credentials_manager.load_credentials(name)
            if success:
                saved_host = cred.get("host", "")
                saved_port = str(cred.get("port", ""))
                saved_user = cred.get("user", "")  # CredentialsManager uses "user"
                saved_db = cred.get("database", "")

                print(
                    f"[DEBUG] Comparing with '{name}': host={saved_host}, port={saved_port}, user={saved_user}, db={saved_db}"
                )

                # Check if this credential matches our current connection
                if (
                    saved_host == current_host
                    and saved_port == current_port
                    and saved_user == current_user
                    and saved_db == current_db
                ):
                    print(f"[DEBUG] Found matching credential: {name}")
                    return name

        print("[DEBUG] No matching credential found")
        # If we get here, no matching credential was found
        return ""

    def toggle_connection_callback(self, sender, app_data):
        """Toggle the visibility of tables under a connection."""
        if "current" in self.connections_expanded:
            # If expanded, collapse it
            self.connections_expanded.remove("current")
        else:
            # If collapsed, expand it
            self.connections_expanded.add("current")

        # Re-filter tables with the current search query to update display
        current_search = UIHelpers.safe_get_value("table_search", "")
        self.filter_tables_callback(None, current_search)
