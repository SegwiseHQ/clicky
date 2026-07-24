"""Performance-focused tests for the data explorer."""

from types import SimpleNamespace
from unittest.mock import MagicMock

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
