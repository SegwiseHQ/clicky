"""Connection management functionality for ClickHouse Client."""

import traceback

from dearpygui.dearpygui import *

from config import (
    COLOR_ERROR,
    COLOR_SUCCESS,
    DEFAULT_DATABASE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
)
from credentials_manager import CredentialsManager
from database import DatabaseManager
from ui_components import StatusManager
from utils import UIHelpers, validate_connection_params


class ConnectionManager:
    """Manages database connections and related operations."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        credentials_manager: CredentialsManager,
        theme_manager=None,
    ):
        self.db_manager = db_manager
        self.credentials_manager = credentials_manager
        self.theme_manager = theme_manager
        self.stored_credentials = None

        # Optional callbacks for additional functionality
        self.on_connect_success = None  # Called after successful connection
        self.on_disconnect = None  # Called after disconnection

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
                if self.theme_manager:
                    connected_theme = (
                        self.theme_manager.create_connection_indicator_theme(True)
                    )
                    UIHelpers.safe_bind_item_theme(
                        "connection_indicator", connected_theme
                    )

                # Update button states
                UIHelpers.safe_configure_item("connect_button", enabled=True)
                UIHelpers.safe_configure_item("disconnect_button", enabled=True)

                # Call success callback if provided
                if self.on_connect_success:
                    self.on_connect_success()
            else:
                raise Exception(message)

        except Exception as e:
            error_msg = f"Connection failed:\n{str(e)}"
            if hasattr(e, "__traceback__"):
                error_msg += f"\nDetails:\n{traceback.format_exc()}"
            StatusManager.show_status(error_msg, error=True)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            # Apply disconnected theme to connection indicator
            if self.theme_manager:
                disconnected_theme = (
                    self.theme_manager.create_connection_indicator_theme(False)
                )
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator", disconnected_theme
                )
        finally:
            # Re-enable connect button
            UIHelpers.safe_configure_item("connect_button", enabled=True)

    def disconnect_callback(self, sender, data):
        """Handle database disconnection."""
        try:
            message = self.db_manager.disconnect()

            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            # Apply disconnected theme to connection indicator
            if self.theme_manager:
                disconnected_theme = (
                    self.theme_manager.create_connection_indicator_theme(False)
                )
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator", disconnected_theme
                )

            StatusManager.show_status(message)

            # Update button states
            UIHelpers.safe_configure_item("connect_button", enabled=True)
            UIHelpers.safe_configure_item("disconnect_button", enabled=False)

            # Call disconnect callback if provided
            if self.on_disconnect:
                self.on_disconnect()

        except Exception as e:
            StatusManager.show_status(f"Error during disconnect: {str(e)}", error=True)

    def auto_load_and_connect(self):
        """Auto-load credentials without attempting connection on startup."""
        try:
            print("[DEBUG] Starting auto_load_credentials")

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

                # Only populate the form if the form elements exist (modal is open)
                if does_item_exist("host_input"):
                    self.set_form_values(credentials)
                    print(f"[DEBUG] Form populated with auto-loaded credentials")
                else:
                    print(
                        f"[DEBUG] Form elements don't exist yet, credentials stored for later use"
                    )

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

    def set_form_values(self, credentials: dict):
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

    def clear_form_values(self):
        """Clear all form values."""
        UIHelpers.safe_configure_item("host_input", default_value=DEFAULT_HOST)
        UIHelpers.safe_configure_item("port_input", default_value=DEFAULT_PORT)
        UIHelpers.safe_configure_item("username_input", default_value=DEFAULT_USERNAME)
        UIHelpers.safe_configure_item("password_input", default_value="")
        UIHelpers.safe_configure_item("database_input", default_value=DEFAULT_DATABASE)
