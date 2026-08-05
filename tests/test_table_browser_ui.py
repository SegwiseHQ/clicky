"""Performance-focused tests for table-list filtering."""

from unittest.mock import MagicMock, patch

from components.table_browser_ui import (
    CONNECTION_FAILURE_NOTICE,
    CONNECTION_FAILURE_NOTICE_SECONDS,
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


def test_connection_failure_immediately_restores_saved_connections():
    browser, db_manager = _make_browser()
    db_manager.is_connected = False
    db_manager.connection_info = {}
    browser.selected_table = "events"
    browser._pending_table_search = "eve"
    browser._table_cache = ("events",)

    with (
        patch.object(browser, "show_saved_connections") as show_saved_connections,
        patch("components.table_browser_ui.time.monotonic", return_value=100.0),
    ):
        browser.handle_connect_failure()

    assert browser.active_connection_name == ""
    assert "current" not in browser.connections_expanded
    assert browser.selected_table is None
    assert browser._pending_table_search is None
    assert browser._table_cache is None
    assert (
        browser._connection_failure_notice_expires_at
        == 100.0 + CONNECTION_FAILURE_NOTICE_SECONDS
    )
    show_saved_connections.assert_called_once_with()


@patch("components.table_browser_ui.add_separator")
@patch("components.table_browser_ui.add_button")
@patch("components.table_browser_ui.add_text")
@patch("components.table_browser_ui.delete_item")
def test_saved_connections_include_temporary_failure_notice(
    _delete_item, add_text, add_button, add_separator
):
    browser, db_manager = _make_browser()
    db_manager.is_connected = False
    db_manager.connection_info = {}
    browser.credentials_manager.get_credential_names.return_value = ["Production"]
    browser._connection_failure_notice_expires_at = 103.0

    with patch("components.table_browser_ui.time.monotonic", return_value=101.0):
        browser.show_saved_connections()

    add_text.assert_called_once_with(
        CONNECTION_FAILURE_NOTICE,
        parent="tables_list",
        color=(255, 90, 90),
        wrap=320,
    )
    add_separator.assert_called_once_with(parent="tables_list")
    add_button.assert_called_once()


def test_connection_failure_notice_expires_on_the_main_loop():
    browser, db_manager = _make_browser()
    db_manager.is_connected = False
    browser._connection_failure_notice_expires_at = 103.0

    with patch.object(browser, "show_saved_connections") as show_saved_connections:
        assert not browser.process_pending_connection_notice(now=102.9)
        assert browser.process_pending_connection_notice(now=103.0)

    assert browser._connection_failure_notice_expires_at == 0.0
    show_saved_connections.assert_called_once_with()


def test_failed_connection_result_notifies_the_table_browser():
    from components.connection_manager import ConnectionManager

    browser, _db_manager = _make_browser()
    manager = ConnectionManager(MagicMock(), MagicMock())

    with (
        patch.object(browser, "handle_connect_failure") as handle_connect_failure,
        patch("components.connection_manager.StatusManager.show_status"),
        patch("components.connection_manager.UIHelpers.safe_configure_item"),
    ):
        manager.on_connect_failure = handle_connect_failure
        manager._on_connect_done((False, "invalid credentials"))

    handle_connect_failure.assert_called_once_with()
