"""Table browser component for ClickHouse Client."""

import time
from typing import Callable, Dict, Optional, Set

from dearpygui.dearpygui import *

from config import (
    COLOR_COLUMN,
    COLOR_ERROR,
    COLOR_INFO,
    DOUBLE_CLICK_THRESHOLD,
    TABLE_BUTTON_HEIGHT,
)
from database import DatabaseManager
from icon_manager import icon_manager
from utils import TableHelpers


class TableBrowser:
    """Manages the database tables browser interface."""

    def __init__(self, db_manager: DatabaseManager, theme_manager=None):
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.expanded_tables: Set[str] = set()
        self.table_columns: Dict[str, list] = {}
        self.last_click_time: Dict[str, float] = {}
        self.double_click_callback: Optional[Callable[[str], None]] = None
        self.status_callback: Optional[Callable[[str, bool], None]] = None

    def set_double_click_callback(self, callback: Callable[[str], None]):
        """Set callback for table double-click events."""
        self.double_click_callback = callback

    def set_status_callback(self, callback: Callable[[str, bool], None]):
        """Set callback for status messages."""
        self.status_callback = callback

    def table_click_callback(self, sender, data):
        """Handle clicking on a table name to toggle its columns or open explorer on double-click."""
        # Extract table name from the button tag (format: "table_{table_name}")
        # The sender parameter is the tag of the clicked button
        table_name = sender.replace("table_", "")
        current_time = time.time()

        # Check for double-click
        if table_name in self.last_click_time:
            time_diff = current_time - self.last_click_time[table_name]
            if time_diff < DOUBLE_CLICK_THRESHOLD:  # Double-click detected
                if self.status_callback:
                    self.status_callback(
                        f"Double-click detected on table: {table_name}", False
                    )
                if self.double_click_callback:
                    self.double_click_callback(table_name)
                return

        # Store current click time
        self.last_click_time[table_name] = current_time

        # Regular single-click behavior - toggle columns
        if table_name in self.expanded_tables:
            # Collapse the table
            self.expanded_tables.remove(table_name)
        else:
            # Expand the table
            self.expanded_tables.add(table_name)
            # Load column information if not cached
            if table_name not in self.table_columns:
                self._load_table_columns(table_name)

        # Rebuild the tables list while preserving scroll
        self._rebuild_tables_list_preserve_scroll()

    def _load_table_columns(self, table_name: str):
        """Load and cache column information for a table."""
        if not self.db_manager.is_connected:
            return

        if not table_name or not table_name.strip():
            if self.status_callback:
                self.status_callback("Error: Empty table name provided", True)
            return

        table_name = table_name.strip()

        try:
            if self.status_callback:
                self.status_callback(f"Loading columns for table: {table_name}")

            columns = self.db_manager.get_table_columns(table_name)
            self.table_columns[table_name] = columns

            if self.status_callback:
                self.status_callback(f"Loaded {len(columns)} columns for {table_name}")

        except Exception as e:
            if self.status_callback:
                self.status_callback(
                    f"Failed to load columns for {table_name}: {str(e)}", True
                )
            self.table_columns[table_name] = (
                []
            )  # Cache empty result to avoid repeated failures

    def _rebuild_tables_list_preserve_scroll(self):
        """Rebuild the tables list while preserving scroll position."""
        # Get current scroll position
        try:
            scroll_y = get_y_scroll("tables_list")
        except:
            scroll_y = 0

        # Rebuild the list
        self.refresh_tables()

        # Restore scroll position
        try:
            set_y_scroll("tables_list", scroll_y)
        except:
            pass

    def refresh_tables(self):
        """Refresh the tables list and show tables from database."""
        if not self.db_manager.is_connected:
            self.clear_tables()
            return

        try:
            # Get all tables
            tables = self.db_manager.get_tables()

            # Clear and rebuild tables list
            delete_item("tables_list", children_only=True)

            if not tables:
                add_text("No tables found", parent="tables_list", color=COLOR_INFO)
                return

            # Add each table with expand/collapse functionality
            for table in tables:
                self._add_table_to_list(table)

            if self.status_callback:
                self.status_callback(f"Loaded {len(tables)} tables")

        except Exception as e:
            delete_item("tables_list", children_only=True)
            add_text("Error loading tables", parent="tables_list", color=COLOR_ERROR)
            if self.status_callback:
                self.status_callback(f"Failed to list tables: {str(e)}", True)

    def _add_table_to_list(self, table_name: str):
        """Add a single table to the tables list with expand/collapse functionality."""
        # Determine expand/collapse icon
        is_expanded = table_name in self.expanded_tables
        icon = (
            icon_manager.get("arrow_down")
            if is_expanded
            else icon_manager.get("arrow_right")
        )

        # Add table button
        table_button_tag = f"table_{table_name}"
        add_button(
            label=f"{icon} {table_name}",
            parent="tables_list",
            callback=self.table_click_callback,
            tag=table_button_tag,
            height=TABLE_BUTTON_HEIGHT,
        )

        # Apply theme
        if self.theme_manager:
            bind_item_theme(
                table_button_tag, self.theme_manager.get_theme("table_button")
            )

        # Add columns if expanded
        if is_expanded and table_name in self.table_columns:
            for column_name, column_type in self.table_columns[table_name]:
                column_tag = f"column_{table_name}_{column_name}"
                add_text(
                    f"    {icon_manager.get('column')} {column_name} ({column_type})",
                    parent="tables_list",
                    color=COLOR_COLUMN,
                    tag=column_tag,
                )
                if self.theme_manager:
                    bind_item_theme(
                        column_tag, self.theme_manager.get_theme("column_text")
                    )

    def clear_tables(self):
        """Clear the tables list and show disconnected state."""
        self.expanded_tables.clear()
        self.table_columns.clear()

        # Clear tables list
        delete_item("tables_list", children_only=True)
        add_text("Connect to see tables", parent="tables_list", color=COLOR_INFO)
