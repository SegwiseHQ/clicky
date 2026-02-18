"""Connection management functionality for ClickHouse Client."""

import traceback

from dearpygui.dearpygui import *

from config import (
    COLOR_ERROR,
    COLOR_SUCCESS,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_DATABASE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_QUERY_RETRIES,
    DEFAULT_SEND_RECEIVE_TIMEOUT,
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
        async_worker=None,
    ):
        self.db_manager = db_manager
        self.credentials_manager = credentials_manager
        self.theme_manager = theme_manager
        self.async_worker = async_worker
        self.stored_credentials = None

        # Optional callbacks for additional functionality
        self.on_connect_success = None  # Called after successful connection

    def get_connection_parameters(self):
        """Get connection parameters, prioritizing form values over stored credentials."""
        print("[DEBUG] Attempting to get connection parameters")

        # Try to get values from form first
        host = UIHelpers.safe_get_value("host_input", None)
        port = UIHelpers.safe_get_value("port_input", None)
        username = UIHelpers.safe_get_value("username_input", None)
        password = UIHelpers.safe_get_value("password_input", None)
        database = UIHelpers.safe_get_value("database_input", None)

        # Check if we have valid form values (not None and not empty for required fields)
        form_has_values = (
            host is not None
            and host.strip() != ""
            and username is not None
            and username.strip() != ""
        )

        if form_has_values:
            print("[DEBUG] Using form values")
            # Use form values, with defaults for empty optional fields
            return {
                "host": host or DEFAULT_HOST,
                "port": port if port is not None else DEFAULT_PORT,
                "username": username or DEFAULT_USERNAME,
                "password": password or "",
                "database": database or DEFAULT_DATABASE,
            }
        elif self.stored_credentials:
            print("[DEBUG] Form values not available, using stored credentials")
            return {
                "host": self.stored_credentials.get("host", DEFAULT_HOST),
                "port": self.stored_credentials.get("port", DEFAULT_PORT),
                "username": self.stored_credentials.get("user", DEFAULT_USERNAME),
                "password": self.stored_credentials.get("password", ""),
                "database": self.stored_credentials.get("database", DEFAULT_DATABASE),
            }
        else:
            print(
                "[DEBUG] No form values or stored credentials available, using defaults"
            )
            return {
                "host": DEFAULT_HOST,
                "port": DEFAULT_PORT,
                "username": DEFAULT_USERNAME,
                "password": "",
                "database": DEFAULT_DATABASE,
            }

    def connect_callback(self, sender, data):
        """Handle database connection (non-blocking)."""
        UIHelpers.safe_configure_item("connect_button", enabled=False)
        StatusManager.show_status("Connecting... Please wait", error=False)

        try:
            params = self.get_connection_parameters()
            host = params["host"]
            port = params["port"]
            username = params["username"]
            password = params["password"]
            database = params["database"]

            print(
                f"[DEBUG] Connection parameters: host={host}, port={port}, username={username}, database={database}"
            )

            is_valid, error_msg = validate_connection_params(
                host, port, username, database
            )
            if not is_valid:
                raise ValueError(error_msg)

            print("[DEBUG] Connection parameters validated successfully")

        except Exception as e:
            # Validation failed on main thread — report immediately
            error_msg = f"Connection failed:\n{str(e)}"
            StatusManager.show_status(error_msg, error=True)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            if self.theme_manager:
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator",
                    self.theme_manager.create_connection_indicator_theme(False),
                )
            UIHelpers.safe_configure_item("connect_button", enabled=True)
            return

        port = int(port)

        if self.async_worker:
            self.async_worker.run_async(
                task=lambda: self.db_manager.connect(
                    host,
                    port,
                    username,
                    password,
                    database,
                    connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                    send_receive_timeout=DEFAULT_SEND_RECEIVE_TIMEOUT,
                    query_retries=DEFAULT_QUERY_RETRIES,
                ),
                on_done=self._on_connect_done,
                on_error=self._on_connect_error,
            )
        else:
            # Synchronous fallback
            success, message = self.db_manager.connect(
                host, port, username, password, database,
                connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                send_receive_timeout=DEFAULT_SEND_RECEIVE_TIMEOUT,
                query_retries=DEFAULT_QUERY_RETRIES,
            )
            self._on_connect_done((success, message))

    def _on_connect_done(self, result):
        """Called on main thread when connection attempt finishes."""
        success, message = result
        UIHelpers.safe_configure_item("connect_button", enabled=True)

        print(f"[DEBUG] Connection attempt result: success={success}, message={message}")

        if success:
            StatusManager.show_status(message)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_SUCCESS)
            if self.theme_manager:
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator",
                    self.theme_manager.create_connection_indicator_theme(True),
                )
            if self.on_connect_success:
                self.on_connect_success()
        else:
            error_msg = f"Connection failed:\n{message}"
            StatusManager.show_status(error_msg, error=True)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            if self.theme_manager:
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator",
                    self.theme_manager.create_connection_indicator_theme(False),
                )

    def _on_connect_error(self, e: Exception):
        """Called on main thread when connection raises an unexpected exception."""
        UIHelpers.safe_configure_item("connect_button", enabled=True)
        error_msg = f"Connection failed:\n{str(e)}\nDetails:\n{traceback.format_exc()}"
        StatusManager.show_status(error_msg, error=True)
        UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
        if self.theme_manager:
            UIHelpers.safe_bind_item_theme(
                "connection_indicator",
                self.theme_manager.create_connection_indicator_theme(False),
            )

    def test_credentials_callback(self, sender, data):
        """Test database credentials without establishing a persistent connection (non-blocking)."""
        UIHelpers.safe_configure_item("connect_button", enabled=False)
        StatusManager.show_status("Testing credentials... Please wait", error=False)

        try:
            params = self.get_connection_parameters()
            host = params["host"]
            port = params["port"]
            username = params["username"]
            password = params["password"]
            database = params["database"]

            print(
                f"[DEBUG] Testing credentials: host={host}, port={port}, username={username}, database={database}"
            )

            is_valid, error_msg = validate_connection_params(
                host, port, username, database
            )
            if not is_valid:
                raise ValueError(error_msg)

            print("[DEBUG] Connection parameters validated successfully")

        except Exception as e:
            error_msg = f"Credential test failed:\n{str(e)}"
            StatusManager.show_status(error_msg, error=True)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            if self.theme_manager:
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator",
                    self.theme_manager.create_connection_indicator_theme(False),
                )
            UIHelpers.safe_configure_item("connect_button", enabled=True)
            return

        port = int(port)

        if self.async_worker:
            self.async_worker.run_async(
                task=lambda: self.db_manager.test_credentials(
                    host,
                    port,
                    username,
                    password,
                    database,
                    connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                    send_receive_timeout=DEFAULT_SEND_RECEIVE_TIMEOUT,
                    query_retries=DEFAULT_QUERY_RETRIES,
                ),
                on_done=self._on_test_done,
                on_error=self._on_test_error,
            )
        else:
            success, message = self.db_manager.test_credentials(
                host, port, username, password, database,
                connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                send_receive_timeout=DEFAULT_SEND_RECEIVE_TIMEOUT,
                query_retries=DEFAULT_QUERY_RETRIES,
            )
            self._on_test_done((success, message))

    def _on_test_done(self, result):
        """Called on main thread when credential test finishes."""
        success, message = result
        UIHelpers.safe_configure_item("connect_button", enabled=True)

        print(f"[DEBUG] Credential test result: success={success}, message={message}")

        if success:
            StatusManager.show_status(f"✓ {message}", error=False)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_SUCCESS)
            if self.theme_manager:
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator",
                    self.theme_manager.create_connection_indicator_theme(True),
                )
        else:
            error_msg = f"Credential test failed:\n{message}"
            StatusManager.show_status(error_msg, error=True)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            if self.theme_manager:
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator",
                    self.theme_manager.create_connection_indicator_theme(False),
                )

    def _on_test_error(self, e: Exception):
        """Called on main thread when credential test raises an unexpected exception."""
        UIHelpers.safe_configure_item("connect_button", enabled=True)
        error_msg = f"Credential test failed:\n{str(e)}\nDetails:\n{traceback.format_exc()}"
        StatusManager.show_status(error_msg, error=True)
        UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
        if self.theme_manager:
            UIHelpers.safe_bind_item_theme(
                "connection_indicator",
                self.theme_manager.create_connection_indicator_theme(False),
            )

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
                    print("[DEBUG] Form populated with auto-loaded credentials")
                else:
                    print(
                        "[DEBUG] Form elements don't exist yet, credentials stored for later use"
                    )

                # No auto-connecting anymore
                print("[DEBUG] Credentials loaded but not auto-connecting")
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
