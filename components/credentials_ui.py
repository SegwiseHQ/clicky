"""Credentials management UI components for ClickHouse Client."""

from dearpygui.dearpygui import *

from config import DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME
from credentials_manager import CredentialsManager
from ui_components import StatusManager
from utils import UIHelpers


class CredentialsUI:
    """Manages credentials-related UI operations."""

    def __init__(
        self,
        credentials_manager: CredentialsManager,
        connection_manager=None,
        theme_manager=None,
    ):
        self.credentials_manager = credentials_manager
        self.connection_manager = connection_manager
        self.theme_manager = theme_manager

        # Optional callbacks for UI updates
        self.on_credentials_saved = None  # Called after credentials are saved

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

                # Call callback if provided (for UI updates)
                if self.on_credentials_saved:
                    self.on_credentials_saved()

        except Exception as e:
            StatusManager.show_status(f"Error saving credentials: {str(e)}", error=True)

    def load_selected_credentials_callback(self, sender, data):
        """Load credentials selected from dropdown."""
        try:
            selected_name = UIHelpers.safe_get_value("credentials_combo", "")
            if not selected_name:
                return

            success, credentials, message = self.credentials_manager.load_credentials(
                selected_name
            )

            if success and credentials and self.connection_manager:
                self.connection_manager.set_form_values(credentials)
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
                if current_name == selected_name and self.connection_manager:
                    self.connection_manager.clear_form_values()

        except Exception as e:
            StatusManager.show_status(
                f"Error deleting credentials: {str(e)}", error=True
            )

    def show_connection_settings_modal(self):
        """Show a modal dialog for connection settings."""
        # Close existing modal if it exists
        try:
            delete_item("connection_settings_modal")
        except:
            pass  # Modal doesn't exist, which is fine

        with window(
            label="Connection Settings",
            modal=True,
            tag="connection_settings_modal",
            width=700,
            height=500,
        ):
            # Credential management section
            add_text("Saved Connections:", color=(220, 220, 220))
            add_combo(
                label="",
                tag="credentials_combo",
                callback=self.load_selected_credentials_callback,
                width=250,
            )
            if self.theme_manager:
                bind_item_theme(
                    "credentials_combo",
                    self.theme_manager.get_theme("connection_combo"),
                )

            add_text("Save New Connection:")
            with group(horizontal=True):
                add_input_text(
                    tag="credential_name_input", width=200, hint="Connection name"
                )
                if self.theme_manager:
                    bind_item_theme(
                        "credential_name_input",
                        self.theme_manager.get_theme("connection_input"),
                    )
                add_button(
                    label="Save As",
                    callback=self.save_named_credentials_callback,
                    width=80,
                    tag="save_as_button",
                )
                if self.theme_manager:
                    bind_item_theme(
                        "save_as_button", self.theme_manager.get_theme("button_success")
                    )
                add_button(
                    label="Delete",
                    callback=self.delete_credentials_callback,
                    width=80,
                    tag="delete_button",
                )
                if self.theme_manager:
                    bind_item_theme(
                        "delete_button", self.theme_manager.get_theme("button_danger")
                    )

            add_separator()

            # Connection parameters with grouped layout for reduced height
            # Host and Port on same row
            add_text("Server Connection:")
            with group(horizontal=True):
                with group():
                    add_text("Host/Server Address:")
                    add_input_text(
                        default_value=DEFAULT_HOST,
                        tag="host_input",
                        hint="e.g., localhost, 192.168.1.100, clickhouse.example.com",
                        width=400,
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            "host_input",
                            self.theme_manager.get_theme("connection_input"),
                        )

                add_spacing(count=10)

                with group():
                    add_text("Port:")
                    add_input_text(
                        default_value=DEFAULT_PORT,
                        tag="port_input",
                        hint="Default: 9000 (Native), 8123 (HTTP)",
                        width=120,
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            "port_input",
                            self.theme_manager.get_theme("connection_input"),
                        )

            # Username and Password on same row
            with group(horizontal=True):
                with group():
                    add_text("Username:")
                    add_input_text(
                        default_value=DEFAULT_USERNAME,
                        tag="username_input",
                        hint="ClickHouse user account name",
                        width=250,
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            "username_input",
                            self.theme_manager.get_theme("connection_input"),
                        )

                add_spacing(count=10)

                with group():
                    add_text("Password:")
                    add_input_text(
                        password=True,
                        tag="password_input",
                        hint="Leave empty if no password required",
                        width=250,
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            "password_input",
                            self.theme_manager.get_theme("connection_input"),
                        )

            # Database on its own row (full width)
            add_text("Database Name:")
            add_input_text(
                default_value=DEFAULT_DATABASE,
                tag="database_input",
                hint="Target database to connect to",
            )
            if self.theme_manager:
                bind_item_theme(
                    "database_input", self.theme_manager.get_theme("connection_input")
                )

            add_separator()

            # Connection status and control buttons
            with group(horizontal=True):
                add_button(
                    label="Test Connection",
                    callback=(
                        self.connection_manager.test_credentials_callback
                        if self.connection_manager
                        else None
                    ),
                    tag="connect_button",
                    width=130,
                )
                if self.theme_manager:
                    bind_item_theme(
                        "connect_button", self.theme_manager.get_theme("button_primary")
                    )

            # Auto-refresh credentials when modal opens
            self.refresh_credentials_callback(None, None)

            # If we have stored credentials, populate the form
            if self.connection_manager and self.connection_manager.stored_credentials:
                self.connection_manager.set_form_values(
                    self.connection_manager.stored_credentials
                )
