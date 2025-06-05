"""UI components for ClickHouse Client."""

import time
from typing import Callable, Dict, Optional, Set

from dearpygui.dearpygui import *

from config import (
    COLOR_COLUMN,
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_SUCCESS,
    COLOR_WARNING,
    DOUBLE_CLICK_THRESHOLD,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_WIDTH,
    QUERY_INPUT_HEIGHT,
    STATUS_WINDOW_HEIGHT,
    TABLE_BUTTON_HEIGHT,
    TABLES_PANEL_WIDTH,
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
        self.left_aligned_button_theme = None

    def initialize_theme(self):
        """Initialize the left-aligned button theme after DearPyGUI context is created."""
        with theme() as self.left_aligned_button_theme:
            with theme_component(mvButton):
                add_theme_style(mvStyleVar_ButtonTextAlign, 0.0, 0.5)

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
                    self.status_callback(f"Double-click detected on table: {table_name}", False)
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
                self.status_callback(f"Loading columns for table: {table_name}", False)

            columns = self.db_manager.get_table_columns(table_name)
            self.table_columns[table_name] = columns

            if self.status_callback:
                self.status_callback(f"Loaded {len(columns)} columns for table: {table_name}", False)

        except Exception as e:
            # Cache empty result to avoid repeated failed queries
            self.table_columns[table_name] = []
            if self.status_callback:
                self.status_callback(f"Failed to get columns for table '{table_name}': {str(e)}", True)

    def _rebuild_tables_list_preserve_scroll(self):
        """Rebuild tables list while preserving scroll position."""
        # Get current scroll position if possible
        try:
            scroll_y = get_y_scroll("tables_panel")
        except:
            scroll_y = 0

        # Rebuild the list
        self.rebuild_tables_list()

        # Restore scroll position
        try:
            set_y_scroll("tables_panel", scroll_y)
        except:
            pass

    def rebuild_tables_list(self):
        """Rebuild the entire tables list with expanded columns in the correct positions."""
        if not self.db_manager.is_connected:
            return

        # Clear the current list
        delete_item("tables_list", children_only=True)

        # Get all tables
        try:
            tables = self.db_manager.get_tables()
            if not tables:
                add_text("No tables found", parent="tables_list", color=COLOR_INFO)
                return

            # Add each table and its columns if expanded
            for table_name in tables:
                # Add the table button with icon, left-aligned with increased height
                button_tag = f"table_{table_name}"
                table_label = f"{icon_manager.get('table')} {table_name}"
                add_button(label=table_label, parent="tables_list", callback=self.table_click_callback, 
                          width=-1, height=TABLE_BUTTON_HEIGHT, tag=button_tag)

                # Apply theme from theme manager if available
                if self.theme_manager:
                    bind_item_theme(button_tag, self.theme_manager.get_theme('table_button'))
                elif self.left_aligned_button_theme:
                    bind_item_theme(button_tag, self.left_aligned_button_theme)

                # Add columns if this table is expanded
                if table_name in self.expanded_tables and table_name in self.table_columns:
                    for column_name, column_type in self.table_columns[table_name]:
                        column_text = f"    {icon_manager.get('column')} {column_name} ({column_type})"
                        column_tag = f"column_{table_name}_{column_name}"
                        add_text(column_text, parent="tables_list", color=COLOR_COLUMN, tag=column_tag)

                        # Apply column text theme if theme manager is available
                        if self.theme_manager:
                            bind_item_theme(column_tag, self.theme_manager.get_theme('column_text'))

        except Exception as e:
            delete_item("tables_list", children_only=True)
            add_text("Error loading tables", parent="tables_list", color=COLOR_ERROR)
            if self.status_callback:
                self.status_callback(f"Failed to rebuild tables list: {str(e)}", True)

    def refresh_tables(self):
        """Refresh the tables list from the database."""
        if not self.db_manager.is_connected:
            # Don't overwrite status messages here - let the caller handle status updates
            # Only update the tables list UI to show disconnected state
            delete_item("tables_list", children_only=True)
            add_text("Connect to see tables", parent="tables_list", color=COLOR_INFO)
            return

        try:
            # Clear expanded tables and cached columns when reconnecting
            self.expanded_tables.clear()
            self.table_columns.clear()

            # Build the initial tables list
            self.rebuild_tables_list()

            tables = self.db_manager.get_tables()
            if self.status_callback:
                self.status_callback(f"Found {len(tables)} tables", False)

        except Exception as e:
            delete_item("tables_list", children_only=True)
            add_text("Error loading tables", parent="tables_list", color=COLOR_ERROR)
            if self.status_callback:
                self.status_callback(f"Failed to list tables: {str(e)}", True)

    def clear_tables(self):
        """Clear the tables list and show disconnected state."""
        self.expanded_tables.clear()
        self.table_columns.clear()

        # Clear tables list
        delete_item("tables_list", children_only=True)
        add_text("Connect to see tables", parent="tables_list", color=COLOR_INFO)


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
            self.table_theme = self.theme_manager.get_theme('table_enhanced')
        else:
            # Fallback theme creation
            with theme() as self.table_theme:
                with theme_component(mvTable):
                    add_theme_style(mvStyleVar_CellPadding, 8, 8)  # Increase cell padding
                    add_theme_style(mvStyleVar_ItemSpacing, 0, 4)  # Add vertical spacing between items

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
            if not result.result_rows:
                if self.status_callback:
                    self.status_callback("Query executed successfully (no results)", False)
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
                        original_cell = str(cell_value) if cell_value is not None else "NULL"
                        
                        # Use selectable instead of text to enable click-to-copy
                        cell_tag = f"query_cell_{self.table_counter}_{row_idx}_{col_idx}"
                        add_selectable(
                            label=formatted_cell,
                            tag=cell_tag,
                            callback=self._copy_cell_to_clipboard,
                            user_data=original_cell  # Original cell content for copying
                        )
            
            if self.status_callback:
                self.status_callback(f"Query executed successfully. Rows returned: {len(rows)}", False)
            
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Query failed: {str(e)}", True)
    
    def _setup_results_table(self, columns, query=None):
        """Setup the results table with the given columns."""
        # Delete existing table if any
        if self.current_table:
            delete_item(self.current_table)
        
        # Create new table with dynamic columns and borders
        self.table_counter += 1
        self.current_table = f"query_result_{self.table_counter}"
        add_table(tag=self.current_table, parent="results_window",
                 borders_innerH=True, borders_innerV=True, borders_outerH=True, borders_outerV=True,
                 header_row=True, scrollX=True, scrollY=True, freeze_rows=1, height=-1,
                 resizable=True)  # Enable column resizing
        
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
            add_table_column(
                label=header_label, 
                parent=self.current_table, 
                init_width_or_weight=250,  # Increased initial width for better readability
                width_stretch=False,       # Don't auto-stretch
                no_resize=False            # Allow manual resizing (this is default but explicit for clarity)
            )

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
                cell_value = val.decode('utf-8', errors='replace')
            except:
                cell_value = str(val)
        elif isinstance(val, str):
            # Ensure string is properly encoded
            try:
                cell_value = val.encode('utf-8', errors='replace').decode('utf-8')
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
            import re
            query_lower = query.lower().strip()
            
            # Look for "FROM table_name" pattern
            from_match = re.search(r'\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_lower)
            if from_match:
                table_name = from_match.group(1)
                
                # Get column information for this table
                try:
                    table_columns = self.db_manager.get_table_columns(table_name)
                    table_column_types = {col_name: col_type for col_name, col_type in table_columns}
                    
                    # Match query result columns with table columns
                    for col in columns:
                        if col in table_column_types:
                            column_types[col] = table_column_types[col]
                except Exception:
                    pass  # If we can't get table info, just skip
        except Exception:
            pass  # If any error in pattern matching, just return empty dict
        
        return column_types


class StatusManager:
    """Manages status messages display."""
    
    theme_manager = None  # Class variable to store theme manager
    
    @classmethod
    def set_theme_manager(cls, theme_manager):
        """Set the theme manager for styling status messages."""
        cls.theme_manager = theme_manager
    
    @staticmethod
    def show_status(message: str, error: bool = False):
        """Display a status message."""
        delete_item("status_text", children_only=True)
        if error:
            # For errors, show in both text and copyable input
            error_text_tag = f"error_text_{time.time()}"
            add_text(message, parent="status_text", color=COLOR_ERROR, tag=error_text_tag)
            if StatusManager.theme_manager:
                bind_item_theme(error_text_tag, StatusManager.theme_manager.get_theme('error_text'))
            
            add_input_text(parent="status_text", default_value=message, readonly=True, 
                          multiline=True, width=-1, height=60)
        else:
            success_text_tag = f"success_text_{time.time()}"
            add_text(message, parent="status_text", color=COLOR_SUCCESS, tag=success_text_tag)
            if StatusManager.theme_manager:
                bind_item_theme(success_text_tag, StatusManager.theme_manager.get_theme('success_text'))
