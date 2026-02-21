"""Query interface component for ClickHouse Client."""

import datetime
import json
import os
import re
import time
from collections.abc import Callable
from dataclasses import dataclass

from dearpygui.dearpygui import *

from config import DEFAULT_TAB_LABEL, MAX_QUERY_TABS, QUERY_INPUT_HEIGHT
from database import ConnectionPool, DatabaseManager
from icon_manager import icon_manager


class QueryInterface:
    """Manages the query interface and results display."""

    def __init__(
        self, db_manager: DatabaseManager, theme_manager=None, async_worker=None
    ):
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.async_worker = async_worker
        self.current_table: str | None = None
        self.table_counter = 0
        self.status_callback: Callable[[str, bool], None] | None = None
        self.table_theme = None
        self.loading_indicator = None
        self.loading_animation_running = False
        self.last_query_results = None  # Store last query results for JSON export
        self.last_column_names = None  # Store column names for JSON export
        self._query_running = False  # Guard against concurrent queries
        self._setup_table_theme()

    def _setup_table_theme(self):
        """Setup theme for results tables with increased row height."""
        if self.theme_manager:
            # Use theme manager's table theme
            self.table_theme = self.theme_manager.get_theme("table_enhanced")
        else:
            # Fallback theme creation
            with theme() as self.table_theme, theme_component(mvTable):
                add_theme_style(mvStyleVar_CellPadding, 8, 8)  # Increase cell padding
                add_theme_style(
                    mvStyleVar_ItemSpacing, 0, 4
                )  # Add vertical spacing between items

    def set_status_callback(self, callback: Callable[[str, bool], None]):
        """Set callback for status messages."""
        self.status_callback = callback

    def run_query_callback(self, sender, data):
        """Execute the query from the input field (non-blocking)."""
        if self._query_running:
            if self.status_callback:
                self.status_callback("A query is already running, please wait...", True)
            return

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

        if query != original_query and self.status_callback:
            self.status_callback("Added default LIMIT 100 to query", False)

        # Show loading animation on the main thread immediately
        self._show_loading()
        self._query_running = True

        if self.async_worker:
            q = query  # capture for closure
            self.async_worker.run_async(
                task=lambda: self._execute_query_task(q),
                on_done=self._on_query_done,
                on_error=self._on_query_error,
            )
        else:
            # Synchronous fallback (no async_worker supplied)
            try:
                result = self._execute_query_task(query)
                self._on_query_done(result)
            except Exception as e:
                self._on_query_error(e)

    # ------------------------------------------------------------------
    # Background task (runs on worker thread — NO DearPyGUI calls here)
    # ------------------------------------------------------------------

    def _execute_query_task(self, query: str):
        """Run in background thread: execute query and fetch column types."""
        result = self.db_manager.execute_query(query)
        column_types = self._get_column_types_from_query(query, result.column_names)
        return result, column_types

    # ------------------------------------------------------------------
    # Main-thread callbacks (called via AsyncWorker queue)
    # ------------------------------------------------------------------

    def _on_query_done(self, payload):
        """Called on the main thread when the query completes successfully."""
        self._query_running = False
        result, column_types = payload

        self._update_loading_message("Processing results...")

        # Always clear previous results first
        if self.current_table:
            delete_item(self.current_table)
            self.current_table = None

        if not result.result_rows:
            self._hide_loading()
            self.last_query_results = None
            self.last_column_names = None
            self._hide_save_json_button()
            if self.status_callback:
                self.status_callback("Query executed successfully (no results)", False)
            return

        column_names = result.column_names
        rows = result.result_rows

        # Store results for JSON export
        self.last_query_results = rows
        self.last_column_names = column_names

        self._show_save_json_button()

        if len(rows) > 100:
            self._update_loading_message(f"Building table with {len(rows)} rows...")
        else:
            self._update_loading_message("Building table...")

        # Setup table with pre-fetched column types (no additional DB calls)
        self._setup_results_table(column_names, column_types)

        # Add rows
        for row_idx, row in enumerate(rows):
            with table_row(parent=self.current_table):
                for col_idx, cell_value in enumerate(row):
                    formatted_cell = self._format_cell_value(cell_value)
                    original_cell = (
                        str(cell_value) if cell_value is not None else "NULL"
                    )

                    cell_tag = f"query_cell_{self.table_counter}_{row_idx}_{col_idx}"

                    with table_cell():
                        add_input_text(
                            tag=f"cell_input_{cell_tag}",
                            default_value=formatted_cell,
                            readonly=True,
                            width=-1,
                            height=0,
                            no_spaces=False,
                            tab_input=False,
                            hint="",
                            multiline=False,
                            user_data=original_cell,
                        )

        self._hide_loading()

        if self.status_callback:
            self.status_callback(
                f"Query executed successfully. Rows returned: {len(rows)}. Select text and Ctrl+C to copy.",
                False,
            )

    def _on_query_error(self, e: Exception):
        """Called on the main thread when the query raises an exception."""
        self._query_running = False
        self._hide_loading()
        self.last_query_results = None
        self.last_column_names = None
        self._hide_save_json_button()
        if self.status_callback:
            self.status_callback(f"Query failed: {str(e)}", True)

    # ------------------------------------------------------------------
    # Table setup
    # ------------------------------------------------------------------

    def _setup_results_table(self, columns, column_types=None):
        """Setup the results table with the given columns and pre-fetched types."""
        if column_types is None:
            column_types = {}

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
            height=-1,
            width=-1,
            resizable=True,
            policy=mvTable_SizingFixedFit,
        )

        if self.table_theme:
            bind_item_theme(self.current_table, self.table_theme)

        # Add columns with wider widths and type information
        for col in columns:
            col_type = column_types.get(col, "")
            if col_type:
                header_label = f"{col_type}\n{col}"
            else:
                header_label = str(col)
            column_tag = f"col_{self.current_table}_{col}"
            add_table_column(
                tag=column_tag,
                label=header_label,
                parent=self.current_table,
                init_width_or_weight=350,
                width_stretch=False,
                width_fixed=False,
                no_resize=False,
            )

        # Force all column widths after table creation
        for col in columns:
            column_tag = f"col_{self.current_table}_{col}"
            try:
                configure_item(column_tag, width=350)
            except Exception:
                try:
                    set_item_width(column_tag, 350)
                except Exception:
                    pass

    def _copy_cell_to_clipboard(self, sender, app_data, user_data):
        """Copy cell content to clipboard when clicked."""
        try:
            cell_text = user_data if user_data else ""
            set_clipboard_text(cell_text)
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
            try:
                cell_value = val.decode("utf-8", errors="replace")
            except Exception:
                cell_value = str(val)
        elif isinstance(val, str):
            try:
                cell_value = val.encode("utf-8", errors="replace").decode("utf-8")
            except Exception:
                cell_value = str(val)
        else:
            cell_value = str(val)

        return cell_value

    def _get_column_types_from_query(self, query, columns):
        """Try to extract column types from query context.

        NOTE: This method calls db_manager.get_table_columns() and must only
        be called from a background thread (via _execute_query_task).
        """
        column_types = {}

        try:
            query_lower = query.lower().strip()

            from_match = re.search(r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)", query_lower)
            if from_match:
                table_name = from_match.group(1)

                try:
                    table_columns = self.db_manager.get_table_columns(table_name)
                    table_column_types = {
                        col_name: col_type for col_name, col_type in table_columns
                    }

                    for col in columns:
                        if col in table_column_types:
                            column_types[col] = table_column_types[col]
                except Exception:
                    pass
        except Exception:
            pass

        return column_types

    def _show_loading(self):
        """Show loading animation in the results window."""
        try:
            # Clear any existing results
            if self.current_table and does_item_exist(self.current_table):
                delete_item(self.current_table)
                self.current_table = None

            # Aggressively clear any existing loading indicator
            self._hide_loading()

            # Additional cleanup - check for any orphaned loading elements
            try:
                current_time = int(time.time())
                for i in range(current_time - 5, current_time + 1):
                    potential_tag = f"loading_indicator_{i}"
                    if does_item_exist(potential_tag):
                        delete_item(potential_tag)
            except Exception:
                pass

            self.loading_indicator = f"loading_indicator_{int(time.time())}"
            print(f"Creating new loading indicator: {self.loading_indicator}")

            with group(tag=self.loading_indicator, parent="results_window"):
                add_spacer(height=30)

                with group(horizontal=True):
                    add_spacer(width=20)
                    with group():
                        add_text(
                            "⏳ Executing query...",
                            tag=f"{self.loading_indicator}_text",
                            color=(100, 150, 255),
                        )

                        add_spacer(height=8)

                        add_progress_bar(
                            tag=f"{self.loading_indicator}_progress",
                            default_value=-1.0,  # Indeterminate progress
                            width=400,
                            height=18,
                            overlay="Please wait...",
                        )

                        add_spacer(height=5)

                        add_text(
                            "Processing...",
                            tag=f"{self.loading_indicator}_help",
                            color=(120, 120, 120),
                        )

            self.loading_animation_running = True

            if self.status_callback:
                self.status_callback("Executing query...", False)

        except Exception as e:
            print(f"Error showing loading indicator: {e}")
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
            if not does_item_exist(self.loading_indicator or ""):
                self.loading_indicator = None
                self.loading_animation_running = False

    def _hide_loading(self):
        """Hide loading animation."""
        try:
            self.loading_animation_running = False

            if self.loading_indicator:
                loading_tag = self.loading_indicator

                try:
                    if does_item_exist(loading_tag):
                        delete_item(loading_tag)
                        print(f"Successfully deleted loading indicator: {loading_tag}")
                except Exception as delete_error:
                    print(f"Error deleting main loading group: {delete_error}")

                    component_tags = [
                        f"{loading_tag}_text",
                        f"{loading_tag}_progress",
                        f"{loading_tag}_help",
                        loading_tag,
                    ]

                    for tag in component_tags:
                        try:
                            if does_item_exist(tag):
                                delete_item(tag)
                                print(f"Deleted component: {tag}")
                        except Exception as comp_error:
                            print(f"Failed to delete component {tag}: {comp_error}")

                self.loading_indicator = None

            try:
                current_time = int(time.time())
                for i in range(current_time - 10, current_time + 1):
                    potential_tag = f"loading_indicator_{i}"
                    if does_item_exist(potential_tag):
                        delete_item(potential_tag)
                        print(f"Force deleted stale loading indicator: {potential_tag}")
            except Exception as cleanup_error:
                print(f"Error in force cleanup: {cleanup_error}")

        except Exception as e:
            print(f"Error hiding loading indicator: {e}")
        finally:
            self.loading_indicator = None
            self.loading_animation_running = False
            print("Loading state reset complete")

    def _add_default_limit(self, query: str) -> str:
        """Add default LIMIT clause if not already present in the query."""
        try:
            query_clean = query.strip()
            query_lower = query_clean.lower()

            if not query_lower.strip().startswith("select"):
                return query

            limit_patterns = [
                r"\blimit\s+\d+\b",
                r"\blimit\s+\d+\s+offset\s+\d+\b",
                r"\boffset\s+\d+\s+limit\s+\d+\b",
            ]

            for pattern in limit_patterns:
                if re.search(pattern, query_lower):
                    return query

            if query_lower.count("select") > 1:
                if not re.search(r"\)\s*$", query_clean.rstrip(";")):
                    pass
                else:
                    return query

            if query_clean.endswith(";"):
                query_with_limit = query_clean[:-1] + " LIMIT 100;"
            else:
                query_with_limit = query_clean + " LIMIT 100"

            return query_with_limit

        except Exception as e:
            print(f"Error adding default limit: {e}")
            return query

    def _show_save_json_button(self):
        """Show the save as JSON button after a successful query."""
        try:
            if does_item_exist("save_json_button"):
                configure_item("save_json_button", show=True)
            else:
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
            self._show_save_file_dialog()
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error opening file dialog: {str(e)}", True)
            print(f"Error in save_as_json_callback: {e}")

    def _show_save_file_dialog(self):
        """Show file dialog for saving JSON file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"query_results_{timestamp}.json"

        home_dir = os.path.expanduser("~")
        downloads_dir = os.path.join(home_dir, "Downloads")

        if os.path.exists(downloads_dir):
            default_path = downloads_dir
        elif os.path.exists(home_dir):
            default_path = home_dir
        else:
            default_path = os.getcwd()

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
            file_path = app_data["file_path_name"]

            if not file_path:
                if self.status_callback:
                    self.status_callback("Save cancelled by user", False)
                return

            if not file_path.lower().endswith(".json"):
                file_path += ".json"

            json_data = self._convert_results_to_json()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

            if self.status_callback:
                self.status_callback(
                    f"Query results saved to {file_path} ({len(json_data)} rows)", False
                )

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error saving JSON file: {str(e)}", True)
            print(f"Error in _save_file_dialog_callback: {e}")

    def _convert_results_to_json(self):
        """Convert query results to JSON format."""
        json_data = []
        for row in self.last_query_results:
            row_dict = {}
            for col_idx, column_name in enumerate(self.last_column_names):
                cell_value = row[col_idx] if col_idx < len(row) else None

                if cell_value is None:
                    row_dict[column_name] = None
                elif isinstance(cell_value, bytes):
                    try:
                        row_dict[column_name] = cell_value.decode(
                            "utf-8", errors="replace"
                        )
                    except Exception:
                        row_dict[column_name] = str(cell_value)
                else:
                    row_dict[column_name] = cell_value

            json_data.append(row_dict)

        return json_data


# ---------------------------------------------------------------------------
# Per-tab state
# ---------------------------------------------------------------------------


@dataclass
class QueryTabState:
    """All mutable state for a single query tab."""

    tab_id: int
    label: str
    tab_tag: str
    input_tag: str
    run_btn_tag: str
    save_btn_tag: str
    results_window_tag: str

    query_running: bool = False
    current_table_tag: str | None = None
    table_counter: int = 0
    last_query_results: list | None = None
    last_column_names: list | None = None
    loading_indicator: str | None = None
    loading_animation_running: bool = False


# ---------------------------------------------------------------------------
# Tabbed query interface
# ---------------------------------------------------------------------------


class TabbedQueryInterface:
    """Manages multiple independent query tabs, each with its own DB connection."""

    def __init__(
        self,
        connection_pool: ConnectionPool,
        db_manager: DatabaseManager,
        theme_manager=None,
        async_worker=None,
    ):
        self.connection_pool = connection_pool
        self.db_manager = db_manager  # used only for get_table_columns() (metadata)
        self.theme_manager = theme_manager
        self.async_worker = async_worker
        self.status_callback: Callable[[str, bool], None] | None = None

        self._tabs: dict[int, QueryTabState] = {}
        self._tab_counter = 0
        self.table_theme = None
        self._setup_table_theme()

    def _setup_table_theme(self):
        if self.theme_manager:
            self.table_theme = self.theme_manager.get_theme("table_enhanced")
        else:
            with theme() as self.table_theme, theme_component(mvTable):
                add_theme_style(mvStyleVar_CellPadding, 8, 8)
                add_theme_style(mvStyleVar_ItemSpacing, 0, 4)

    def set_status_callback(self, callback: Callable[[str, bool], None]):
        self.status_callback = callback

    # ------------------------------------------------------------------
    # Tab lifecycle
    # ------------------------------------------------------------------

    def create_tab(self) -> int:
        """Create a new query tab. Returns tab_id, or -1 if at limit."""
        if len(self._tabs) >= MAX_QUERY_TABS:
            if self.status_callback:
                self.status_callback(f"Maximum of {MAX_QUERY_TABS} tabs allowed", True)
            return -1

        tab_id = self._tab_counter
        self._tab_counter += 1

        label = f"{DEFAULT_TAB_LABEL} {tab_id + 1}"
        state = QueryTabState(
            tab_id=tab_id,
            label=label,
            tab_tag=f"query_tab_{tab_id}",
            input_tag=f"query_input_{tab_id}",
            run_btn_tag=f"run_query_btn_{tab_id}",
            save_btn_tag=f"save_json_btn_{tab_id}",
            results_window_tag=f"results_window_{tab_id}",
        )
        self._tabs[tab_id] = state
        self._build_tab_ui(state)
        set_value("query_tab_bar", state.tab_tag)
        return tab_id

    def _build_tab_ui(self, state: QueryTabState):
        """Build the DPG UI for a single tab (must be called on main thread)."""
        with tab(
            tag=state.tab_tag,
            parent="query_tab_bar",
            closable=True,
            label=state.label,
        ):
            add_input_text(
                tag=state.input_tag,
                multiline=True,
                width=-1,
                height=QUERY_INPUT_HEIGHT,
            )
            if self.theme_manager:
                bind_item_theme(
                    state.input_tag,
                    self.theme_manager.get_theme("input_enhanced"),
                )

            add_button(
                label=f"{icon_manager.get('query')} Run Query",
                tag=state.run_btn_tag,
                callback=self._make_run_callback(state.tab_id),
            )
            if self.theme_manager:
                bind_item_theme(
                    state.run_btn_tag,
                    self.theme_manager.get_theme("button_primary"),
                )

            add_button(
                label=f"{icon_manager.get('export')} Save as JSON",
                tag=state.save_btn_tag,
                show=False,
                callback=self._make_save_callback(state.tab_id),
            )
            if self.theme_manager:
                bind_item_theme(
                    state.save_btn_tag,
                    self.theme_manager.get_theme("button_primary"),
                )

            add_separator()

            with child_window(
                label=f"{icon_manager.get('table')} Results",
                tag=state.results_window_tag,
                border=True,
                height=-1,
            ):
                pass

    def _make_run_callback(self, tab_id: int):
        def callback(sender, data):
            self._run_query_for_tab(tab_id)

        return callback

    def _make_save_callback(self, tab_id: int):
        def callback(sender, data):
            self._save_as_json_for_tab(tab_id)

        return callback

    def poll_closed_tabs(self):
        """Called each frame to detect tabs closed via the DPG X button."""
        closed_ids = [
            tab_id
            for tab_id, state in list(self._tabs.items())
            if not does_item_exist(state.tab_tag) or not is_item_shown(state.tab_tag)
        ]
        for tab_id in closed_ids:
            self._close_tab_state(tab_id)

        # Enforce minimum 1 tab
        if len(self._tabs) == 0:
            self.create_tab()

    def _close_tab_state(self, tab_id: int):
        """Clean up state for a tab that has been closed."""
        state = self._tabs.pop(tab_id, None)
        if state is None:
            return
        if does_item_exist(state.tab_tag):
            delete_item(state.tab_tag)
        self.connection_pool.release(tab_id)

    def close_tab(self, tab_id: int):
        """Programmatically close a tab (also deletes its DPG item)."""
        state = self._tabs.pop(tab_id, None)
        if state is None:
            return
        if does_item_exist(state.tab_tag):
            delete_item(state.tab_tag)
        self.connection_pool.release(tab_id)

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    def _run_query_for_tab(self, tab_id: int):
        state = self._tabs.get(tab_id)
        if state is None:
            return

        if state.query_running:
            if self.status_callback:
                self.status_callback(
                    "A query is already running in this tab, please wait...", True
                )
            return

        if not self.connection_pool.is_configured:
            if self.status_callback:
                self.status_callback("Not connected to database", True)
            return

        query = get_value(state.input_tag).strip()
        if not query:
            if self.status_callback:
                self.status_callback("Query is empty", True)
            return

        original_query = query
        query = self._add_default_limit(query)
        if query != original_query and self.status_callback:
            self.status_callback("Added default LIMIT 100 to query", False)

        self._show_loading(state)
        state.query_running = True

        q = query
        if self.async_worker:
            self.async_worker.run_async(
                task=lambda: self._execute_query_task(tab_id, q),
                on_done=lambda payload: self._on_query_done(tab_id, payload),
                on_error=lambda e: self._on_query_error(tab_id, e),
            )
        else:
            try:
                result = self._execute_query_task(tab_id, q)
                self._on_query_done(tab_id, result)
            except Exception as e:
                self._on_query_error(tab_id, e)

    def _execute_query_task(self, tab_id: int, query: str):
        """Background thread: execute query and fetch column types."""
        result = self.connection_pool.execute_query(tab_id, query)
        column_types = self._get_column_types_from_query(query, result.column_names)
        return result, column_types

    def _on_query_done(self, tab_id: int, payload):
        """Main-thread callback when query completes successfully."""
        state = self._tabs.get(tab_id)
        if state is None:
            return

        state.query_running = False
        result, column_types = payload

        self._update_loading_message(state, "Processing results...")

        if state.current_table_tag and does_item_exist(state.current_table_tag):
            delete_item(state.current_table_tag)
            state.current_table_tag = None

        if not result.result_rows:
            self._hide_loading(state)
            state.last_query_results = None
            state.last_column_names = None
            if does_item_exist(state.save_btn_tag):
                configure_item(state.save_btn_tag, show=False)
            if self.status_callback:
                self.status_callback("Query executed successfully (no results)", False)
            return

        column_names = result.column_names
        rows = result.result_rows
        state.last_query_results = rows
        state.last_column_names = column_names

        if does_item_exist(state.save_btn_tag):
            configure_item(state.save_btn_tag, show=True)

        if len(rows) > 100:
            self._update_loading_message(
                state, f"Building table with {len(rows)} rows..."
            )
        else:
            self._update_loading_message(state, "Building table...")

        self._setup_results_table(state, column_names, column_types)

        for row_idx, row in enumerate(rows):
            with table_row(parent=state.current_table_tag):
                for col_idx, cell_value in enumerate(row):
                    formatted_cell = self._format_cell_value(cell_value)
                    original_cell = (
                        str(cell_value) if cell_value is not None else "NULL"
                    )
                    cell_tag = f"query_cell_{state.tab_id}_{state.table_counter}_{row_idx}_{col_idx}"
                    with table_cell():
                        add_input_text(
                            tag=f"cell_input_{cell_tag}",
                            default_value=formatted_cell,
                            readonly=True,
                            width=-1,
                            height=0,
                            no_spaces=False,
                            tab_input=False,
                            hint="",
                            multiline=False,
                            user_data=original_cell,
                        )

        self._hide_loading(state)

        if self.status_callback:
            self.status_callback(
                f"Query executed successfully. Rows returned: {len(rows)}. Select text and Ctrl+C to copy.",
                False,
            )

    def _on_query_error(self, tab_id: int, e: Exception):
        """Main-thread callback when query raises an exception."""
        state = self._tabs.get(tab_id)
        if state is None:
            return
        state.query_running = False
        self._hide_loading(state)
        state.last_query_results = None
        state.last_column_names = None
        if does_item_exist(state.save_btn_tag):
            configure_item(state.save_btn_tag, show=False)
        if self.status_callback:
            self.status_callback(f"Query failed: {str(e)}", True)

    # ------------------------------------------------------------------
    # Table setup
    # ------------------------------------------------------------------

    def _setup_results_table(self, state: QueryTabState, columns, column_types=None):
        if column_types is None:
            column_types = {}

        if state.loading_indicator:
            self._hide_loading(state)

        state.table_counter += 1
        state.current_table_tag = f"query_result_{state.tab_id}_{state.table_counter}"

        add_table(
            tag=state.current_table_tag,
            parent=state.results_window_tag,
            borders_innerH=True,
            borders_innerV=True,
            borders_outerH=True,
            borders_outerV=True,
            header_row=True,
            scrollX=True,
            scrollY=True,
            freeze_rows=1,
            height=-1,
            width=-1,
            resizable=True,
            policy=mvTable_SizingFixedFit,
        )

        if self.table_theme:
            bind_item_theme(state.current_table_tag, self.table_theme)

        for col in columns:
            col_type = column_types.get(col, "")
            header_label = f"{col_type}\n{col}" if col_type else str(col)
            column_tag = f"col_{state.current_table_tag}_{col}"
            add_table_column(
                tag=column_tag,
                label=header_label,
                parent=state.current_table_tag,
                init_width_or_weight=350,
                width_stretch=False,
                width_fixed=False,
                no_resize=False,
            )

        for col in columns:
            column_tag = f"col_{state.current_table_tag}_{col}"
            try:
                configure_item(column_tag, width=350)
            except Exception:
                try:
                    set_item_width(column_tag, 350)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Loading indicator (per-tab)
    # ------------------------------------------------------------------

    def _show_loading(self, state: QueryTabState):
        self._hide_loading(state)

        if state.current_table_tag and does_item_exist(state.current_table_tag):
            delete_item(state.current_table_tag)
            state.current_table_tag = None

        ts = int(time.time())
        state.loading_indicator = f"loading_{state.tab_id}_{ts}"

        try:
            with group(tag=state.loading_indicator, parent=state.results_window_tag):
                add_spacer(height=30)
                with group(horizontal=True):
                    add_spacer(width=20)
                    with group():
                        add_text(
                            "⏳ Executing query...",
                            tag=f"{state.loading_indicator}_text",
                            color=(100, 150, 255),
                        )
                        add_spacer(height=8)
                        add_progress_bar(
                            tag=f"{state.loading_indicator}_progress",
                            default_value=-1.0,
                            width=400,
                            height=18,
                            overlay="Please wait...",
                        )
                        add_spacer(height=5)
                        add_text(
                            "Processing...",
                            tag=f"{state.loading_indicator}_help",
                            color=(120, 120, 120),
                        )
            state.loading_animation_running = True
            if self.status_callback:
                self.status_callback("Executing query...", False)
        except Exception as e:
            print(f"Error showing loading indicator: {e}")
            state.loading_indicator = None
            state.loading_animation_running = False

    def _update_loading_message(self, state: QueryTabState, message: str):
        try:
            if (
                state.loading_indicator
                and state.loading_animation_running
                and does_item_exist(f"{state.loading_indicator}_text")
            ):
                set_value(f"{state.loading_indicator}_text", f"⏳ {message}")
        except Exception as e:
            print(f"Error updating loading message: {e}")

    def _hide_loading(self, state: QueryTabState):
        state.loading_animation_running = False
        if state.loading_indicator:
            try:
                if does_item_exist(state.loading_indicator):
                    delete_item(state.loading_indicator)
            except Exception as e:
                print(f"Error hiding loading indicator: {e}")
            state.loading_indicator = None

    # ------------------------------------------------------------------
    # Save as JSON
    # ------------------------------------------------------------------

    def _save_as_json_for_tab(self, tab_id: int):
        state = self._tabs.get(tab_id)
        if state is None:
            return
        if not state.last_query_results or not state.last_column_names:
            if self.status_callback:
                self.status_callback("No query results to save", True)
            return
        self._show_save_file_dialog(state)

    def _show_save_file_dialog(self, state: QueryTabState):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"query_results_{timestamp}.json"
        home_dir = os.path.expanduser("~")
        downloads_dir = os.path.join(home_dir, "Downloads")
        if os.path.exists(downloads_dir):
            default_path = downloads_dir
        elif os.path.exists(home_dir):
            default_path = home_dir
        else:
            default_path = os.getcwd()

        dialog_tag = f"json_save_file_dialog_{state.tab_id}"
        if does_item_exist(dialog_tag):
            delete_item(dialog_tag)

        with file_dialog(
            directory_selector=False,
            show=True,
            callback=lambda s, d: self._save_file_dialog_callback(s, d, state),
            tag=dialog_tag,
            width=700,
            height=400,
            default_path=default_path,
            default_filename=default_filename,
        ):
            add_file_extension("JSON files (*.json){.json}", color=(0, 255, 0, 255))
            add_file_extension("All files (*.*){.*}", color=(255, 255, 255, 255))

    def _save_file_dialog_callback(self, sender, app_data, state: QueryTabState):
        try:
            file_path = app_data["file_path_name"]
            if not file_path:
                if self.status_callback:
                    self.status_callback("Save cancelled by user", False)
                return
            if not file_path.lower().endswith(".json"):
                file_path += ".json"
            json_data = self._convert_results_to_json(state)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
            if self.status_callback:
                self.status_callback(
                    f"Query results saved to {file_path} ({len(json_data)} rows)",
                    False,
                )
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error saving JSON file: {str(e)}", True)

    def _convert_results_to_json(self, state: QueryTabState):
        json_data = []
        for row in state.last_query_results:
            row_dict = {}
            for col_idx, column_name in enumerate(state.last_column_names):
                cell_value = row[col_idx] if col_idx < len(row) else None
                if cell_value is None:
                    row_dict[column_name] = None
                elif isinstance(cell_value, bytes):
                    try:
                        row_dict[column_name] = cell_value.decode(
                            "utf-8", errors="replace"
                        )
                    except Exception:
                        row_dict[column_name] = str(cell_value)
                else:
                    row_dict[column_name] = cell_value
            json_data.append(row_dict)
        return json_data

    # ------------------------------------------------------------------
    # Helpers (shared with QueryInterface logic)
    # ------------------------------------------------------------------

    def _get_column_types_from_query(self, query, columns):
        """Fetch column types from DB metadata. Call from background thread only."""
        column_types = {}
        try:
            query_lower = query.lower().strip()
            from_match = re.search(r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)", query_lower)
            if from_match:
                table_name = from_match.group(1)
                try:
                    table_columns = self.db_manager.get_table_columns(table_name)
                    table_column_types = {
                        col_name: col_type for col_name, col_type in table_columns
                    }
                    for col in columns:
                        if col in table_column_types:
                            column_types[col] = table_column_types[col]
                except Exception:
                    pass
        except Exception:
            pass
        return column_types

    @staticmethod
    def _format_cell_value(val) -> str:
        if val is None:
            return "NULL"
        elif isinstance(val, bytes):
            try:
                return val.decode("utf-8", errors="replace")
            except Exception:
                return str(val)
        elif isinstance(val, str):
            try:
                return val.encode("utf-8", errors="replace").decode("utf-8")
            except Exception:
                return str(val)
        return str(val)

    @staticmethod
    def _add_default_limit(query: str) -> str:
        try:
            query_clean = query.strip()
            query_lower = query_clean.lower()
            if not query_lower.startswith("select"):
                return query
            limit_patterns = [
                r"\blimit\s+\d+\b",
                r"\blimit\s+\d+\s+offset\s+\d+\b",
                r"\boffset\s+\d+\s+limit\s+\d+\b",
            ]
            for pattern in limit_patterns:
                if re.search(pattern, query_lower):
                    return query
            if query_clean.endswith(";"):
                return query_clean[:-1] + " LIMIT 100;"
            return query_clean + " LIMIT 100"
        except Exception:
            return query
