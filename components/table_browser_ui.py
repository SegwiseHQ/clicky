"""Table browser UI component for ClickHouse Client."""

import time
from typing import Callable, Dict, Optional, Set

from dearpygui.dearpygui import *

from config import COLOR_ERROR, DOUBLE_CLICK_THRESHOLD
from utils import UIHelpers


class TableBrowserUI:
    """Manages table browsing and filtering UI functionality."""

    def __init__(self, db_manager, credentials_manager, theme_manager=None):
        """Initialize table browser UI component."""
        self.db_manager = db_manager
        self.credentials_manager = credentials_manager
        self.theme_manager = theme_manager

        # Track connection expansion state (initialized as collapsed)
        self.connections_expanded: Set[str] = set()

        # Track currently selected table
        self.selected_table = None

        # Single-click callback for explorer opening
        self.double_click_callback: Optional[Callable[[str], None]] = None

    def set_double_click_callback(self, callback: Callable[[str], None]):
        """Set callback for table single-click events to open explorer."""
        self.double_click_callback = callback

    def filter_tables_callback(self, sender, app_data):
        """Filter tables in the left panel based on the search query."""
        # If this was triggered by search input (not programmatic call)
        # get current scroll position only when it's a user-initiated search
        preserve_scroll = sender is not None
        if preserve_scroll:
            try:
                scroll_y = get_y_scroll("tables_panel")
            except:
                scroll_y = 0

        search_query = app_data.strip().lower()
        delete_item("tables_list", children_only=True)

        if not self.db_manager.is_connected:
            # If not connected, show all saved connections
            self.show_saved_connections()
            return

        # Get connection name for the parent node
        connection_name = self._get_connection_display_name()

        # Check if tables should be visible based on expand/collapse state
        is_expanded = "current" in self.connections_expanded

        # If connection is collapsed, simply show all saved connections
        if not is_expanded:
            self.show_saved_connections()
            return

        # Get all table names and filter them
        all_tables = self.db_manager.get_tables()
        filtered_tables = [
            table for table in all_tables if search_query in table.lower()
        ]

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
        if self.theme_manager:
            bind_item_theme(
                connection_button, self.theme_manager.get_theme("selected_table_button")
            )

        # Show tables if we have any matching the filter
        if not filtered_tables:
            # Display message when no tables match search criteria
            add_text("  No tables found", parent="tables_list", color=(255, 0, 0))
        else:
            # Add filtered tables as children with indentation
            for table in filtered_tables:
                table_button = add_button(
                    label=f"  {table}",  # Indent to show hierarchy
                    parent="tables_list",
                    callback=self.select_table_callback,
                    tag=f"table_button_{table}",
                )

                # Add right-click context menu for copying table name
                with popup(
                    parent=f"table_button_{table}",
                    mousebutton=1,
                    tag=f"context_menu_{table}",
                ):
                    add_menu_item(
                        label="Copy Table Name",
                        callback=self._copy_table_name_callback,
                        user_data=table,
                    )

                # Apply appropriate theme based on selection state
                if table == self.selected_table:
                    # Apply selected table theme
                    if self.theme_manager:
                        bind_item_theme(
                            f"table_button_{table}",
                            self.theme_manager.get_theme("selected_table_button"),
                        )
                else:
                    # Apply regular table button theme
                    if self.theme_manager:
                        bind_item_theme(
                            f"table_button_{table}",
                            self.theme_manager.get_theme("table_button"),
                        )

        # Only show other connections section if there are tables displayed
        if filtered_tables:
            # Add a separator before showing other connections
            add_separator(parent="tables_list")
            add_text("Other Connections:", parent="tables_list", color=(255, 193, 7))

            # Show other available connections below the table list
            credential_names = self.credentials_manager.get_credential_names()
            current_connection_name = self._find_credential_name_for_connection()

            # Filter out the current connection from the list
            other_connections = [
                name for name in credential_names if name != current_connection_name
            ]

            if other_connections:
                for name in other_connections:
                    connection_button = f"connection_{name}_{int(time.time() * 1000)}"
                    add_button(
                        label=f"{name}",
                        parent="tables_list",
                        callback=self.connect_to_saved_callback,
                        user_data=name,
                        width=-1,
                        height=30,
                        tag=connection_button,
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            connection_button,
                            self.theme_manager.get_theme("table_button"),
                        )
            else:
                add_text(
                    "  No other connections",
                    parent="tables_list",
                    color=(128, 128, 128),
                )

        # If this was a search triggered by user input, restore the scroll position
        if preserve_scroll:
            try:
                set_y_scroll("tables_panel", scroll_y)
            except:
                pass

    def select_table_callback(self, sender, app_data):
        """Handle table selection and single-click explorer opening."""
        # Extract table name from sender tag
        table_name = sender.replace("table_button_", "")

        # Update selected table for visual highlighting
        old_selected = self.selected_table
        self.selected_table = table_name

        # Get current scroll position before refreshing display
        try:
            scroll_y = get_y_scroll("tables_panel")
        except:
            scroll_y = 0

        # Refresh the display to update themes
        current_search = UIHelpers.safe_get_value("table_search", "")
        self.filter_tables_callback(None, current_search)

        # Restore scroll position after refresh
        try:
            set_y_scroll("tables_panel", scroll_y)
        except:
            pass

        # Open explorer on single-click
        if self.double_click_callback:
            self.double_click_callback(table_name)

    def toggle_connection_callback(self, sender, app_data):
        """Toggle the visibility of tables under a connection."""
        # Get current scroll position before changing state
        try:
            scroll_y = get_y_scroll("tables_panel")
        except:
            scroll_y = 0

        if "current" in self.connections_expanded:
            # If expanded, collapse it
            self.connections_expanded.remove("current")

            # When collapsed, show all saved connections
            self.show_saved_connections()
        else:
            # If collapsed, expand it
            self.connections_expanded.add("current")

            # Re-filter tables with the current search query to update display
            current_search = UIHelpers.safe_get_value("table_search", "")
            self.filter_tables_callback(None, current_search)

        # Restore scroll position after refresh
        try:
            set_y_scroll("tables_panel", scroll_y)
        except:
            pass

    def show_saved_connections(self):
        """Show all saved connections in the left panel."""
        # Clear the left panel
        delete_item("tables_list", children_only=True)

        # Get list of all saved credential names
        credential_names = self.credentials_manager.get_credential_names()

        if not credential_names:
            add_text(
                "No saved connections found", parent="tables_list", color=(255, 128, 0)
            )
            return

        # Find the currently active connection name, if any
        current_name = ""
        if self.db_manager.is_connected and self.db_manager.connection_info:
            current_name = self._find_credential_name_for_connection()

        # Display each saved connection as a button
        for name in credential_names:
            connection_button = f"connection_{name}_{int(time.time() * 1000)}"

            # Check if this is the currently active connection
            is_active = name == current_name

            # Create button with appropriate icon
            connection_status = "[Active] " if is_active else ""
            add_button(
                label=f"{connection_status}{name}",
                parent="tables_list",
                callback=self.connect_to_saved_callback,
                user_data=name,  # Pass the credential name as user_data
                width=-1,
                height=30,
                tag=connection_button,
            )

            # Apply theme based on active status
            if is_active and self.db_manager.is_connected:
                if self.theme_manager:
                    bind_item_theme(
                        connection_button,
                        self.theme_manager.get_theme("selected_table_button"),
                    )
            else:
                if self.theme_manager:
                    bind_item_theme(
                        connection_button, self.theme_manager.get_theme("table_button")
                    )

    def connect_to_saved_callback(self, sender, app_data, user_data):
        """Handle clicking on a saved connection to connect to it."""
        # Import here to avoid circular imports
        from ui_components import StatusManager

        # Get connection name from user_data
        connection_name = user_data

        # Check if we're already connected to this connection
        current_connection_name = ""
        if self.db_manager.is_connected:
            current_connection_name = self._find_credential_name_for_connection()

        # If already connected to this connection, just toggle expansion
        if current_connection_name == connection_name and self.db_manager.is_connected:
            # Toggle the connection expansion state
            if "current" in self.connections_expanded:
                self.connections_expanded.remove("current")
                self.show_saved_connections()
            else:
                self.connections_expanded.add("current")
                current_search = UIHelpers.safe_get_value("table_search", "")
                self.filter_tables_callback(None, current_search)
            return

        # Show connecting status
        StatusManager.show_status(
            f"Connecting to {connection_name}... Please wait", error=False
        )

        try:
            # Load credentials
            success, credentials, message = self.credentials_manager.load_credentials(
                connection_name
            )

            if not success or not credentials:
                StatusManager.show_status(
                    f"Failed to load credentials: {message}", error=True
                )
                return

            # Check if we're already connected to the same database with the same credentials
            # but the credential name is different (this can happen with duplicate saved connections)
            should_reconnect = True
            if self.db_manager.is_connected:
                current = self.db_manager.connection_info
                current_host = current.get("host", "")
                current_port = str(current.get("port", ""))
                current_user = current.get("username", "")
                current_db = current.get("database", "")

                # Check if the new connection matches the current one
                saved_host = credentials.get("host", "")
                saved_port = str(credentials.get("port", ""))
                saved_user = credentials.get(
                    "user", ""
                )  # CredentialsManager uses "user"
                saved_db = credentials.get("database", "")

                if (
                    saved_host == current_host
                    and saved_port == current_port
                    and saved_user == current_user
                    and saved_db == current_db
                ):
                    # We're already connected to this database, no need to reconnect
                    should_reconnect = False
                    StatusManager.show_status(
                        f"Already connected to {connection_name}", error=False
                    )

                    # Make sure the connection is expanded
                    self.connections_expanded.add("current")

                    # Refresh the table list to show the tables
                    current_search = UIHelpers.safe_get_value("table_search", "")
                    self.filter_tables_callback(None, current_search)
                    return

            # If we need to reconnect, disconnect first
            if should_reconnect and self.db_manager.is_connected:
                self.db_manager.disconnect()

            # For actual connection, we need to trigger the connection callback
            # This will be handled by the main app
            if hasattr(self, "connection_callback"):
                # Store loaded credentials for connection
                self.stored_credentials = credentials
                self.connection_callback(None, None)

                # After connecting successfully, make sure the connection is expanded
                self.connections_expanded.add("current")

                # Refresh the table list to show the tables
                current_search = UIHelpers.safe_get_value("table_search", "")
                self.filter_tables_callback(None, current_search)

        except Exception as e:
            error_msg = f"Failed to connect to {connection_name}: {str(e)}"
            StatusManager.show_status(error_msg, error=True)

    def _copy_table_name_callback(self, sender, app_data, user_data):
        """Copy table name to clipboard when context menu item is clicked."""
        try:
            table_name = user_data if user_data else ""

            # Use DearPyGui's set_clipboard_text to copy to system clipboard
            set_clipboard_text(table_name)

            # Show feedback through status manager (if available)
            try:
                from ui_components import StatusManager

                StatusManager.show_status(
                    f"Table name copied to clipboard: {table_name}", error=False
                )
            except Exception:
                # Fallback: print to console if StatusManager isn't available
                print(f"Table name copied to clipboard: {table_name}")

        except Exception as e:
            try:
                from ui_components import StatusManager

                StatusManager.show_status(
                    f"Error copying table name: {str(e)}", error=True
                )
            except Exception:
                # Fallback: print to console if StatusManager isn't available
                print(f"Error copying table name: {str(e)}")

    def clear_connection_state(self):
        """Clear connection-related state during disconnection."""
        self.connections_expanded.clear()
        self.selected_table = None

    def _get_connection_display_name(self) -> str:
        """Get a display name for the current connection."""
        if not self.db_manager.is_connected or not self.db_manager.connection_info:
            return "No Connection"

        # Try to find a matching credential name
        credential_name = self._find_credential_name_for_connection()
        if credential_name:
            return credential_name

        # If no matching credential found, construct a name from connection info
        connection_info = self.db_manager.connection_info
        host = connection_info.get("host", "unknown")
        database = connection_info.get("database", "unknown")
        return f"{host}/{database}"

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

        # Get all credential names
        credential_names = self.credentials_manager.get_credential_names()

        # Check each saved credential for a match
        matching_credentials = []

        for name in credential_names:
            success, cred, _ = self.credentials_manager.load_credentials(name)
            if success:
                saved_host = cred.get("host", "")
                saved_port = str(cred.get("port", ""))
                saved_user = cred.get("user", "")  # CredentialsManager uses "user"
                saved_db = cred.get("database", "")

                # Check if this credential matches our current connection
                if (
                    saved_host == current_host
                    and saved_port == current_port
                    and saved_user == current_user
                    and saved_db == current_db
                ):
                    matching_credentials.append(name)

        # If we found multiple matches, return the first one
        if matching_credentials:
            return matching_credentials[0]

        # If we get here, no matching credential was found
        return ""
