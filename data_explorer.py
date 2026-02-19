"""Data Explorer component for ClickHouse Client."""

import time
from typing import Dict, Optional

from dearpygui.dearpygui import *

from config import DEFAULT_LIMIT, MAX_CELL_LENGTH, MAX_ROWS_LIMIT
from database import DatabaseManager


class DataExplorer:
    """Manages the data explorer interface and functionality."""

    def __init__(self, db_manager: DatabaseManager, theme_manager=None, async_worker=None):
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.async_worker = async_worker
        self.current_table: Optional[str] = None
        self.filters: Dict[str, str] = {}
        self.table_theme = None
        self.selected_row_data = None  # Store selected row data for details panel
        self.current_column_names = []  # Store current column names
        self.sort_column: Optional[str] = None  # Current sort column
        self.sort_ascending: bool = True  # Sort direction
        self._refresh_seq = 0  # Sequence number to discard stale async results
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

    def open_explorer(self, table_name: str, status_callback=None) -> bool:
        """Open data explorer for a specific table."""
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

        # Hide query section
        configure_item("query_section", show=False)

        # Show explorer section
        configure_item("explorer_section", show=True)

        # Setup filter controls
        self._setup_filters()

        try:
            configure_item("explorer_section", show=True)
            configure_item("explorer_data_window", show=True)

            if does_item_exist("explorer_main_table"):
                delete_item("explorer_main_table", children_only=True)
                add_text(
                    "Loading data preview...",
                    parent="explorer_main_table",
                    color=(220, 220, 220),
                )

            if does_item_exist("explorer_row_details"):
                self._clear_row_details()

        except Exception as e:
            print(f"[DataExplorer] Error in explorer setup: {e}")
            if status_callback:
                status_callback(f"Error setting up data explorer: {str(e)}", True)
            return False

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

        try:
            configure_item("explorer_where", default_value="")
        except:
            pass

        configure_item("explorer_section", show=False)
        configure_item("query_section", show=True)

    def _setup_filters(self):
        """Setup WHERE filter control for the current table."""
        try:
            configure_item("explorer_where", callback=self._on_where_change)
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
            where_clause = get_value("explorer_where")
            if where_clause and where_clause.strip():
                query += f" WHERE {where_clause.strip()}"
        except:
            pass

        if self.sort_column:
            sort_direction = "ASC" if self.sort_ascending else "DESC"
            query += f" ORDER BY `{self.sort_column}` {sort_direction}"

        query += f" LIMIT {DEFAULT_LIMIT}"

        # Bump sequence number — any in-flight fetch with an older seq will be discarded
        self._refresh_seq += 1
        seq = self._refresh_seq

        # Show placeholder immediately on the main thread
        if does_item_exist("explorer_main_table"):
            delete_item("explorer_main_table", children_only=True)
            add_text(
                "  Loading data...",
                parent="explorer_main_table",
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

        if not does_item_exist("explorer_main_table"):
            if status_callback:
                status_callback(
                    "Error: Main table panel is not available. Please restart.", True
                )
            return

        delete_item("explorer_main_table", children_only=True)

        if not result.result_rows:
            add_text(
                "No data found", parent="explorer_main_table", color=(128, 128, 128)
            )
            self._clear_row_details()
            return

        table_tag = f"explorer_data_table_{int(time.time() * 1000)}"

        try:
            add_table(
                tag=table_tag,
                parent="explorer_main_table",
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
                parent="explorer_main_table",
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
                            tag=f"cell_{row_idx}_{col_idx}",
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

        if status_callback:
            status_callback(
                f"Explorer: Showing {len(result.result_rows)} rows from {self.current_table}"
            )

    def _on_data_error(self, e: Exception, seq: int, status_callback=None):
        """Called on the main thread when data fetch fails."""
        if seq != self._refresh_seq:
            return

        if does_item_exist("explorer_main_table"):
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
        try:
            configure_item("explorer_where", default_value="")
        except:
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
            user_data["col_idx"]
            cell_value = user_data["cell_value"]
            row_data = user_data["row_data"]

            set_clipboard_text(cell_value)

            if hasattr(self, "_last_status_callback") and self._last_status_callback:
                self._last_status_callback(
                    f"Copied to clipboard: {cell_value[:50]}{'...' if len(cell_value) > 50 else ''}"
                )

            self._update_row_details(row_data, row_idx)

        except Exception as e:
            print(f"Error handling cell click: {e}")

    def _update_row_details(self, row_data, row_idx):
        """Update the row details panel with the selected row's data."""
        try:
            delete_item("explorer_row_details", children_only=True)

            add_text(
                f"Row {row_idx + 1} Details",
                parent="explorer_row_details",
                color=(255, 193, 7),
            )
            add_separator(parent="explorer_row_details")

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
                        tag=f"detail_col_{col_idx}",
                        span_columns=False,
                        height=0,
                        callback=self._copy_detail_to_clipboard,
                        user_data=column_name,
                    )

                    formatted_value = self._format_cell_value(value)
                    add_selectable(
                        label=formatted_value,
                        tag=f"detail_val_{col_idx}",
                        span_columns=False,
                        height=0,
                        callback=self._copy_detail_to_clipboard,
                        user_data=formatted_value,
                    )

            self.selected_row_data = row_data

        except Exception as e:
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
            pass

    def _copy_detail_to_clipboard(self, sender, app_data, user_data):
        """Copy detail value to clipboard when clicked."""
        try:
            detail_text = user_data if user_data else ""
            set_clipboard_text(detail_text)
            if hasattr(self, "_last_status_callback") and self._last_status_callback:
                self._last_status_callback(
                    f"Copied to clipboard: {detail_text[:50]}{'...' if len(detail_text) > 50 else ''}"
                )
        except Exception as e:
            print(f"Error copying detail to clipboard: {e}")
