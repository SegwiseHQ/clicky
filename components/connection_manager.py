"""Connection management functionality for ClickHouse Client."""

import logging
import time
import traceback

from dearpygui.dearpygui import *

from components.status_manager import StatusManager
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
from utils import UIHelpers, validate_connection_params

logger = logging.getLogger(__name__)


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
        self.on_connect_failure = None  # Called after a failed connection attempt

    def _notify_connect_failure(self):
        """Notify UI components that the current connection attempt has ended."""
        if self.on_connect_failure:
            self.on_connect_failure()

    def _show_modal_status(self, message, error=False):
        """Show a status message in the connection modal's status area."""
        tag = "modal_status_text"
        if does_item_exist(tag):
            delete_item(tag, children_only=True)
            color = COLOR_ERROR if error else COLOR_SUCCESS
            text_tag = f"modal_status_{time.time()}"
            add_text(message, parent=tag, color=color, tag=text_tag, wrap=650)
            if self.theme_manager:
                theme_name = "error_text" if error else "success_text"
                bind_item_theme(text_tag, self.theme_manager.get_theme(theme_name))

    def get_connection_parameters(self):
        """Get connection parameters, prioritizing form values over stored credentials."""
        logger.debug("Attempting to get connection parameters")

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
            logger.debug("Using form values")
            # Use form values, with defaults for empty optional fields
            return {
                "host": host or DEFAULT_HOST,
                "port": port if port is not None else DEFAULT_PORT,
                "username": username or DEFAULT_USERNAME,
                "password": password or "",
                "database": database or DEFAULT_DATABASE,
            }
        elif self.stored_credentials:
            logger.debug("Form values not available, using stored credentials")
            return {
                "host": self.stored_credentials.get("host", DEFAULT_HOST),
                "port": self.stored_credentials.get("port", DEFAULT_PORT),
                "username": self.stored_credentials.get("user", DEFAULT_USERNAME),
                "password": self.stored_credentials.get("password", ""),
                "database": self.stored_credentials.get("database", DEFAULT_DATABASE),
            }
        else:
            logger.debug(
                "No form values or stored credentials available, using defaults"
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

            logger.debug(
                "Connection parameters: host=%s, port=%s, username=%s, database=%s",
                host,
                port,
                username,
                database,
            )

            is_valid, error_msg = validate_connection_params(
                host, port, username, database
            )
            if not is_valid:
                raise ValueError(error_msg)

            logger.debug("Connection parameters validated successfully")

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
            self._notify_connect_failure()
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
                host,
                port,
                username,
                password,
                database,
                connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                send_receive_timeout=DEFAULT_SEND_RECEIVE_TIMEOUT,
                query_retries=DEFAULT_QUERY_RETRIES,
            )
            self._on_connect_done((success, message))

    def _on_connect_done(self, result):
        """Called on main thread when connection attempt finishes."""
        success, message = result
        UIHelpers.safe_configure_item("connect_button", enabled=True)

        logger.debug(
            "Connection attempt result: success=%s, message=%s", success, message
        )

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
            self._notify_connect_failure()

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
        self._notify_connect_failure()

    def test_credentials_callback(self, sender, data):
        """Test database credentials without establishing a persistent connection (non-blocking)."""
        UIHelpers.safe_configure_item("connect_button", enabled=False)
        self._show_modal_status("Testing credentials... Please wait", error=False)

        try:
            params = self.get_connection_parameters()
            host = params["host"]
            port = params["port"]
            username = params["username"]
            password = params["password"]
            database = params["database"]

            logger.debug(
                "Testing credentials: host=%s, port=%s, username=%s, database=%s",
                host,
                port,
                username,
                database,
            )

            is_valid, error_msg = validate_connection_params(
                host, port, username, database
            )
            if not is_valid:
                raise ValueError(error_msg)

            logger.debug("Connection parameters validated successfully")

        except Exception as e:
            error_msg = f"Credential test failed:\n{str(e)}"
            self._show_modal_status(error_msg, error=True)
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
                host,
                port,
                username,
                password,
                database,
                connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                send_receive_timeout=DEFAULT_SEND_RECEIVE_TIMEOUT,
                query_retries=DEFAULT_QUERY_RETRIES,
            )
            self._on_test_done((success, message))

    def _on_test_done(self, result):
        """Called on main thread when credential test finishes."""
        success, message = result
        UIHelpers.safe_configure_item("connect_button", enabled=True)

        logger.debug("Credential test result: success=%s, message=%s", success, message)

        if success:
            self._show_modal_status(f"✓ {message}", error=False)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_SUCCESS)
            if self.theme_manager:
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator",
                    self.theme_manager.create_connection_indicator_theme(True),
                )
        else:
            error_msg = f"Credential test failed:\n{message}"
            self._show_modal_status(error_msg, error=True)
            UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
            if self.theme_manager:
                UIHelpers.safe_bind_item_theme(
                    "connection_indicator",
                    self.theme_manager.create_connection_indicator_theme(False),
                )

    def _on_test_error(self, e: Exception):
        """Called on main thread when credential test raises an unexpected exception."""
        UIHelpers.safe_configure_item("connect_button", enabled=True)
        error_msg = (
            f"Credential test failed:\n{str(e)}\nDetails:\n{traceback.format_exc()}"
        )
        self._show_modal_status(error_msg, error=True)
        UIHelpers.safe_configure_item("connection_indicator", color=COLOR_ERROR)
        if self.theme_manager:
            UIHelpers.safe_bind_item_theme(
                "connection_indicator",
                self.theme_manager.create_connection_indicator_theme(False),
            )

    def auto_load_and_connect(self):
        """Auto-load credentials without attempting connection on startup."""
        try:
            logger.debug("Starting auto_load_credentials")

            # Try to load the first available credentials
            success, credentials, message = (
                self.credentials_manager.load_credentials_legacy()
            )
            logger.debug(
                "Load credentials result: success=%s, message=%s", success, message
            )

            if credentials:
                logger.debug("Saved credentials found")

            if success and credentials:
                StatusManager.show_status(
                    "Credentials loaded automatically. Click 'Connect' to establish connection."
                )

                # Store the credentials for later use
                self.stored_credentials = credentials

                # Only populate the form if the form elements exist (modal is open)
                if does_item_exist("host_input"):
                    self.set_form_values(credentials)
                    logger.debug("Form populated with auto-loaded credentials")
                else:
                    logger.debug(
                        "Form elements do not exist yet; credentials stored for later use"
                    )

                # No auto-connecting anymore
                logger.debug("Credentials loaded but not auto-connecting")
            else:
                logger.debug("No credentials found or load failed")
                StatusManager.show_status(
                    "No saved credentials found. Please enter connection details.",
                    error=False,
                )

        except Exception as e:
            logger.debug("Auto-load exception: %s", e, exc_info=True)
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
