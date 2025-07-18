"""Query interface component for ClickHouse Client."""

import datetime
import json
import os
import re
import time
from typing import Callable, Optional

from dearpygui.dearpygui import *

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
        self.loading_indicator = None
        self.loading_animation_running = False
        self.last_query_results = None  # Store last query results for JSON export
        self.last_column_names = None  # Store column names for JSON export
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

        # Add default LIMIT if not present
        original_query = query
        query = self._add_default_limit(query)

        # Show a message if we added a default limit
        if query != original_query:
            if self.status_callback:
                self.status_callback("Added default LIMIT 100 to query", False)

        # Show loading animation
        self._show_loading()

        try:
            # Execute query
            result = self.db_manager.execute_query(query)

            # Update loading message for result processing
            self._update_loading_message("Processing results...")

            # Always clear previous results first (loading already cleared them)
            if self.current_table:
                delete_item(self.current_table)
                self.current_table = None

            if not result.result_rows:
                # Hide loading animation for no results case
                self._hide_loading()
                # Clear previous results and hide save button
                self.last_query_results = None
                self.last_column_names = None
                self._hide_save_json_button()
                if self.status_callback:
                    self.status_callback(
                        "Query executed successfully (no results)", False
                    )
                return

            # Get column names and rows
            column_names = result.column_names
            rows = result.result_rows

            # Store results for JSON export
            self.last_query_results = rows
            self.last_column_names = column_names

            # Show the save as JSON button
            self._show_save_json_button()

            # Update loading message for table building
            if len(rows) > 100:
                self._update_loading_message(f"Building table with {len(rows)} rows...")
            else:
                self._update_loading_message("Building table...")

            # Setup table with new columns
            self._setup_results_table(column_names, query)

            # Add rows
            for row_idx, row in enumerate(rows):
                # Update progress for very large result sets
                if len(rows) > 1000 and row_idx > 0 and row_idx % 500 == 0:
                    progress = (row_idx / len(rows)) * 100
                    self._update_loading_message(
                        f"Loading rows... {progress:.0f}% complete"
                    )

                with table_row(parent=self.current_table):
                    for col_idx, cell_value in enumerate(row):
                        # Format cell value for display and get original for copying
                        formatted_cell = self._format_cell_value(cell_value)
                        original_cell = (
                            str(cell_value) if cell_value is not None else "NULL"
                        )

                        # Use regular table cell instead of selectable to allow right-click menus
                        # Store the original cell data as user_data for potential future copy functionality
                        cell_tag = (
                            f"query_cell_{self.table_counter}_{row_idx}_{col_idx}"
                        )

                        # Create table cell with selectable text for copying
                        with table_cell():
                            # Use input_text in readonly mode - allows text selection/copying without interfering with right-click
                            add_input_text(
                                tag=f"cell_input_{cell_tag}",
                                default_value=formatted_cell,
                                readonly=True,  # Read-only allows selection but not editing
                                width=-1,  # Take full available width
                                height=0,  # Auto height based on content
                                no_spaces=False,  # Allow spaces in the text
                                tab_input=False,  # Don't capture tab navigation
                                hint="",  # No hint text
                                multiline=False,  # Single line input
                                user_data=original_cell,  # Store original for reference
                            )

            # Hide loading animation after all results are displayed
            self._hide_loading()

            # Give a small delay to ensure loading is cleared before showing success
            time.sleep(0.01)

            if self.status_callback:
                self.status_callback(
                    f"Query executed successfully. Rows returned: {len(rows)}. Select text and Ctrl+C to copy.",
                    False,
                )

        except Exception as e:
            # Hide loading animation on error
            self._hide_loading()
            # Clear previous results and hide save button
            self.last_query_results = None
            self.last_column_names = None
            self._hide_save_json_button()
            if self.status_callback:
                self.status_callback(f"Query failed: {str(e)}", True)
        finally:
            # Final safety check - ensure loading is always cleared
            if self.loading_indicator:
                try:
                    self._hide_loading()
                except:
                    # Force reset if hiding fails
                    self.loading_indicator = None
                    self.loading_animation_running = False

    def _setup_results_table(self, columns, query=None):
        """Setup the results table with the given columns."""
        # Ensure loading is completely cleared before setting up table
        if self.loading_indicator:
            self._hide_loading()

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
            height=-1,  # Take all available height
            width=-1,  # Take all available width
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

    def _show_loading(self):
        """Show loading animation in the results window."""
        try:
            # Clear any existing results
            if self.current_table and does_item_exist(self.current_table):
                delete_item(self.current_table)
                self.current_table = None

            # Aggressively clear any existing loading indicator
            self._hide_loading()  # Use the improved hide method

            # Additional cleanup - check for any orphaned loading elements
            try:
                current_time = int(time.time())
                for i in range(current_time - 5, current_time + 1):
                    potential_tag = f"loading_indicator_{i}"
                    if does_item_exist(potential_tag):
                        delete_item(potential_tag)
            except:
                pass

            # Create loading indicator with compact design
            self.loading_indicator = f"loading_indicator_{int(time.time())}"
            print(f"Creating new loading indicator: {self.loading_indicator}")

            with group(tag=self.loading_indicator, parent="results_window"):
                add_spacer(height=30)  # Reduced from 80px to 30px

                # Center the loading content
                with group(horizontal=True):
                    add_spacer(width=20)  # Reduced from 50px to 20px
                    with group():
                        # Loading text with emoji - more compact
                        add_text(
                            "⏳ Executing query...",
                            tag=f"{self.loading_indicator}_text",
                            color=(100, 150, 255),
                        )

                        add_spacer(height=8)  # Reduced from 15px to 8px

                        # Progress bar with animation - smaller height
                        add_progress_bar(
                            tag=f"{self.loading_indicator}_progress",
                            default_value=-1.0,  # Indeterminate progress
                            width=400,  # Reduced from 500px to 400px
                            height=18,  # Reduced from 25px to 18px
                            overlay="Please wait...",
                        )

                        add_spacer(height=5)  # Reduced from 10px to 5px

                        # Additional helpful text - smaller and less prominent
                        add_text(
                            "Processing...",  # Shorter text
                            tag=f"{self.loading_indicator}_help",
                            color=(120, 120, 120),  # Lighter gray
                        )

            # Start loading animation
            self.loading_animation_running = True

            if self.status_callback:
                self.status_callback("Executing query...", False)

        except Exception as e:
            print(f"Error showing loading indicator: {e}")
            # If we can't show loading, at least clear the state
            self.loading_indicator = None
            self.loading_animation_running = False

    def _update_loading_message(self, message: str):
        """Update the loading message while keeping the animation running."""
        try:
            if (
                self.loading_indicator
                and self.loading_animation_running
                and does_item_exist(f"{self.loading_indicator}_text")
            ):
                set_value(f"{self.loading_indicator}_text", f"⏳ {message}")
        except Exception as e:
            print(f"Error updating loading message: {e}")
            # If we can't update the message, it might mean the loading indicator was cleared
            # Reset the state to prevent further issues
            if not does_item_exist(self.loading_indicator or ""):
                self.loading_indicator = None
                self.loading_animation_running = False

    def _hide_loading(self):
        """Hide loading animation."""
        try:
            self.loading_animation_running = False

            if self.loading_indicator:
                # More aggressive cleanup approach
                loading_tag = self.loading_indicator

                # Try to delete the main group first
                try:
                    if does_item_exist(loading_tag):
                        delete_item(loading_tag)
                        print(f"Successfully deleted loading indicator: {loading_tag}")
                except Exception as delete_error:
                    print(f"Error deleting main loading group: {delete_error}")

                    # If main group deletion fails, try to delete individual components
                    component_tags = [
                        f"{loading_tag}_text",
                        f"{loading_tag}_progress",
                        f"{loading_tag}_help",
                        loading_tag,  # Try the main tag again
                    ]

                    for tag in component_tags:
                        try:
                            if does_item_exist(tag):
                                delete_item(tag)
                                print(f"Deleted component: {tag}")
                        except Exception as comp_error:
                            print(f"Failed to delete component {tag}: {comp_error}")

                # Force reset the loading indicator reference
                self.loading_indicator = None

            # Double-check and force cleanup any remaining loading elements
            # This is a fallback in case the above doesn't work
            try:
                # Try to find and delete any remaining loading indicators
                current_time = int(time.time())
                for i in range(
                    current_time - 10, current_time + 1
                ):  # Check last 10 seconds
                    potential_tag = f"loading_indicator_{i}"
                    if does_item_exist(potential_tag):
                        delete_item(potential_tag)
                        print(f"Force deleted stale loading indicator: {potential_tag}")
            except Exception as cleanup_error:
                print(f"Error in force cleanup: {cleanup_error}")

        except Exception as e:
            print(f"Error hiding loading indicator: {e}")
        finally:
            # Always reset the state, even if deletion fails
            self.loading_indicator = None
            self.loading_animation_running = False
            print("Loading state reset complete")

    def _add_default_limit(self, query: str) -> str:
        """Add default LIMIT clause if not already present in the query."""
        try:
            # Clean the query for analysis
            query_clean = query.strip()
            query_lower = query_clean.lower()

            # Check if it's a SELECT query (we only add LIMIT to SELECT queries)
            if not query_lower.strip().startswith("select"):
                return query  # Not a SELECT query, return as-is

            # Check if query already has a LIMIT clause
            # Look for LIMIT followed by number, optionally with OFFSET
            limit_patterns = [
                r"\blimit\s+\d+\b",  # LIMIT 100
                r"\blimit\s+\d+\s+offset\s+\d+\b",  # LIMIT 100 OFFSET 50
                r"\boffset\s+\d+\s+limit\s+\d+\b",  # OFFSET 50 LIMIT 100 (some SQL dialects)
            ]

            for pattern in limit_patterns:
                if re.search(pattern, query_lower):
                    return query  # Query already has LIMIT, return as-is

            # Special case: Check for subqueries that might have LIMIT
            # If the main query is complex, be more conservative
            if query_lower.count("select") > 1:
                # Multiple SELECT statements (subqueries), be more careful
                # Only add LIMIT if we're confident it's the main outer query
                if not re.search(r"\)\s*$", query_clean.rstrip(";")):
                    # Doesn't end with ), so likely not a subquery wrapper
                    pass  # Continue to add LIMIT
                else:
                    return query  # Looks like a complex query, don't modify

            # Add default LIMIT of 100
            if query_clean.endswith(";"):
                # Remove semicolon, add LIMIT, then add semicolon back
                query_with_limit = query_clean[:-1] + " LIMIT 100;"
            else:
                # Just add LIMIT
                query_with_limit = query_clean + " LIMIT 100"

            return query_with_limit

        except Exception as e:
            print(f"Error adding default limit: {e}")
            return query  # Return original query if any error occurs

    def _show_save_json_button(self):
        """Show the save as JSON button after a successful query."""
        try:
            # Check if button already exists
            if does_item_exist("save_json_button"):
                configure_item("save_json_button", show=True)
            else:
                # Create the button (this should normally be created in UI setup)
                print("Warning: save_json_button not found in UI")
        except Exception as e:
            print(f"Error showing save JSON button: {e}")

    def _hide_save_json_button(self):
        """Hide the save as JSON button when there are no results."""
        try:
            if does_item_exist("save_json_button"):
                configure_item("save_json_button", show=False)
        except Exception as e:
            print(f"Error hiding save JSON button: {e}")

    def save_as_json_callback(self, sender, data):
        """Save query results as JSON file."""
        if not self.last_query_results or not self.last_column_names:
            if self.status_callback:
                self.status_callback("No query results to save", True)
            return

        try:
            # Show file dialog for user to choose save location
            self._show_save_file_dialog()

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error opening file dialog: {str(e)}", True)
            print(f"Error in save_as_json_callback: {e}")  # Debug logging

    def _show_save_file_dialog(self):
        """Show file dialog for saving JSON file."""
        # Generate default filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"query_results_{timestamp}.json"

        # Try to determine default directory
        home_dir = os.path.expanduser("~")
        downloads_dir = os.path.join(home_dir, "Downloads")

        if os.path.exists(downloads_dir):
            default_path = downloads_dir
        elif os.path.exists(home_dir):
            default_path = home_dir
        else:
            default_path = os.getcwd()

        # Create file dialog
        with file_dialog(
            directory_selector=False,
            show=True,
            callback=self._save_file_dialog_callback,
            tag="json_save_file_dialog",
            width=700,
            height=400,
            default_path=default_path,
            default_filename=default_filename,
        ):
            add_file_extension("JSON files (*.json){.json}", color=(0, 255, 0, 255))
            add_file_extension("All files (*.*){.*}", color=(255, 255, 255, 255))

    def _save_file_dialog_callback(self, sender, app_data):
        """Handle file dialog callback when user selects a file."""
        try:
            # Get the selected file path
            file_path = app_data["file_path_name"]

            if not file_path:
                if self.status_callback:
                    self.status_callback("Save cancelled by user", False)
                return

            # Ensure the file has .json extension
            if not file_path.lower().endswith(".json"):
                file_path += ".json"

            # Convert results to JSON format
            json_data = self._convert_results_to_json()

            # Write JSON to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

            if self.status_callback:
                self.status_callback(
                    f"Query results saved to {file_path} ({len(json_data)} rows)", False
                )

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error saving JSON file: {str(e)}", True)
            print(f"Error in _save_file_dialog_callback: {e}")  # Debug logging

    def _convert_results_to_json(self):
        """Convert query results to JSON format."""
        json_data = []
        for row in self.last_query_results:
            row_dict = {}
            for col_idx, column_name in enumerate(self.last_column_names):
                # Handle different data types for JSON serialization
                cell_value = row[col_idx] if col_idx < len(row) else None

                # Convert non-JSON serializable types
                if cell_value is None:
                    row_dict[column_name] = None
                elif isinstance(cell_value, bytes):
                    # Convert bytes to string
                    try:
                        row_dict[column_name] = cell_value.decode(
                            "utf-8", errors="replace"
                        )
                    except:
                        row_dict[column_name] = str(cell_value)
                else:
                    row_dict[column_name] = cell_value

            json_data.append(row_dict)

        return json_data
