"""Performance-focused tests for the data explorer."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from data_explorer import DataExplorer


def test_fetch_data_reuses_query_result_metadata():
    db_manager = MagicMock()
    result = SimpleNamespace(
        column_names=("id", "payload"),
        column_types=(
            SimpleNamespace(name="UInt64"),
            SimpleNamespace(name="Nullable(String)"),
        ),
    )
    db_manager.execute_query.return_value = result
    explorer = DataExplorer.__new__(DataExplorer)
    explorer.db_manager = db_manager

    payload = explorer._fetch_data_task("SELECT * FROM events", "events")

    assert payload == (
        result,
        {"id": "UInt64", "payload": "Nullable(String)"},
    )
    db_manager.execute_query.assert_called_once_with("SELECT * FROM events")
    db_manager.get_table_columns.assert_not_called()


@patch("data_explorer.add_button", create=True)
@patch("data_explorer.table_row", create=True)
@patch("data_explorer.set_item_width", create=True)
@patch("data_explorer.configure_item", create=True)
@patch("data_explorer.add_table_column", create=True)
@patch("data_explorer.add_table", create=True)
@patch("data_explorer.delete_item", create=True)
@patch("data_explorer.does_item_exist", return_value=True, create=True)
def test_explorer_table_enables_clipping_and_queues_rows(
    _exists,
    _delete,
    add_table,
    _add_column,
    _configure,
    _set_width,
    _table_row,
    _add_button,
):
    explorer = DataExplorer.__new__(DataExplorer)
    explorer._refresh_seq = 1
    explorer._render_generation = 2
    explorer._active_table_tag = None
    explorer.main_table_tag = "main_table"
    explorer.table_theme = None
    explorer.sort_column = None
    explorer.sort_ascending = True
    explorer.current_table = "events"
    explorer.current_column_names = []
    explorer.async_worker = MagicMock()
    result = SimpleNamespace(
        column_names=("id", "name"),
        result_rows=[(1, "one"), (2, "two")],
    )

    with (
        patch("data_explorer.mvTable_SizingFixedFit", 0, create=True),
        patch.object(explorer, "_queue_data_rows_chunk") as queue_chunk,
    ):
        explorer._on_data_ready((result, {"id": "UInt64", "name": "String"}), 1)

    assert add_table.call_args.kwargs["clipper"] is True
    assert queue_chunk.call_args.args[1] == result.result_rows


@patch("data_explorer.add_selectable", create=True)
@patch("data_explorer.table_row", create=True)
@patch("data_explorer.does_item_exist", return_value=True, create=True)
def test_explorer_rows_are_built_in_bounded_chunks(_exists, _table_row, add_selectable):
    explorer = DataExplorer.__new__(DataExplorer)
    explorer._render_generation = 4
    explorer._active_table_tag = "table"
    explorer.async_worker = MagicMock()
    explorer.current_table = "events"
    explorer._last_status_callback = None
    rows = [(i,) for i in range(5)]

    with (
        patch("data_explorer.RESULT_ROWS_PER_FRAME", 2),
        patch.object(explorer, "_queue_data_rows_chunk") as queue_chunk,
    ):
        explorer._render_data_rows_chunk("table", rows, 0, 4)

    assert add_selectable.call_count == 2
    assert queue_chunk.call_args.args[2] == 2
