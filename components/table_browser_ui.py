"""Table browser UI component for ClickHouse Client."""

import time
from typing import Callable, Optional, Set

from dearpygui.dearpygui import *

from utils import UIHelpers


class TableBrowserUI:
    """Manages table browsing and filtering UI functionality."""

    def __init__(
        self,
        db_manager,
        credentials_manager,
        theme_manager=None,
        connection_manager=None,
        async_worker=None,
    ):
        """Initialize table browser UI component."""
        self.db_manager = db_manager
        self.credentials_manager = credentials_manager
        self.theme_manager = theme_manager
        self.connection_manager = connection_manager
        self.async_worker = async_worker

        # Track connection expansion state (initialized as collapsed)
        self.connections_expanded: Set[str] = set()

        # Track currently selected table
        self.selected_table = None

        # Single-click callback for explorer opening
        self.double_click_callback: Optional[Callable[[str], None]] = None

        # Sequence number to discard stale async table-list results
        self._tables_seq = 0

    def set_double_click_callback(self, callback: Callable[[str], None]):
        """Set callback for table single-click events to open explorer."""
        self.double_click_callback = callback

    def filter_tables_callback(self, sender, app_data):
        """Filter tables in the left panel based on the search query (non-blocking)."""
        preserve_scroll = sender is not None
        scroll_y = 0
        if preserve_scroll:
            try:
                scroll_y = get_y_scroll("tables_panel")
            except:
                pass

        search_query = (app_data or "").strip().lower()
        delete_item("tables_list", children_only=True)

        if not self.db_manager.is_connected:
            self.show_saved_connections()
            return

        connection_name = self._get_connection_display_name()
        is_expanded = "current" in self.connections_expanded

        if not is_expanded:
            self.show_saved_connections()
            return

        # Show a loading placeholder while fetching tables in background
        add_text("  Loading tables...", parent="tables_list", color=(100, 150, 255))

        # Bump sequence so a stale async result from a previous call is ignored
        self._tables_seq += 1
        seq = self._tables_seq

        if self.async_worker:
            self.async_worker.run_async(
                task=lambda: self.db_manager.get_tables(),
                on_done=lambda tables: self._finish_filter_tables(
                    tables, seq, search_query, connection_name, preserve_scroll, scroll_y
                ),
                on_error=lambda e: self._on_get_tables_error(e, seq),
            )
        else:
            # Synchronous fallback
            all_tables = self.db_manager.get_tables()
            self._finish_filter_tables(
                all_tables, seq, search_query, connection_name, preserve_scroll, scroll_y
            )

    def _finish_filter_tables(
        self, all_tables, seq, search_query, connection_name, preserve_scroll, scroll_y
    ):
        """Build the table list UI on the main thread after tables are fetched."""
        # Discard stale results
        if seq != self._tables_seq:
            return

        # Guard against late arrival after disconnect
        if not self.db_manager.is_connected or "current" not in self.connections_expanded:
            self.show_saved_connections()
            return

        delete_item("tables_list", children_only=True)

        filtered_tables = [
            table for table in all_tables if search_query in table.lower()
        ]

        # Add connection header button
        connection_button = f"connection_header_{int(time.time() * 1000)}"
        add_button(
            label=f"[-] {connection_name}",
            parent="tables_list",
            callback=self.toggle_connection_callback,
            width=-1,
            height=30,
            tag=connection_button,
        )
        if self.theme_manager:
            bind_item_theme(
                connection_button, self.theme_manager.get_theme("selected_table_button")
            )

        if not filtered_tables:
            add_text("  No tables found", parent="tables_list", color=(255, 0, 0))
        else:
            for table in filtered_tables:
                table_button_tag = f"table_button_{table}"
                context_menu_tag = f"context_menu_{table}"

                try:
                    if does_item_exist(table_button_tag):
                        delete_item(table_button_tag)
                    if does_item_exist(context_menu_tag):
                        delete_item(context_menu_tag)
                except:
                    pass

                add_button(
                    label=f"  {table}",
                    parent="tables_list",
                    callback=self.select_table_callback,
                    tag=table_button_tag,
                )

                with popup(
                    parent=table_button_tag,
                    mousebutton=1,
                    tag=context_menu_tag,
                ):
                    add_menu_item(
                        label="Copy Table Name",
                        callback=self._copy_table_name_callback,
                        user_data=table,
                    )

                if table == self.selected_table:
                    if self.theme_manager:
                        bind_item_theme(
                            table_button_tag,
                            self.theme_manager.get_theme("selected_table_button"),
                        )
                else:
                    if self.theme_manager:
                        bind_item_theme(
                            table_button_tag,
                            self.theme_manager.get_theme("table_button"),
                        )

        if filtered_tables:
            add_separator(parent="tables_list")
            add_text("Other Connections:", parent="tables_list", color=(220, 220, 220))

            credential_names = self.credentials_manager.get_credential_names()
            current_connection_name = self._find_credential_name_for_connection()

            other_connections = [
                name for name in credential_names if name != current_connection_name
            ]

            if other_connections:
                for name in other_connections:
                    btn_tag = f"connection_{name}_{int(time.time() * 1000)}"
                    add_button(
                        label=f"{name}",
                        parent="tables_list",
                        callback=self.connect_to_saved_callback,
                        user_data=name,
                        width=-1,
                        height=30,
                        tag=btn_tag,
                    )
                    if self.theme_manager:
                        bind_item_theme(
                            btn_tag,
                            self.theme_manager.get_theme("table_button"),
                        )
            else:
                add_text(
                    "  No other connections",
                    parent="tables_list",
                    color=(128, 128, 128),
                )

        if preserve_scroll:
            try:
                set_y_scroll("tables_panel", scroll_y)
            except:
                pass

    def _on_get_tables_error(self, e: Exception, seq: int):
        """Called on main thread when get_tables raises an exception."""
        if seq != self._tables_seq:
            return
        delete_item("tables_list", children_only=True)
        add_text(
            f"  Error loading tables: {str(e)}", parent="tables_list", color=(255, 0, 0)
        )

    def select_table_callback(self, sender, app_data):
        """Handle table selection and single-click explorer opening."""
        table_name = sender.replace("table_button_", "")

        # Swap button themes in-place — no re-fetch, no scroll jump
        if self.theme_manager:
            # Deselect the previously selected table button
            if self.selected_table:
                prev_tag = f"table_button_{self.selected_table}"
                if does_item_exist(prev_tag):
                    bind_item_theme(prev_tag, self.theme_manager.get_theme("table_button"))

            # Highlight the newly selected table button
            new_tag = f"table_button_{table_name}"
            if does_item_exist(new_tag):
                bind_item_theme(new_tag, self.theme_manager.get_theme("selected_table_button"))

        self.selected_table = table_name

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
                # Store loaded credentials for connection in both places
                self.stored_credentials = credentials

                # IMPORTANT: Update the connection manager's stored credentials too
                # so it uses the correct credentials when connecting
                if self.connection_manager:
                    self.connection_manager.stored_credentials = credentials

                # Expand the connection node immediately so that when on_connect_success
                # triggers filter_tables_callback, the expanded state is already set.
                self.connections_expanded.add("current")

                # Show a connecting placeholder in the tables list
                delete_item("tables_list", children_only=True)
                add_text(
                    f"  Connecting to {connection_name}...",
                    parent="tables_list",
                    color=(100, 150, 255),
                )

                # Kick off async connection — on_connect_success will refresh the table list
                self.connection_callback(None, None)

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
