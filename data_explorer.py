"""Data Explorer component for ClickHouse Client."""

import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from dearpygui.dearpygui import *

from config import DEFAULT_LIMIT, MAX_CELL_LENGTH, MAX_EXPLORER_TABS, MAX_ROWS_LIMIT
from database import DatabaseManager

class DataExplorer:
    """Manages the data explorer interface and functionality for a single tab."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        theme_manager=None,
        async_worker=None,
        tag_prefix: str = "explorer",
    ):
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.async_worker = async_worker
        self.current_table: Optional[str] = None
        self.filters: Dict[str, str] = {}
        self.table_theme = None
        self.selected_row_data = None
        self.current_column_names = []
        self.sort_column: Optional[str] = None
        self.sort_ascending: bool = True
        self._refresh_seq = 0
        self._last_status_callback = None

        # Per-instance widget tags derived from prefix
        self.where_tag = f"{tag_prefix}_where"
        self.main_table_tag = f"{tag_prefix}_main_table"
        self.row_details_tag = f"{tag_prefix}_row_details"
        self.data_window_tag = f"{tag_prefix}_data_window"
        self.data_layout_tag = f"{tag_prefix}_data_layout"
        self.close_btn_tag = f"{tag_prefix}_close_button"
        self.toggle_btn_tag = f"{tag_prefix}_toggle_details_button"
        self._btn_table_tag = f"{tag_prefix}_btn_table"

        self._setup_table_theme()

    def _setup_table_theme(self):
        """Setup theme for data tables with increased row height."""
        if self.theme_manager:
            self.table_theme = self.theme_manager.get_theme("table_enhanced")
        else:
            with theme() as self.table_theme:
                with theme_component(mvTable):
                    add_theme_style(mvStyleVar_CellPadding, 8, 8)
                    add_theme_style(mvStyleVar_ItemSpacing, 0, 4)

    def create_ui(self):
        """Build WHERE input, buttons, and data panels under the current DPG parent (a tab_item).

        Callbacks for close_btn_tag and toggle_btn_tag are wired by TabbedExplorerInterface
        after this method returns.
        """
        # WHERE filter row
        with group(horizontal=True):
            add_text("WHERE:")
            add_input_text(
                tag=self.where_tag,
                hint="Enter WHERE condition - Press Enter to apply",
                width=-1,
                on_enter=True,
                callback=self._on_where_change,
            )

        if self.theme_manager:
            bind_item_theme(
                self.where_tag,
                self.theme_manager.get_theme("input_enhanced"),
            )

        # Button controls row
        with table(header_row=False, tag=self._btn_table_tag):
            add_table_column(width_fixed=True, init_width_or_weight=150)
            add_table_column(width_fixed=True, init_width_or_weight=150)

            with table_row():
                with table_cell():
                    add_button(
                        label="Close Tab",
                        tag=self.close_btn_tag,
                        width=140,
                        height=35,
                    )
                with table_cell():
                    add_button(
                        label="Toggle Row View",
                        tag=self.toggle_btn_tag,
                        width=140,
                        height=35,
                    )

        if self.theme_manager:
            bind_item_theme(
                self.close_btn_tag,
                self.theme_manager.get_theme("button_danger"),
            )
            bind_item_theme(
                self.toggle_btn_tag,
                self.theme_manager.get_theme("button_primary"),
            )

        # Data window with horizontal split — fills remaining vertical space
        with child_window(
            label="Data", tag=self.data_window_tag, border=True, height=-1
        ):
            with group(horizontal=True, tag=self.data_layout_tag):
                # Left panel: Main data table
                with child_window(
                    label="Table Data",
                    tag=self.main_table_tag,
                    border=True,
                    width=-410,
                    height=-1,
                ):
                    add_text("Loading data...", color=(128, 128, 128))

                # Right panel: Row details (initially visible)
                with child_window(
                    label="Row Details",
                    tag=self.row_details_tag,
                    border=True,
                    width=400,
                    height=-1,
                    show=True,
                ):
                    add_text(
                        "Select a row to view details",
                        color=(128, 128, 128),
                    )

    def load_table(self, table_name: str, status_callback=None) -> bool:
        """Load a table into this explorer tab (replaces open_explorer)."""
        if not table_name or not table_name.strip():
            if status_callback:
                status_callback(
                    "Error: Cannot open data explorer - invalid table name", True
                )
            return False

        self.current_table = table_name.strip()
        self.filters.clear()
        self.sort_column = None
        self.sort_ascending = True
        self.selected_row_data = None
        self.current_column_names = []

        if status_callback:
            status_callback(f"Opening data explorer for table: {self.current_table}")

        try:
            if does_item_exist(self.main_table_tag):
                delete_item(self.main_table_tag, children_only=True)
                add_text(
                    "Loading data preview...",
                    parent=self.main_table_tag,
                    color=(220, 220, 220),
                )

            if does_item_exist(self.row_details_tag):
                self._clear_row_details()

        except Exception as e:
            print(f"[DataExplorer] Error in explorer setup: {e}")
            if status_callback:
                status_callback(f"Error setting up data explorer: {str(e)}", True)
            return False

        self.refresh_data(status_callback)
        return True

    def _setup_filters(self):
        """Setup WHERE filter control for the current table."""
        try:
            configure_item(self.where_tag, callback=self._on_where_change)
        except Exception:
            pass

    def _on_where_change(self, sender, app_data):
        """Handle WHERE condition change - refresh data when Enter is pressed."""
        self.refresh_data()

    def _on_column_header_click(self, sender, app_data, user_data):
        """Handle column header click for sorting."""
        column_name = user_data

        if self.sort_column == column_name:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column_name
            self.sort_ascending = True

        self.refresh_data()

    def refresh_data(self, status_callback=None):
        """Refresh data in the data explorer with current filters (non-blocking)."""
        if not self.db_manager.is_connected or not self.current_table:
            return

        self._last_status_callback = status_callback

        # Build query
        query = f"SELECT * FROM `{self.current_table}`"

        try:
            where_clause = get_value(self.where_tag)
            if where_clause and where_clause.strip():
                query += f" WHERE {where_clause.strip()}"
        except Exception:
            pass

        if self.sort_column:
            sort_direction = "ASC" if self.sort_ascending else "DESC"
            query += f" ORDER BY `{self.sort_column}` {sort_direction}"

        query += f" LIMIT {DEFAULT_LIMIT}"

        # Bump sequence number — any in-flight fetch with an older seq will be discarded
        self._refresh_seq += 1
        seq = self._refresh_seq

        # Show placeholder immediately on the main thread
        if does_item_exist(self.main_table_tag):
            delete_item(self.main_table_tag, children_only=True)
            add_text(
                "  Loading data...",
                parent=self.main_table_tag,
                color=(100, 150, 255),
            )

        table_name = self.current_table

        if self.async_worker:
            self.async_worker.run_async(
                task=lambda: self._fetch_data_task(query, table_name),
                on_done=lambda result: self._on_data_ready(result, seq, status_callback),
                on_error=lambda e: self._on_data_error(e, seq, status_callback),
            )
        else:
            # Synchronous fallback
            try:
                result = self._fetch_data_task(query, table_name)
                self._on_data_ready(result, seq, status_callback)
            except Exception as e:
                self._on_data_error(e, seq, status_callback)

    # ------------------------------------------------------------------
    # Background task (runs on worker thread — NO DearPyGUI calls here)
    # ------------------------------------------------------------------

    def _fetch_data_task(self, query: str, table_name: str):
        """Run in background thread: execute query and fetch column types."""
        result = self.db_manager.execute_query(query)
        try:
            table_columns = self.db_manager.get_table_columns(table_name)
            column_types = {col_name: col_type for col_name, col_type in table_columns}
        except Exception:
            column_types = {}
        return result, column_types

    # ------------------------------------------------------------------
    # Main-thread callbacks (called via AsyncWorker queue)
    # ------------------------------------------------------------------

    def _on_data_ready(self, payload, seq: int, status_callback=None):
        """Called on the main thread when data is ready."""
        # Discard stale results from superseded refreshes
        if seq != self._refresh_seq:
            return

        result, column_types = payload
        self.current_column_names = result.column_names

        if not does_item_exist(self.main_table_tag):
            if status_callback:
                status_callback(
                    "Error: Main table panel is not available. Please restart.", True
                )
            return

        delete_item(self.main_table_tag, children_only=True)

        if not result.result_rows:
            add_text(
                "No data found", parent=self.main_table_tag, color=(128, 128, 128)
            )
            self._clear_row_details()
            return

        table_tag = f"explorer_data_table_{int(time.time() * 1000)}"

        try:
            add_table(
                tag=table_tag,
                parent=self.main_table_tag,
                borders_innerH=True,
                borders_innerV=True,
                borders_outerH=True,
                borders_outerV=True,
                header_row=False,
                scrollX=True,
                scrollY=True,
                freeze_rows=1,
                height=-1,
                resizable=True,
                policy=mvTable_SizingFixedFit,
            )
        except Exception as table_e:
            print(f"[DataExplorer] Error creating table: {table_e}")
            add_text(
                f"Error creating data table: {str(table_e)}",
                parent=self.main_table_tag,
                color=(255, 0, 0),
            )
            return

        if self.table_theme:
            bind_item_theme(table_tag, self.table_theme)

        column_tags = []
        for col in result.column_names:
            column_tag = f"col_{table_tag}_{col}"
            column_tags.append(column_tag)
            add_table_column(
                tag=column_tag,
                parent=table_tag,
                init_width_or_weight=200,
                width_stretch=False,
                width_fixed=False,
                no_resize=False,
            )
            try:
                configure_item(column_tag, width=200)
            except Exception:
                try:
                    set_item_width(column_tag, 200)
                except Exception:
                    pass

        # Force widths after all columns created
        for column_tag in column_tags:
            try:
                configure_item(column_tag, width=200)
            except Exception:
                try:
                    set_item_width(column_tag, 200)
                except Exception:
                    pass

        # Custom header row with clickable sort buttons
        with table_row(parent=table_tag):
            for col in result.column_names:
                col_type = column_types.get(col, "Unknown")

                sort_indicator = ""
                if self.sort_column == col:
                    sort_indicator = " ^" if self.sort_ascending else " v"

                header_label = f"{col_type}\n{col}{sort_indicator}"

                add_button(
                    label=header_label,
                    tag=f"header_{table_tag}_{col}",
                    callback=self._on_column_header_click,
                    user_data=col,
                    width=-1,
                    height=50,
                )

        # Data rows
        for row_idx, row in enumerate(result.result_rows):
            with table_row(parent=table_tag):
                for col_idx, val in enumerate(row):
                    try:
                        cell_value = self._format_cell_value(val)
                        add_selectable(
                            label=cell_value,
                            tag=f"cell_{table_tag}_{row_idx}_{col_idx}",
                            span_columns=False,
                            height=0,
                            callback=self._handle_cell_click,
                            user_data={
                                "row_idx": row_idx,
                                "col_idx": col_idx,
                                "cell_value": cell_value,
                                "row_data": row,
                            },
                        )
                    except Exception as e:
                        error_text = f"[Error: {str(e)}]"
                        add_selectable(
                            label=error_text,
                            tag=f"cell_error_{table_tag}_{row_idx}_{col_idx}",
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

        if status_callback:
            status_callback(
                f"Explorer: Showing {len(result.result_rows)} rows from {self.current_table}"
            )

    def _on_data_error(self, e: Exception, seq: int, status_callback=None):
        """Called on the main thread when data fetch fails."""
        if seq != self._refresh_seq:
            return

        if does_item_exist(self.main_table_tag):
            delete_item(self.main_table_tag, children_only=True)
            add_text(
                f"Error loading data: {str(e)}",
                parent=self.main_table_tag,
                color=(255, 0, 0),
            )
        self._clear_row_details()
        if status_callback:
            status_callback(f"Explorer error: {str(e)}", True)

    def clear_filters(self):
        """Clear all filters in data explorer."""
        try:
            configure_item(self.where_tag, default_value="")
        except Exception:
            pass

        self.sort_column = None
        self.sort_ascending = True
        self._clear_row_details()
        self.refresh_data()

    def _copy_cell_to_clipboard(self, sender, app_data, user_data):
        """Copy cell content to clipboard when clicked."""
        try:
            cell_text = user_data if user_data else ""
            set_clipboard_text(cell_text)
            if self._last_status_callback:
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
            cell_value = val.decode("utf-8", errors="replace")
        elif isinstance(val, str):
            cell_value = val.encode("utf-8", errors="replace").decode("utf-8")
        else:
            cell_value = str(val)

        if len(cell_value) > MAX_CELL_LENGTH:
            cell_value = cell_value[: MAX_CELL_LENGTH - 3] + "..."

        return cell_value

    def _handle_cell_click(self, sender, app_data, user_data):
        """Handle cell click for both copying to clipboard and showing row details."""
        try:
            row_idx = user_data["row_idx"]
            cell_value = user_data["cell_value"]
            row_data = user_data["row_data"]

            set_clipboard_text(cell_value)

            if self._last_status_callback:
                self._last_status_callback(
                    f"Copied to clipboard: {cell_value[:50]}{'...' if len(cell_value) > 50 else ''}"
                )

            self._update_row_details(row_data, row_idx)

        except Exception as e:
            print(f"Error handling cell click: {e}")

    def _update_row_details(self, row_data, row_idx):
        """Update the row details panel with the selected row's data."""
        try:
            delete_item(self.row_details_tag, children_only=True)

            add_text(
                f"Row {row_idx + 1} Details",
                parent=self.row_details_tag,
                color=(255, 193, 7),
            )
            add_separator(parent=self.row_details_tag)

            details_table_tag = f"row_details_table_{int(time.time() * 1000)}"
            add_table(
                tag=details_table_tag,
                parent=self.row_details_tag,
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

            add_table_column(
                label="Column", parent=details_table_tag, init_width_or_weight=120
            )
            add_table_column(
                label="Value", parent=details_table_tag, init_width_or_weight=250
            )

            for col_idx, (column_name, value) in enumerate(
                zip(self.current_column_names, row_data)
            ):
                with table_row(parent=details_table_tag):
                    add_selectable(
                        label=column_name,
                        tag=f"detail_col_{details_table_tag}_{col_idx}",
                        span_columns=False,
                        height=0,
                        callback=self._copy_detail_to_clipboard,
                        user_data=column_name,
                    )

                    formatted_value = self._format_cell_value(value)
                    add_selectable(
                        label=formatted_value,
                        tag=f"detail_val_{details_table_tag}_{col_idx}",
                        span_columns=False,
                        height=0,
                        callback=self._copy_detail_to_clipboard,
                        user_data=formatted_value,
                    )

            self.selected_row_data = row_data

        except Exception as e:
            delete_item(self.row_details_tag, children_only=True)
            add_text(
                f"Error displaying row details: {str(e)}",
                parent=self.row_details_tag,
                color=(255, 0, 0),
            )

    def _clear_row_details(self):
        """Clear the row details panel."""
        try:
            delete_item(self.row_details_tag, children_only=True)
            add_text(
                "Select a row to view details",
                parent=self.row_details_tag,
                color=(128, 128, 128),
            )
            self.selected_row_data = None
        except Exception:
            pass

    def _copy_detail_to_clipboard(self, sender, app_data, user_data):
        """Copy detail value to clipboard when clicked."""
        try:
            detail_text = user_data if user_data else ""
            set_clipboard_text(detail_text)
            if self._last_status_callback:
                self._last_status_callback(
                    f"Copied to clipboard: {detail_text[:50]}{'...' if len(detail_text) > 50 else ''}"
                )
        except Exception as e:
            print(f"Error copying detail to clipboard: {e}")


# ---------------------------------------------------------------------------
# Per-tab state
# ---------------------------------------------------------------------------


@dataclass
class ExplorerTabState:
    """All state for a single explorer tab."""

    tab_id: int
    tab_tag: str
    table_name: str
    explorer: DataExplorer


# ---------------------------------------------------------------------------
# Tabbed explorer interface
# ---------------------------------------------------------------------------


class TabbedExplorerInterface:
    """Manages multiple independent explorer tabs, each browsing one table."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        theme_manager=None,
        async_worker=None,
    ):
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.async_worker = async_worker
        self.status_callback: Optional[Callable[[str, bool], None]] = None

        self._tabs: dict[int, ExplorerTabState] = {}
        self._tab_counter = 0

    def set_status_callback(self, callback: Callable[[str, bool], None]):
        self.status_callback = callback

    # ------------------------------------------------------------------
    # Tab lifecycle
    # ------------------------------------------------------------------

    def open_tab(self, table_name: str, status_callback=None):
        """Open a tab for table_name, or focus + refresh if already open."""
        if not table_name or not table_name.strip():
            return

        table_name = table_name.strip()

        # If table is already open, focus it and refresh
        for state in self._tabs.values():
            if state.table_name == table_name and does_item_exist(state.tab_tag):
                set_value("explorer_tab_bar", state.tab_tag)
                state.explorer.refresh_data(status_callback or self.status_callback)
                return

        # Enforce max tab limit
        if len(self._tabs) >= MAX_EXPLORER_TABS:
            cb = status_callback or self.status_callback
            if cb:
                cb(f"Maximum of {MAX_EXPLORER_TABS} explorer tabs allowed", True)
            return

        tab_id = self._tab_counter
        self._tab_counter += 1
        tab_tag = f"explorer_tab_{tab_id}"
        cb = status_callback or self.status_callback

        try:
            # Show explorer section, hide query section
            configure_item("explorer_section", show=True)
            configure_item("query_section", show=False)

            # Create per-tab DataExplorer with unique tag prefix
            explorer = DataExplorer(
                db_manager=self.db_manager,
                theme_manager=self.theme_manager,
                async_worker=self.async_worker,
                tag_prefix=f"explorer_{tab_id}",
            )

            # Build the tab UI
            with tab(
                tag=tab_tag,
                parent="explorer_tab_bar",
                closable=True,
                label=table_name,
            ):
                explorer.create_ui()

            # Wire callbacks now that widgets exist
            configure_item(
                explorer.close_btn_tag,
                callback=lambda s, d, tid=tab_id: self._close_tab_by_id(tid),
            )
            configure_item(
                explorer.toggle_btn_tag,
                callback=lambda s, d, exp=explorer: self._toggle_row_details(exp),
            )

            # Auto-focus the new tab
            set_value("explorer_tab_bar", tab_tag)

            # Register state
            state = ExplorerTabState(
                tab_id=tab_id,
                tab_tag=tab_tag,
                table_name=table_name,
                explorer=explorer,
            )
            self._tabs[tab_id] = state

            # Load table data
            explorer.load_table(table_name, cb)

        except Exception as e:
            print(f"[TabbedExplorerInterface] Error opening tab: {e}")
            if cb:
                cb(f"Error opening explorer for '{table_name}': {e}", True)
            # Clean up partial state
            self._tabs.pop(tab_id, None)
            if does_item_exist(tab_tag):
                delete_item(tab_tag)
            if not self._tabs:
                self._show_query_view()

    def poll_closed_tabs(self):
        """Called each frame to detect tabs closed via the DPG X button."""
        closed_ids = [
            tab_id
            for tab_id, state in list(self._tabs.items())
            if not does_item_exist(state.tab_tag)
            or not is_item_shown(state.tab_tag)
        ]
        for tab_id in closed_ids:
            self._close_tab_state(tab_id)

        if closed_ids and not self._tabs:
            self._show_query_view()

    def _close_tab_by_id(self, tab_id: int):
        """Close a tab programmatically (e.g. from the Close Tab button)."""
        self._close_tab_state(tab_id)
        if not self._tabs:
            self._show_query_view()

    def _close_tab_state(self, tab_id: int):
        """Remove tab state and delete its DPG item if it still exists."""
        state = self._tabs.pop(tab_id, None)
        if state is None:
            return
        if does_item_exist(state.tab_tag):
            delete_item(state.tab_tag)

    def _show_query_view(self):
        """Hide explorer section and restore the query section."""
        try:
            configure_item("explorer_section", show=False)
            configure_item("query_section", show=True)
        except Exception as e:
            print(f"[TabbedExplorerInterface] Error restoring query view: {e}")

    def _toggle_row_details(self, explorer: DataExplorer):
        """Toggle the row details panel for the given explorer tab."""
        try:
            is_visible = get_item_configuration(explorer.row_details_tag)["show"]
            configure_item(explorer.row_details_tag, show=not is_visible)
            # Adjust main table width based on panel visibility
            if is_visible:
                configure_item(explorer.main_table_tag, width=-1)
            else:
                configure_item(explorer.main_table_tag, width=-410)
        except Exception as e:
            print(f"[TabbedExplorerInterface] Error toggling row details: {e}")
