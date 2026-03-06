"""
Unit tests for components/status_manager.py module.

Tests the StatusManager class which displays status messages
spanning the full window width.
"""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock

# Add parent directory so we can import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Build a mock dearpygui module that supports wildcard import.
# A real types.ModuleType with __all__ ensures `from X import *` works.
_dpg_funcs = [
    "delete_item",
    "add_text",
    "add_input_text",
    "bind_item_theme",
]
dpg_inner = types.ModuleType("dearpygui.dearpygui")
for _fn in _dpg_funcs:
    setattr(dpg_inner, _fn, MagicMock(name=_fn))
dpg_inner.__all__ = _dpg_funcs

dpg_outer = types.ModuleType("dearpygui")
dpg_outer.dearpygui = dpg_inner

sys.modules["dearpygui"] = dpg_outer
sys.modules["dearpygui.dearpygui"] = dpg_inner

# Mock config with real values
config_mock = MagicMock()
config_mock.COLOR_ERROR = (255, 80, 80)
config_mock.COLOR_SUCCESS = (80, 255, 80)
sys.modules["config"] = config_mock

# Force reimport so wildcard import pulls named functions into module globals
if "components.status_manager" in sys.modules:
    del sys.modules["components.status_manager"]

import components.status_manager as sm_mod  # noqa: E402
from components.status_manager import StatusManager  # noqa: E402


def _reset_dpg_mocks():
    for fn in _dpg_funcs:
        getattr(dpg_inner, fn).reset_mock()


class TestStatusManagerTheme(unittest.TestCase):
    """Test theme manager integration."""

    def setUp(self):
        StatusManager.theme_manager = None

    def test_set_theme_manager(self):
        mock_tm = MagicMock()
        StatusManager.set_theme_manager(mock_tm)
        self.assertIs(StatusManager.theme_manager, mock_tm)

    def tearDown(self):
        StatusManager.theme_manager = None


class TestShowStatusSuccess(unittest.TestCase):
    """Test success message display."""

    def setUp(self):
        StatusManager.theme_manager = None
        _reset_dpg_mocks()

    def test_success_message_uses_wrap_minus_one(self):
        """Success text should use wrap=-1 to fill available width."""
        StatusManager.show_status("Connected")

        sm_mod.add_text.assert_called_once()
        _, kwargs = sm_mod.add_text.call_args
        self.assertEqual(kwargs["wrap"], -1)

    def test_success_message_uses_success_color(self):
        StatusManager.show_status("Connected")

        _, kwargs = sm_mod.add_text.call_args
        self.assertEqual(kwargs["color"], (80, 255, 80))

    def test_success_clears_existing_status(self):
        StatusManager.show_status("OK")
        sm_mod.delete_item.assert_called_with("status_text", children_only=True)

    def test_success_applies_theme_when_available(self):
        mock_tm = MagicMock()
        StatusManager.theme_manager = mock_tm

        StatusManager.show_status("OK")

        sm_mod.bind_item_theme.assert_called_once()
        mock_tm.get_theme.assert_called_with("success_text")

    def test_success_no_theme_bind_without_manager(self):
        StatusManager.theme_manager = None
        StatusManager.show_status("OK")
        sm_mod.bind_item_theme.assert_not_called()

    def test_success_does_not_add_input(self):
        """Success messages should not include a copyable input."""
        StatusManager.show_status("OK", error=False)
        sm_mod.add_input_text.assert_not_called()

    def tearDown(self):
        StatusManager.theme_manager = None


class TestShowStatusError(unittest.TestCase):
    """Test error message display."""

    def setUp(self):
        StatusManager.theme_manager = None
        _reset_dpg_mocks()

    def test_error_message_uses_wrap_minus_one(self):
        """Error text should use wrap=-1 to fill available width."""
        StatusManager.show_status("Failed", error=True)

        sm_mod.add_text.assert_called_once()
        _, kwargs = sm_mod.add_text.call_args
        self.assertEqual(kwargs["wrap"], -1)

    def test_error_message_uses_error_color(self):
        StatusManager.show_status("Failed", error=True)

        _, kwargs = sm_mod.add_text.call_args
        self.assertEqual(kwargs["color"], (255, 80, 80))

    def test_error_adds_copyable_input(self):
        """Errors should include a readonly copyable input field."""
        StatusManager.show_status("Connection refused", error=True)

        sm_mod.add_input_text.assert_called_once()
        _, kwargs = sm_mod.add_input_text.call_args
        self.assertEqual(kwargs["default_value"], "Connection refused")
        self.assertTrue(kwargs["readonly"])
        self.assertEqual(kwargs["width"], -1)

    def tearDown(self):
        StatusManager.theme_manager = None


if __name__ == "__main__":
    unittest.main(verbosity=2)
