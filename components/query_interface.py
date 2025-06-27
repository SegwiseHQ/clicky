"""Query interface component for ClickHouse Client."""

import re
import time
from typing import Callable, Optional

from dearpygui.dearpygui import *

from config import COLOR_ERROR, COLOR_SUCCESS
from database import DatabaseManager


class QueryInterface:
    """Manages the query interface and results display."""

    def __init__(self, db_manager: DatabaseManager, theme_manager=None):
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.current_table: Optional[str] = None
        self.table_counter = 0
        self.status_callback: Optional[Callable[[str, bool], None]] = None
        self.table_theme = None
        self._setup_table_theme()

    def _setup_table_theme(self):
        """Setup theme for results tables with increased row height."""
        if self.theme_manager:
            # Use theme manager's table theme
            self.table_theme = self.theme_manager.get_theme("table_enhanced")
        else:
            # Fallback theme creation
            with theme() as self.table_theme:
                with theme_component(mvTable):
                    add_theme_style(
                        mvStyleVar_CellPadding, 8, 8
                    )  # Increase cell padding
                    add_theme_style(
                        mvStyleVar_ItemSpacing, 0, 4
                    )  # Add vertical spacing between items

    def set_status_callback(self, callback: Callable[[str, bool], None]):
        """Set callback for status messages."""
        self.status_callback = callback

    def run_query_callback(self, sender, data):
        """Execute the query from the input field."""
        if not self.db_manager.is_connected:
            if self.status_callback:
                self.status_callback("Not connected to database", True)
            return

        query = get_value("query_input").strip()
        if not query:
            if self.status_callback:
                self.status_callback("Query is empty", True)
            return

        try:
            # Execute query
            result = self.db_manager.execute_query(query)

            # Always clear previous results first
            if self.current_table:
                delete_item(self.current_table)
                self.current_table = None

            if not result.result_rows:
                if self.status_callback:
                    self.status_callback(
                        "Query executed successfully (no results)", False
                    )
                return

            # Get column names and rows
            column_names = result.column_names
            rows = result.result_rows

            # Setup table with new columns
            self._setup_results_table(column_names, query)

            # Add rows
            for row_idx, row in enumerate(rows):
                with table_row(parent=self.current_table):
                    for col_idx, cell_value in enumerate(row):
                        # Format cell value for display and get original for copying
                        formatted_cell = self._format_cell_value(cell_value)
                        original_cell = (
                            str(cell_value) if cell_value is not None else "NULL"
                        )

                        # Use selectable instead of text to enable click-to-copy
                        cell_tag = (
                            f"query_cell_{self.table_counter}_{row_idx}_{col_idx}"
                        )
                        add_selectable(
                            label=formatted_cell,
                            tag=cell_tag,
                            callback=self._copy_cell_to_clipboard,
                            user_data=original_cell,  # Original cell content for copying
                        )

            if self.status_callback:
                self.status_callback(
                    f"Query executed successfully. Rows returned: {len(rows)}", False
                )

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Query failed: {str(e)}", True)

    def _setup_results_table(self, columns, query=None):
        """Setup the results table with the given columns."""
        # Create new table with dynamic columns and borders
        self.table_counter += 1
        self.current_table = f"query_result_{self.table_counter}"
        add_table(
            tag=self.current_table,
            parent="results_window",
            borders_innerH=True,
            borders_innerV=True,
            borders_outerH=True,
            borders_outerV=True,
            header_row=True,
            scrollX=True,
            scrollY=True,
            freeze_rows=1,
            height=-1,
            resizable=True,
            policy=mvTable_SizingFixedFit,
        )  # Enable column resizing with fixed fit policy

        # Apply theme for larger row height
        if self.table_theme:
            bind_item_theme(self.current_table, self.table_theme)

        # Try to get column types from query context
        column_types = {}
        if query:
            column_types = self._get_column_types_from_query(query, columns)

        # Add columns with wider widths and type information
        for col in columns:
            # Create header with column name and type information
            col_type = column_types.get(col, "")
            if col_type:
                header_label = f"{col_type}\n{col}"
            else:
                header_label = str(col)
            # Allow manual column resizing by removing width_fixed and using sensible defaults
            column_tag = f"col_{self.current_table}_{col}"
            add_table_column(
                tag=column_tag,
                label=header_label,
                parent=self.current_table,
                init_width_or_weight=350,  # Increased to 350px for query results
                width_stretch=False,  # Do not auto-stretch, use fixed pixel width
                width_fixed=False,  # Explicitly allow width changes
                no_resize=False,  # Allow manual resizing (this is default but explicit for clarity)
            )

        # Force all column widths after table creation
        for col in columns:
            column_tag = f"col_{self.current_table}_{col}"
            # Force the column width after creation with multiple approaches
            try:
                configure_item(column_tag, width=350)
            except:
                try:
                    set_item_width(column_tag, 350)
                except:
                    pass  # If none work, that's ok

    def _copy_cell_to_clipboard(self, sender, app_data, user_data):
        """Copy cell content to clipboard when clicked."""
        try:
            # Get the cell value from the user_data
            cell_text = user_data if user_data else ""

            # Use DearPyGui's set_clipboard_text to copy to system clipboard
            set_clipboard_text(cell_text)

            # Show feedback through status callback
            if self.status_callback:
                preview = cell_text[:50] + "..." if len(cell_text) > 50 else cell_text
                self.status_callback(f"Copied to clipboard: {preview}", False)

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error copying to clipboard: {str(e)}", True)

    def _format_cell_value(self, val) -> str:
        """Format a cell value for display."""
        if val is None:
            return "NULL"
        elif isinstance(val, bytes):
            # Handle byte strings
            try:
                cell_value = val.decode("utf-8", errors="replace")
            except:
                cell_value = str(val)
        elif isinstance(val, str):
            # Ensure string is properly encoded
            try:
                cell_value = val.encode("utf-8", errors="replace").decode("utf-8")
            except:
                cell_value = str(val)
        else:
            # Convert other types to string safely
            cell_value = str(val)

        return cell_value

    def _get_column_types_from_query(self, query, columns):
        """Try to extract column types from query context."""
        column_types = {}

        try:
            # Simple pattern matching for basic SELECT queries
            query_lower = query.lower().strip()

            # Look for "FROM table_name" pattern
            from_match = re.search(r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)", query_lower)
            if from_match:
                table_name = from_match.group(1)

                # Get column information for this table
                try:
                    table_columns = self.db_manager.get_table_columns(table_name)
                    table_column_types = {
                        col_name: col_type for col_name, col_type in table_columns
                    }

                    # Match query result columns with table columns
                    for col in columns:
                        if col in table_column_types:
                            column_types[col] = table_column_types[col]
                except Exception:
                    pass  # If we can't get table info, just skip
        except Exception:
            pass  # If any error in pattern matching, just return empty dict

        return column_types
