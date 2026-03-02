"""
Unit tests for components/query_interface.py module.

Tests the TabbedQueryInterface class, focusing on tab rename
functionality and tab lifecycle management.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory so we can import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dearpygui before importing query_interface
dpg_mock = MagicMock()
sys.modules["dearpygui"] = dpg_mock
sys.modules["dearpygui.dearpygui"] = dpg_mock

# Mock config with real values
config_mock = MagicMock()
config_mock.DEFAULT_TAB_LABEL = "Query"
config_mock.MAX_QUERY_TABS = 10
config_mock.QUERY_INPUT_HEIGHT = 150
sys.modules["config"] = config_mock

# Mock other dependencies
sys.modules["database"] = MagicMock()
sys.modules["icon_manager"] = MagicMock()

import components.query_interface as qi_mod  # noqa: E402
from components.query_interface import QueryTabState, TabbedQueryInterface  # noqa: E402

# Force real values on the imported module
qi_mod.DEFAULT_TAB_LABEL = "Query"
qi_mod.MAX_QUERY_TABS = 10
qi_mod.QUERY_INPUT_HEIGHT = 150

# Alias for patch with create=True (star-import names don't exist on the module)
_P = "components.query_interface"


def _patch(name, **kwargs):
    """Patch a star-imported DPG function on the query_interface module."""
    return patch(f"{_P}.{name}", create=True, **kwargs)


def _make_interface(theme_manager="DEFAULT"):
    """Create a TabbedQueryInterface with mocked dependencies.

    Always passes a MagicMock theme_manager to __init__ so that
    _setup_table_theme never calls the real DPG theme() context manager.
    After construction, overrides theme_manager to the requested value.
    """
    if theme_manager == "DEFAULT":
        theme_manager = MagicMock()
    pool = MagicMock()
    pool.is_configured = True
    db = MagicMock()
    iface = TabbedQueryInterface(pool, db, theme_manager=MagicMock())
    iface.theme_manager = theme_manager
    return iface


def _make_state(tab_id=0, label="Query 1"):
    """Create a QueryTabState for testing."""
    return QueryTabState(
        tab_id=tab_id,
        label=label,
        tab_tag=f"query_tab_{tab_id}",
        input_tag=f"query_input_{tab_id}",
        run_btn_tag=f"run_query_btn_{tab_id}",
        save_btn_tag=f"save_json_btn_{tab_id}",
        results_window_tag=f"results_window_{tab_id}",
    )


class TestMakeRenameCallback(unittest.TestCase):
    """Test _make_rename_callback returns a callable that invokes _show_rename_modal."""

    def test_callback_calls_show_rename_modal(self):
        iface = _make_interface()
        with patch.object(iface, "_show_rename_modal") as mock_show:
            cb = iface._make_rename_callback(42)
            cb("sender", "data")
            mock_show.assert_called_once_with(42)


class TestShowRenameModal(unittest.TestCase):
    """Test _show_rename_modal creates the modal UI correctly."""

    def test_noop_when_tab_missing(self):
        iface = _make_interface()
        # Should not raise when tab_id not in _tabs
        iface._show_rename_modal(999)

    @_patch("focus_item")
    @_patch("bind_item_theme")
    @_patch("add_button")
    @_patch("group")
    @_patch("add_input_text")
    @_patch("window")
    @_patch("delete_item")
    @_patch("does_item_exist", return_value=False)
    @_patch("get_viewport_height", return_value=800)
    @_patch("get_viewport_width", return_value=1200)
    def test_creates_modal_window(
        self,
        _vw,
        _vh,
        _exists,
        _del,
        mock_window,
        mock_input,
        _group,
        _btn,
        _bind,
        mock_focus,
    ):
        iface = _make_interface()
        state = _make_state(tab_id=3, label="My Tab")
        iface._tabs[3] = state

        iface._show_rename_modal(3)

        # Window created with correct tag and centered position
        mock_window.assert_called_once()
        kw = mock_window.call_args[1]
        self.assertEqual(kw["tag"], "rename_modal_3")
        self.assertTrue(kw["modal"])
        self.assertEqual(kw["pos"], [450, 350])

        # Input pre-filled with current label
        mock_input.assert_called_once()
        input_kw = mock_input.call_args[1]
        self.assertEqual(input_kw["tag"], "rename_input_3")
        self.assertEqual(input_kw["default_value"], "My Tab")
        self.assertTrue(input_kw["on_enter"])

        # Focus set on input
        mock_focus.assert_called_once_with("rename_input_3")

    @_patch("focus_item")
    @_patch("bind_item_theme")
    @_patch("add_button")
    @_patch("group")
    @_patch("add_input_text")
    @_patch("window")
    @_patch("delete_item")
    @_patch("does_item_exist", return_value=True)
    @_patch("get_viewport_height", return_value=800)
    @_patch("get_viewport_width", return_value=1200)
    def test_deletes_existing_modal_before_creating(
        self,
        _vw,
        _vh,
        _exists,
        mock_del,
        _win,
        _input,
        _group,
        _btn,
        _bind,
        _focus,
    ):
        iface = _make_interface()
        state = _make_state(tab_id=1)
        iface._tabs[1] = state

        iface._show_rename_modal(1)

        mock_del.assert_called_once_with("rename_modal_1")

    @_patch("focus_item")
    @_patch("bind_item_theme")
    @_patch("add_button")
    @_patch("group")
    @_patch("add_input_text")
    @_patch("window")
    @_patch("delete_item")
    @_patch("does_item_exist", return_value=False)
    @_patch("get_viewport_height", return_value=800)
    @_patch("get_viewport_width", return_value=1200)
    def test_applies_themes_when_theme_manager_present(
        self,
        _vw,
        _vh,
        _exists,
        _del,
        _win,
        _input,
        _group,
        _btn,
        mock_bind,
        _focus,
    ):
        tm = MagicMock()
        tm.get_theme.side_effect = lambda name: f"theme_{name}"
        iface = _make_interface(theme_manager=tm)
        state = _make_state(tab_id=0)
        iface._tabs[0] = state

        iface._show_rename_modal(0)

        mock_bind.assert_any_call("rename_input_0", "theme_connection_input")
        mock_bind.assert_any_call("rename_ok_0", "theme_button_primary")
        mock_bind.assert_any_call("rename_cancel_0", "theme_button_secondary")

    @_patch("focus_item")
    @_patch("bind_item_theme")
    @_patch("add_button")
    @_patch("group")
    @_patch("add_input_text")
    @_patch("window")
    @_patch("delete_item")
    @_patch("does_item_exist", return_value=False)
    @_patch("get_viewport_height", return_value=800)
    @_patch("get_viewport_width", return_value=1200)
    def test_no_bind_item_theme_without_theme_manager(
        self,
        _vw,
        _vh,
        _exists,
        _del,
        _win,
        _input,
        _group,
        _btn,
        mock_bind,
        _focus,
    ):
        iface = _make_interface(theme_manager=None)
        state = _make_state(tab_id=0)
        iface._tabs[0] = state

        iface._show_rename_modal(0)

        mock_bind.assert_not_called()


class TestApplyRename(unittest.TestCase):
    """Test _apply_rename updates state and tab label."""

    @_patch("delete_item")
    @_patch("does_item_exist", return_value=True)
    @_patch("configure_item")
    @_patch("get_value", return_value="New Name")
    def test_renames_tab(self, _get, mock_cfg, _exists, _del):
        iface = _make_interface()
        state = _make_state(tab_id=5, label="Query 6")
        iface._tabs[5] = state

        iface._apply_rename(5)

        self.assertEqual(state.label, "New Name")
        mock_cfg.assert_called_once_with("query_tab_5", label="New Name")

    @_patch("delete_item")
    @_patch("does_item_exist", return_value=True)
    @_patch("configure_item")
    @_patch("get_value", return_value="  Trimmed  ")
    def test_trims_whitespace(self, _get, mock_cfg, _exists, _del):
        iface = _make_interface()
        state = _make_state(tab_id=0, label="Old")
        iface._tabs[0] = state

        iface._apply_rename(0)

        self.assertEqual(state.label, "Trimmed")
        mock_cfg.assert_called_once_with("query_tab_0", label="Trimmed")

    @_patch("delete_item")
    @_patch("does_item_exist", return_value=True)
    @_patch("configure_item")
    @_patch("get_value", return_value="   ")
    def test_empty_input_keeps_old_label(self, _get, mock_cfg, _exists, _del):
        iface = _make_interface()
        state = _make_state(tab_id=0, label="Keep Me")
        iface._tabs[0] = state

        iface._apply_rename(0)

        self.assertEqual(state.label, "Keep Me")
        mock_cfg.assert_not_called()

    @_patch("delete_item")
    @_patch("does_item_exist", return_value=True)
    @_patch("configure_item")
    @_patch("get_value", return_value="X")
    def test_deletes_modal_after_rename(self, _get, _cfg, _exists, mock_del):
        iface = _make_interface()
        state = _make_state(tab_id=2)
        iface._tabs[2] = state

        iface._apply_rename(2)

        mock_del.assert_called_once_with("rename_modal_2")

    def test_noop_when_tab_missing(self):
        iface = _make_interface()
        iface._apply_rename(999)


class TestCancelRename(unittest.TestCase):
    """Test _cancel_rename deletes the modal."""

    @_patch("delete_item")
    @_patch("does_item_exist", return_value=True)
    def test_deletes_modal(self, _exists, mock_del):
        iface = _make_interface()
        iface._cancel_rename(7)
        mock_del.assert_called_once_with("rename_modal_7")

    @_patch("delete_item")
    @_patch("does_item_exist", return_value=False)
    def test_noop_when_modal_missing(self, _exists, mock_del):
        iface = _make_interface()
        iface._cancel_rename(7)
        mock_del.assert_not_called()


class TestCloseTabStateCleanup(unittest.TestCase):
    """Test _close_tab_state cleans up popup and rename modal."""

    @_patch("delete_item")
    @_patch("does_item_exist")
    def test_cleans_up_popup_and_modal(self, mock_exists, mock_del):
        iface = _make_interface()
        state = _make_state(tab_id=4)
        iface._tabs[4] = state

        mock_exists.return_value = True

        iface._close_tab_state(4)

        mock_del.assert_any_call("tab_ctx_4")
        mock_del.assert_any_call("rename_modal_4")
        mock_del.assert_any_call("query_tab_4")
        self.assertNotIn(4, iface._tabs)

    @_patch("delete_item")
    @_patch("does_item_exist")
    def test_skips_nonexistent_items(self, mock_exists, mock_del):
        iface = _make_interface()
        state = _make_state(tab_id=1)
        iface._tabs[1] = state

        def exists_side_effect(tag):
            return tag == "query_tab_1"

        mock_exists.side_effect = exists_side_effect

        iface._close_tab_state(1)

        mock_del.assert_called_once_with("query_tab_1")

    def test_noop_for_unknown_tab(self):
        iface = _make_interface()
        iface._close_tab_state(999)


class TestMakeApplyAndCancelRenameCallbacks(unittest.TestCase):
    """Test the callback factory methods."""

    def test_make_apply_rename_returns_callable(self):
        iface = _make_interface()
        cb = iface._make_apply_rename(1)
        self.assertTrue(callable(cb))

    def test_make_cancel_rename_returns_callable(self):
        iface = _make_interface()
        cb = iface._make_cancel_rename(1)
        self.assertTrue(callable(cb))

    def test_apply_callback_delegates(self):
        iface = _make_interface()
        with patch.object(iface, "_apply_rename") as mock:
            cb = iface._make_apply_rename(3)
            cb("s", "d")
            mock.assert_called_once_with(3)

    def test_cancel_callback_delegates(self):
        iface = _make_interface()
        with patch.object(iface, "_cancel_rename") as mock:
            cb = iface._make_cancel_rename(3)
            cb("s", "d")
            mock.assert_called_once_with(3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
