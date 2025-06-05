"""Data Explorer component for ClickHouse Client."""

import time
from typing import Dict, Optional, Set

from dearpygui.dearpygui import *

from config import DEFAULT_LIMIT, MAX_CELL_LENGTH, MAX_ROWS_LIMIT, TABLE_ROW_HEIGHT
from database import DatabaseManager
from utils import FontManager, TableHelpers, UIHelpers


class DataExplorer:
    """Manages the data explorer interface and functionality."""

    def __init__(self, db_manager: DatabaseManager, theme_manager=None):
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.current_table: Optional[str] = None
        self.filters: Dict[str, str] = {}
        self.table_theme = None
        self._setup_table_theme()

    def _setup_table_theme(self):
        """Setup theme for data tables with increased row height."""
        if self.theme_manager:
            # Use theme manager's table theme
            self.table_theme = self.theme_manager.get_theme('table_enhanced')
        else:
            # Fallback theme creation
            with theme() as self.table_theme:
                with theme_component(mvTable):
                    add_theme_style(mvStyleVar_CellPadding, 8, 8)  # Increase cell padding
                    add_theme_style(mvStyleVar_ItemSpacing, 0, 4)  # Add vertical spacing between items

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
                status_callback("Error: Cannot open data explorer - invalid table name", True)
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

        # Update explorer title
        configure_item("explorer_title", default_value=f"Data Explorer - {self.current_table}")

        # Setup filter controls
        self._setup_filters()

        # Clear existing data window and show loading message
        # Ensure explorer_data_window exists and is visible before adding children
        try:
            configure_item("explorer_data_window", show=True)
            delete_item("explorer_data_window", children_only=True)
            add_text("Loading data preview...", parent="explorer_data_window", color=(255, 255, 0))
        except Exception as e:
            print(f"[DataExplorer] Error: explorer_data_window not available: {e}")
            if status_callback:
                status_callback("Error: Data explorer view is not available. Please restart the application.", True)
            return False

        # Load initial data preview
        self.refresh_data(status_callback)
        return True

    def close_explorer(self):
        """Close data explorer and return to query interface."""
        self.current_table = None
        self.filters.clear()

        # Hide explorer section
        configure_item("explorer_section", show=False)

        # Show query and results sections
        configure_item("query_section", show=True)
        configure_item("results_window", show=True)

    def _setup_filters(self):
        """Setup WHERE and ORDER BY filter controls for the current table."""
        # Clear existing filters
        delete_item("explorer_filters", children_only=True)

        # Add WHERE clause input with Apply button
        add_text("WHERE clause (optional):", parent="explorer_filters")
        with group(horizontal=True, parent="explorer_filters"):
            add_input_text(tag="explorer_where", 
                           hint="e.g., column_name = 'value' AND other_column > 100", 
                           width=-100, height=60, multiline=True)
            add_button(label="Apply", callback=lambda: self.refresh_data(), width=80)

        add_separator(parent="explorer_filters")

        # Add ORDER BY clause input with Apply button
        add_text("ORDER BY clause (optional):", parent="explorer_filters")
        with group(horizontal=True, parent="explorer_filters"):
            add_input_text(tag="explorer_order_by",
                           hint="e.g., column_name DESC, other_column ASC", 
                           width=-100, height=40, multiline=True)
            add_button(label="Apply", callback=lambda: self.refresh_data(), width=80)

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

            # Add ORDER BY clause if provided
            try:
                order_by_clause = get_value("explorer_order_by")
                if order_by_clause and order_by_clause.strip():
                    query += f" ORDER BY {order_by_clause.strip()}"
            except:
                pass  # ORDER BY input doesn't exist yet or is empty

            # Add limit
            try:
                limit_value = get_value("explorer_limit")
                if limit_value and limit_value.strip():
                    limit = int(limit_value)
                    if limit > MAX_ROWS_LIMIT:  # Prevent loading too much data
                        limit = MAX_ROWS_LIMIT
                        if status_callback:
                            status_callback(f"Limit capped at {MAX_ROWS_LIMIT} rows for performance", False)
                    query += f" LIMIT {limit}"
            except:
                query += f" LIMIT {DEFAULT_LIMIT}"  # Default limit

            if status_callback:
                status_callback(f"Executing query: {query}")

            # Execute query
            result = self.db_manager.execute_query(query)

            # Debug: Show column info
            if status_callback:
                status_callback(f"Query executed. Columns: {result.column_names}, Row count: {len(result.result_rows)}")

            # Clear existing data completely
            delete_item("explorer_data_window", children_only=True)

            if not result.result_rows:
                add_text("No data found", parent="explorer_data_window", color=(128, 128, 128))
                return

            # Create data table with borders and headers - use unique tag to force recreation
            table_tag = f"explorer_data_table_{int(time.time() * 1000)}"
            add_table(
                tag=table_tag,
                parent="explorer_data_window",
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
            )  # Enable column resizing, fixed fit policy

            # Apply theme for larger row height
            if self.table_theme:
                bind_item_theme(table_tag, self.table_theme)

            # Add columns with headers showing both column names and types for better readability
            # Get column types from database
            try:
                table_columns = self.db_manager.get_table_columns(self.current_table)
                column_types = {col_name: col_type for col_name, col_type in table_columns}
            except Exception:
                column_types = {}

            column_tags = []
            for col in result.column_names:
                # Create header with column name and type information
                col_type = column_types.get(col, "Unknown")
                header_label = f"{col_type}\n{col}"
                # Use fixed pixel width for each column
                column_tag = f"col_{table_tag}_{col}"
                column_tags.append(column_tag)
                add_table_column(
                    tag=column_tag,
                    label=header_label,
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

            # Add rows with proper encoding handling and selectable cells with copy functionality
            for row_idx, row in enumerate(result.result_rows):
                with table_row(parent=table_tag):
                    for col_idx, val in enumerate(row):
                        # Handle special characters and encoding properly
                        try:
                            cell_value = self._format_cell_value(val)
                            # Use selectable widget with click callback to copy text
                            add_selectable(
                                label=cell_value,
                                tag=f"cell_{row_idx}_{col_idx}",
                                span_columns=False,
                                height=0,  # Auto height
                                callback=self._copy_cell_to_clipboard,
                                user_data=cell_value  # Pass the actual cell text for copying
                            )
                        except Exception as e:
                            # Fallback for any encoding issues
                            error_text = f"[Error: {str(e)}]"
                            add_selectable(
                                label=error_text,
                                tag=f"cell_error_{row_idx}_{col_idx}",
                                span_columns=False,
                                height=0,
                                callback=self._copy_cell_to_clipboard,
                                user_data=error_text
                            )

            # Update status
            if status_callback:
                status_callback(f"Explorer: Showing {len(result.result_rows)} rows from {self.current_table}")

        except Exception as e:
            # Clear existing data
            delete_item("explorer_data_window", children_only=True)
            add_text(f"Error loading data: {str(e)}", 
                    parent="explorer_data_window", color=(255, 0, 0))
            if status_callback:
                status_callback(f"Explorer error: {str(e)}", True)

    def clear_filters(self):
        """Clear all filters in data explorer."""
        # Clear WHERE clause filter
        try:
            configure_item("explorer_where", default_value="")
        except:
            pass  # Filter input doesn't exist yet

        # Clear ORDER BY filter
        try:
            configure_item("explorer_order_by", default_value="")
        except:
            pass  # Filter input doesn't exist yet

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
            if hasattr(self, '_last_status_callback') and self._last_status_callback:
                self._last_status_callback(f"Copied to clipboard: {cell_text[:50]}{'...' if len(cell_text) > 50 else ''}")

        except Exception as e:
            print(f"Error copying to clipboard: {e}")

    def _format_cell_value(self, val) -> str:
        """Format a cell value for display."""
        if val is None:
            return "NULL"
        elif isinstance(val, bytes):
            # Handle byte strings
            cell_value = val.decode('utf-8', errors='replace')
        elif isinstance(val, str):
            # Ensure string is properly encoded
            cell_value = val.encode('utf-8', errors='replace').decode('utf-8')
        else:
            # Convert other types to string safely
            cell_value = str(val)

        # Limit cell content length to prevent UI issues
        if len(cell_value) > MAX_CELL_LENGTH:
            cell_value = cell_value[:MAX_CELL_LENGTH-3] + "..."

        return cell_value
