"""Performance-focused tests for table-list filtering."""

from unittest.mock import MagicMock, patch

from components.table_browser_ui import (
    TABLE_CACHE_TTL_SECONDS,
    TABLE_SEARCH_DEBOUNCE_SECONDS,
    TableBrowserUI,
)


def _make_browser():
    db_manager = MagicMock()
    db_manager.is_connected = True
    db_manager.connection_info = {
        "host": "clickhouse.example",
        "port": 8123,
        "username": "default",
        "database": "analytics",
    }
    db_manager.get_tables.return_value = ["events", "event_daily", "users"]
    browser = TableBrowserUI(db_manager, MagicMock())
    browser.active_connection_name = "Analytics"
    browser.connections_expanded.add("current")
    return browser, db_manager


@patch("components.table_browser_ui.add_text")
@patch("components.table_browser_ui.delete_item")
@patch("components.table_browser_ui.get_y_scroll", return_value=0)
def test_programmatic_filters_use_cached_tables_without_new_queries(
    _get_scroll, _delete_item, _add_text
):
    browser, db_manager = _make_browser()

    with patch.object(browser, "_finish_filter_tables") as finish:
        browser.filter_tables_callback(None, "e")
        browser.filter_tables_callback(None, "ev")
        browser.filter_tables_callback(None, "eve")

    assert db_manager.get_tables.call_count == 1
    assert finish.call_count == 3
    assert finish.call_args.args[0] == ("events", "event_daily", "users")
    assert finish.call_args.args[2] == "eve"


@patch("components.table_browser_ui.add_text")
@patch("components.table_browser_ui.delete_item")
@patch("components.table_browser_ui.get_y_scroll", return_value=0)
def test_search_debounces_rapid_keystrokes(_get_scroll, _delete_item, _add_text):
    browser, db_manager = _make_browser()

    with (
        patch.object(browser, "_finish_filter_tables") as finish,
        patch("components.table_browser_ui.time.monotonic", return_value=100.0),
    ):
        browser.filter_tables_callback("table_search", "e")
        browser.filter_tables_callback("table_search", "ev")
        browser.filter_tables_callback("table_search", "eve")

        assert not browser.process_pending_filter(
            now=100.0 + TABLE_SEARCH_DEBOUNCE_SECONDS - 0.001
        )
        assert browser.process_pending_filter(now=100.0 + TABLE_SEARCH_DEBOUNCE_SECONDS)

    db_manager.get_tables.assert_called_once_with()
    finish.assert_called_once()
    assert finish.call_args.args[2] == "eve"


@patch("components.table_browser_ui.add_text")
@patch("components.table_browser_ui.delete_item")
@patch("components.table_browser_ui.get_y_scroll", return_value=0)
def test_programmatic_refresh_cancels_pending_search(
    _get_scroll, _delete_item, _add_text
):
    browser, db_manager = _make_browser()

    with (
        patch.object(browser, "_finish_filter_tables") as finish,
        patch("components.table_browser_ui.time.monotonic", return_value=100.0),
    ):
        browser.filter_tables_callback("table_search", "stale")
        browser.filter_tables_callback(None, "current")

        assert not browser.process_pending_filter(now=200.0)

    db_manager.get_tables.assert_called_once_with()
    finish.assert_called_once()
    assert finish.call_args.args[2] == "current"


@patch("components.table_browser_ui.add_text")
@patch("components.table_browser_ui.delete_item")
@patch("components.table_browser_ui.get_y_scroll", return_value=0)
def test_invalidating_cache_refreshes_tables(_get_scroll, _delete_item, _add_text):
    browser, db_manager = _make_browser()

    with patch.object(browser, "_finish_filter_tables"):
        browser.filter_tables_callback(None, "")
        browser.invalidate_table_cache()
        browser.filter_tables_callback(None, "")

    assert db_manager.get_tables.call_count == 2


@patch("components.table_browser_ui.add_text")
@patch("components.table_browser_ui.delete_item")
@patch("components.table_browser_ui.get_y_scroll", return_value=0)
def test_expired_cache_refreshes_tables(_get_scroll, _delete_item, _add_text):
    browser, db_manager = _make_browser()

    with (
        patch.object(browser, "_finish_filter_tables"),
        patch("components.table_browser_ui.time.monotonic") as monotonic,
    ):
        monotonic.side_effect = [
            10.0,
            10.0 + TABLE_CACHE_TTL_SECONDS + 1,
            16.0,
        ]
        browser.filter_tables_callback(None, "")
        browser.filter_tables_callback(None, "events")

    assert db_manager.get_tables.call_count == 2
