"""Data Explorer component for ClickHouse Client."""

import time
from typing import Dict, Optional

from dearpygui.dearpygui import *

from config import DEFAULT_LIMIT, MAX_CELL_LENGTH, MAX_ROWS_LIMIT
from database import DatabaseManager


class DataExplorer:
    """Manages the data explorer interface and functionality."""

    def __init__(self, db_manager: DatabaseManager, theme_manager=None):
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.current_table: Optional[str] = None
        self.filters: Dict[str, str] = {}
        self.table_theme = None
        self.selected_row_data = None  # Store selected row data for details panel
        self.current_column_names = []  # Store current column names
        self.sort_column: Optional[str] = None  # Current sort column
        self.sort_ascending: bool = True  # Sort direction
        self._setup_table_theme()

    def _setup_table_theme(self):
        """Setup theme for data tables with increased row height."""
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

    def open_explorer(self, table_name: str, status_callback=None) -> bool:
        """
        Open data explorer for a specific table.

        Args:
            table_name: Name of the table to explore
            status_callback: Function to call for status updates

        Returns:
            bool: True if explorer opened successfully
        """
        if not table_name or not table_name.strip():
            if status_callback:
                status_callback(
                    "Error: Cannot open data explorer - invalid table name", True
                )
            return False

        self.current_table = table_name.strip()
        self.filters.clear()

        if status_callback:
            status_callback(f"Opening data explorer for table: {self.current_table}")

        # Hide query and results sections
        configure_item("query_section", show=False)
        configure_item("results_window", show=False)

        # Show explorer section
        configure_item("explorer_section", show=True)

        # Setup filter controls
        self._setup_filters()

        # Clear existing data window and show loading message
        # First make sure items exist and are visible
        try:
            # Ensure explorer section is visible
            configure_item("explorer_section", show=True)

            # Verify data window exists and is visible
            configure_item("explorer_data_window", show=True)

            # For safety, verify the main table panel exists
            if does_item_exist("explorer_main_table"):
                delete_item("explorer_main_table", children_only=True)
                add_text(
                    "Loading data preview...",
                    parent="explorer_main_table",
                    color=(220, 220, 220),
                )

            # Clear row details panel if it exists
            if does_item_exist("explorer_row_details"):
                self._clear_row_details()

        except Exception as e:
            print(f"[DataExplorer] Error in explorer setup: {e}")
            if status_callback:
                status_callback(f"Error setting up data explorer: {str(e)}", True)
            return False

        # Load initial data preview
        self.refresh_data(status_callback)
        return True

    def close_explorer(self):
        """Close data explorer and return to query interface."""
        self.current_table = None
        self.filters.clear()
        self.selected_row_data = None
        self.current_column_names = []
        self.sort_column = None
        self.sort_ascending = True

        # Reset WHERE clause and limit fields
        try:
            configure_item("explorer_where", default_value="")
        except:
            pass  # Field might not exist yet

        try:
            configure_item("explorer_limit", default_value="100")
        except:
            pass  # Field might not exist yet

        # Hide explorer section
        configure_item("explorer_section", show=False)

        # Show query and results sections
        configure_item("query_section", show=True)
        configure_item("results_window", show=True)

    def _setup_filters(self):
        """Setup WHERE filter control for the current table."""
        # Set up callback for the WHERE input field to refresh data on Enter
        try:
            configure_item("explorer_where", callback=self._on_where_change)
            configure_item("explorer_limit", callback=self._on_limit_change)
        except Exception:
            pass  # Input might not exist yet

    def _on_where_change(self, sender, app_data):
        """Handle WHERE condition change - refresh data when Enter is pressed."""
        self.refresh_data()

    def _on_limit_change(self, sender, app_data):
        """Handle limit change - refresh data when Enter is pressed."""
        self.refresh_data()

    def _on_column_header_click(self, sender, app_data, user_data):
        """Handle column header click for sorting."""
        column_name = user_data

        # Toggle sort direction if same column, otherwise set to ascending
        if self.sort_column == column_name:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column_name
            self.sort_ascending = True

        # Refresh data with new sort
        self.refresh_data()

    def refresh_data(self, status_callback=None):
        """Refresh data in the data explorer with current filters."""
        if not self.db_manager.is_connected or not self.current_table:
            return

        # Store status callback for use in copy function
        self._last_status_callback = status_callback

        try:
            # Build query with filters - use backticks for table name safety
            query = f"SELECT * FROM `{self.current_table}`"

            # Add WHERE clause if provided
            try:
                where_clause = get_value("explorer_where")
                if where_clause and where_clause.strip():
                    query += f" WHERE {where_clause.strip()}"
            except:
                pass  # WHERE input doesn't exist yet or is empty

            # Add ORDER BY clause if sorting is enabled
            if self.sort_column:
                sort_direction = "ASC" if self.sort_ascending else "DESC"
                query += f" ORDER BY `{self.sort_column}` {sort_direction}"

            # Add limit
            try:
                limit_value = get_value("explorer_limit")
                if limit_value and limit_value.strip():
                    limit = int(limit_value)
                    if limit > MAX_ROWS_LIMIT:  # Prevent loading too much data
                        limit = MAX_ROWS_LIMIT
                        if status_callback:
                            status_callback(
                                f"Limit capped at {MAX_ROWS_LIMIT} rows for performance",
                                False,
                            )
                    query += f" LIMIT {limit}"
            except:
                query += f" LIMIT {DEFAULT_LIMIT}"  # Default limit

            if status_callback:
                status_callback(f"Executing query: {query}")

            # Execute query
            result = self.db_manager.execute_query(query)

            # Debug: Show column info
            if status_callback:
                status_callback(
                    f"Query executed. Columns: {result.column_names}, Row count: {len(result.result_rows)}"
                )

            # Store current data for row details
            self.current_column_names = result.column_names

            # Make sure the explorer_main_table exists before attempting to clear it
            if not does_item_exist("explorer_main_table"):
                if status_callback:
                    status_callback(
                        "Error: Main table panel is not available. Please restart.",
                        True,
                    )
                return

            # Clear existing data completely from main table panel
            delete_item("explorer_main_table", children_only=True)

            if not result.result_rows:
                add_text(
                    "No data found", parent="explorer_main_table", color=(128, 128, 128)
                )
                self._clear_row_details()
                return

            # Create data table with borders and headers - use unique tag to force recreation
            table_tag = f"explorer_data_table_{int(time.time() * 1000)}"

            try:
                add_table(
                    tag=table_tag,
                    parent="explorer_main_table",
                    borders_innerH=True,
                    borders_innerV=True,
                    borders_outerH=True,
                    borders_outerV=True,
                    header_row=False,  # We'll create custom header with clickable buttons
                    scrollX=True,
                    scrollY=True,
                    freeze_rows=1,
                    height=-1,
                    resizable=True,
                    policy=mvTable_SizingFixedFit,
                )  # Enable column resizing, fixed fit policy
            except Exception as table_e:
                print(f"[DataExplorer] Error creating table: {table_e}")
                add_text(
                    f"Error creating data table: {str(table_e)}",
                    parent="explorer_main_table",
                    color=(255, 0, 0),
                )
                return

            # Apply theme for larger row height
            if self.table_theme:
                bind_item_theme(table_tag, self.table_theme)

            # Add columns with headers showing both column names and types for better readability
            # Get column types from database
            try:
                table_columns = self.db_manager.get_table_columns(self.current_table)
                column_types = {
                    col_name: col_type for col_name, col_type in table_columns
                }
            except Exception:
                column_types = {}

            column_tags = []
            for col in result.column_names:
                # Use fixed pixel width for each column
                column_tag = f"col_{table_tag}_{col}"
                column_tags.append(column_tag)
                add_table_column(
                    tag=column_tag,
                    parent=table_tag,
                    init_width_or_weight=200,  # Fixed width: 200px per column
                    width_stretch=False,  # Do not auto-stretch
                    width_fixed=False,  # Allow manual resizing
                    no_resize=False,  # Allow manual resizing
                )
                # Initial width set attempt
                try:
                    configure_item(column_tag, width=200)
                except Exception:
                    try:
                        set_item_width(column_tag, 200)
                    except Exception:
                        pass

            # Try again after all columns are created (aggressive workaround)
            for column_tag in column_tags:
                try:
                    configure_item(column_tag, width=200)
                except Exception:
                    try:
                        set_item_width(column_tag, 200)
                    except Exception:
                        pass

            # Add custom header row with clickable buttons
            with table_row(parent=table_tag):
                for col in result.column_names:
                    # Create header with column name, type information, and sort indicator
                    col_type = column_types.get(col, "Unknown")

                    # Add sort indicator
                    sort_indicator = ""
                    if self.sort_column == col:
                        sort_indicator = " ^" if self.sort_ascending else " v"

                    header_label = f"{col_type}\n{col}{sort_indicator}"

                    # Add clickable button as header
                    add_button(
                        label=header_label,
                        tag=f"header_{table_tag}_{col}",
                        callback=self._on_column_header_click,
                        user_data=col,
                        width=-1,  # Full width of column
                        height=50,  # Taller header
                    )

            # Add rows with proper encoding handling and selectable cells with row selection functionality
            for row_idx, row in enumerate(result.result_rows):
                with table_row(parent=table_tag):
                    for col_idx, val in enumerate(row):
                        # Handle special characters and encoding properly
                        try:
                            cell_value = self._format_cell_value(val)
                            # Use selectable widget with row selection callback
                            add_selectable(
                                label=cell_value,
                                tag=f"cell_{row_idx}_{col_idx}",
                                span_columns=False,
                                height=0,  # Auto height
                                callback=self._handle_cell_click,
                                user_data={
                                    "row_idx": row_idx,
                                    "col_idx": col_idx,
                                    "cell_value": cell_value,
                                    "row_data": row,
                                },
                            )
                        except Exception as e:
                            # Fallback for any encoding issues
                            error_text = f"[Error: {str(e)}]"
                            add_selectable(
                                label=error_text,
                                tag=f"cell_error_{row_idx}_{col_idx}",
                                span_columns=False,
                                height=0,
                                callback=self._handle_cell_click,
                                user_data={
                                    "row_idx": row_idx,
                                    "col_idx": col_idx,
                                    "cell_value": error_text,
                                    "row_data": row,
                                },
                            )

            # Update status
            if status_callback:
                status_callback(
                    f"Explorer: Showing {len(result.result_rows)} rows from {self.current_table}"
                )

        except Exception as e:
            # Clear existing data
            delete_item("explorer_main_table", children_only=True)
            add_text(
                f"Error loading data: {str(e)}",
                parent="explorer_main_table",
                color=(255, 0, 0),
            )
            self._clear_row_details()
            if status_callback:
                status_callback(f"Explorer error: {str(e)}", True)

    def clear_filters(self):
        """Clear all filters in data explorer."""
        # Clear WHERE clause filter
        try:
            configure_item("explorer_where", default_value="")
        except:
            pass  # Filter input doesn't exist yet

        # Reset limit to default value of 100
        try:
            configure_item("explorer_limit", default_value="100")
        except:
            pass  # Limit input doesn't exist yet

        # Reset limit to default value of 100
        try:
            configure_item("explorer_limit", default_value="100")
        except:
            pass  # Limit input doesn't exist yet

        # Clear sorting
        self.sort_column = None
        self.sort_ascending = True

        # Clear row details
        self._clear_row_details()

        # Refresh data with cleared filters
        self.refresh_data()

    def _copy_cell_to_clipboard(self, sender, app_data, user_data):
        """Copy cell content to clipboard when clicked."""
        try:
            # Get the cell value from the user_data
            cell_text = user_data if user_data else ""

            # Use DearPyGui's set_clipboard_text to copy to system clipboard
            set_clipboard_text(cell_text)

            # Optional: Show brief feedback (you can remove this if it's too intrusive)
            # We'll just update status if callback is available
            if hasattr(self, "_last_status_callback") and self._last_status_callback:
                self._last_status_callback(
                    f"Copied to clipboard: {cell_text[:50]}{'...' if len(cell_text) > 50 else ''}"
                )

        except Exception as e:
            print(f"Error copying to clipboard: {e}")

    def _format_cell_value(self, val) -> str:
        """Format a cell value for display."""
        if val is None:
            return "NULL"
        elif isinstance(val, bytes):
            # Handle byte strings
            cell_value = val.decode("utf-8", errors="replace")
        elif isinstance(val, str):
            # Ensure string is properly encoded
            cell_value = val.encode("utf-8", errors="replace").decode("utf-8")
        else:
            # Convert other types to string safely
            cell_value = str(val)

        # Limit cell content length to prevent UI issues
        if len(cell_value) > MAX_CELL_LENGTH:
            cell_value = cell_value[: MAX_CELL_LENGTH - 3] + "..."

        return cell_value

    def _handle_cell_click(self, sender, app_data, user_data):
        """Handle cell click for both copying to clipboard and showing row details."""
        try:
            # Extract data from user_data
            row_idx = user_data["row_idx"]
            col_idx = user_data["col_idx"]
            cell_value = user_data["cell_value"]
            row_data = user_data["row_data"]

            # Copy cell value to clipboard (existing functionality)
            set_clipboard_text(cell_value)

            # Show brief feedback for copy
            if hasattr(self, "_last_status_callback") and self._last_status_callback:
                self._last_status_callback(
                    f"Copied to clipboard: {cell_value[:50]}{'...' if len(cell_value) > 50 else ''}"
                )

            # Update row details panel
            self._update_row_details(row_data, row_idx)

        except Exception as e:
            print(f"Error handling cell click: {e}")

    def _update_row_details(self, row_data, row_idx):
        """Update the row details panel with the selected row's data."""
        try:
            # Clear existing row details
            delete_item("explorer_row_details", children_only=True)

            # Add header
            add_text(
                f"Row {row_idx + 1} Details",
                parent="explorer_row_details",
                color=(255, 193, 7),
            )
            add_separator(parent="explorer_row_details")

            # Create a scrollable table for column:value pairs
            details_table_tag = f"row_details_table_{int(time.time() * 1000)}"
            add_table(
                tag=details_table_tag,
                parent="explorer_row_details",
                borders_innerH=True,
                borders_innerV=True,
                borders_outerH=True,
                borders_outerV=True,
                header_row=True,
                scrollY=True,
                height=-1,
                width=-1,
                resizable=True,
            )

            # Add columns for the details table
            add_table_column(
                label="Column", parent=details_table_tag, init_width_or_weight=120
            )
            add_table_column(
                label="Value", parent=details_table_tag, init_width_or_weight=250
            )

            # Add row data
            for col_idx, (column_name, value) in enumerate(
                zip(self.current_column_names, row_data)
            ):
                with table_row(parent=details_table_tag):
                    # Column name
                    add_selectable(
                        label=column_name,
                        tag=f"detail_col_{col_idx}",
                        span_columns=False,
                        height=0,
                        callback=self._copy_detail_to_clipboard,
                        user_data=column_name,
                    )

                    # Column value
                    formatted_value = self._format_cell_value(value)
                    add_selectable(
                        label=formatted_value,
                        tag=f"detail_val_{col_idx}",
                        span_columns=False,
                        height=0,
                        callback=self._copy_detail_to_clipboard,
                        user_data=formatted_value,
                    )

            # Store selected row data
            self.selected_row_data = row_data

        except Exception as e:
            # Fallback error display
            delete_item("explorer_row_details", children_only=True)
            add_text(
                f"Error displaying row details: {str(e)}",
                parent="explorer_row_details",
                color=(255, 0, 0),
            )

    def _clear_row_details(self):
        """Clear the row details panel."""
        try:
            delete_item("explorer_row_details", children_only=True)
            add_text(
                "Select a row to view details",
                parent="explorer_row_details",
                color=(128, 128, 128),
            )
            self.selected_row_data = None
        except:
            pass  # Ignore errors if panel doesn't exist

    def _copy_detail_to_clipboard(self, sender, app_data, user_data):
        """Copy detail value to clipboard when clicked."""
        try:
            # Get the value from user_data
            detail_text = user_data if user_data else ""

            # Use DearPyGui's set_clipboard_text to copy to system clipboard
            set_clipboard_text(detail_text)

            # Show brief feedback
            if hasattr(self, "_last_status_callback") and self._last_status_callback:
                self._last_status_callback(
                    f"Copied to clipboard: {detail_text[:50]}{'...' if len(detail_text) > 50 else ''}"
                )

        except Exception as e:
            print(f"Error copying detail to clipboard: {e}")
