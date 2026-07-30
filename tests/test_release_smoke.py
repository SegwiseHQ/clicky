"""Tests for release checks executed from the frozen app."""

import io
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

import release_smoke


@patch("database.DatabaseManager")
def test_release_connection_test_uses_public_playground(mock_manager_class):
    manager = Mock()
    manager.connect.return_value = (
        True,
        "Connected successfully to play.clickhouse.com:443",
    )
    mock_manager_class.return_value = manager

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = release_smoke.run_release_connection_test()

    assert exit_code == 0
    assert stdout.getvalue().strip() == (
        "Connected successfully to play.clickhouse.com:443"
    )
    manager.connect.assert_called_once_with(
        host="play.clickhouse.com",
        port=443,
        username="explorer",
        password="",
        database="default",
    )
    manager.disconnect.assert_called_once_with()


@patch("database.DatabaseManager")
def test_release_connection_test_reports_failure(mock_manager_class):
    manager = Mock()
    manager.connect.return_value = (False, "Connection failed")
    mock_manager_class.return_value = manager

    stderr = io.StringIO()
    with redirect_stderr(stderr):
        exit_code = release_smoke.run_release_connection_test()

    assert exit_code == 1
    assert stderr.getvalue().strip() == "Connection failed"
    manager.disconnect.assert_called_once_with()
