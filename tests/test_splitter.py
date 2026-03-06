"""
Unit tests for components/splitter.py module.

Tests the VerticalSplitter class which provides a draggable
divider between the left (tables) and right (query) panes.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory so we can import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dearpygui before importing splitter
dpg_mock = MagicMock()
sys.modules["dearpygui"] = dpg_mock
sys.modules["dearpygui.dearpygui"] = dpg_mock

# Ensure config module has real values (test_database.py may have replaced it
# with a MagicMock in sys.modules when running the full suite).
config_mock = MagicMock()
config_mock.SPLITTER_WIDTH = 6
config_mock.MIN_LEFT_PANEL_WIDTH = 150
config_mock.MAX_LEFT_PANEL_WIDTH = 600
sys.modules["config"] = config_mock

import components.splitter as splitter_mod  # noqa: E402
from components.splitter import VerticalSplitter  # noqa: E402

# Force real int values on the imported module regardless of config mock state.
# This is needed because test_database.py corrupts sys.modules["config"] at
# module level, and depending on import order the constants may be MagicMock.
splitter_mod.SPLITTER_WIDTH = 6
splitter_mod.MIN_LEFT_PANEL_WIDTH = 150
splitter_mod.MAX_LEFT_PANEL_WIDTH = 600


class TestVerticalSplitterInit(unittest.TestCase):
    """Test VerticalSplitter initialization."""

    def test_init_defaults(self):
        splitter = VerticalSplitter()
        self.assertFalse(splitter._dragging)
        self.assertEqual(splitter._splitter_tag, "vertical_splitter")


class TestVerticalSplitterCreate(unittest.TestCase):
    """Test the create() method registers DPG widgets."""

    def setUp(self):
        self.splitter = VerticalSplitter()

    @patch("components.splitter.handler_registry")
    @patch("components.splitter.add_mouse_release_handler")
    @patch("components.splitter.add_mouse_click_handler")
    @patch("components.splitter.add_child_window")
    def test_create_adds_child_window(self, mock_cw, _click, _release, _reg):
        self.splitter.create(350)

        mock_cw.assert_called_once_with(
            tag="vertical_splitter",
            width=6,
            height=-1,
            border=False,
        )

    @patch("components.splitter.handler_registry")
    @patch("components.splitter.add_mouse_release_handler")
    @patch("components.splitter.add_mouse_click_handler")
    @patch("components.splitter.add_child_window")
    def test_create_registers_mouse_handlers(
        self, _cw, mock_click, mock_release, mock_reg
    ):
        self.splitter.create(350)

        mock_reg.assert_called_once_with(tag="splitter_handler_registry")
        mock_click.assert_called_once()
        mock_release.assert_called_once()

    @patch("components.splitter.handler_registry")
    @patch("components.splitter.add_mouse_release_handler")
    @patch("components.splitter.add_mouse_click_handler")
    @patch("components.splitter.add_child_window")
    def test_create_stores_current_width(self, _cw, _click, _release, _reg):
        self.splitter.create(400)
        self.assertEqual(self.splitter._current_width, 400)


class TestVerticalSplitterDrag(unittest.TestCase):
    """Test drag start / stop logic."""

    def setUp(self):
        self.splitter = VerticalSplitter()
        self.splitter._current_width = 350

    @patch("components.splitter.get_mouse_pos", return_value=(350, 200))
    @patch("components.splitter.get_item_pos", return_value=(350, 0))
    def test_mouse_down_over_splitter_starts_drag(self, _pos, _mouse):
        """Mouse down within the splitter hit region should start dragging."""
        self.splitter._on_mouse_down(None, None)
        self.assertTrue(self.splitter._dragging)

    @patch("components.splitter.get_mouse_pos", return_value=(100, 200))
    @patch("components.splitter.get_item_pos", return_value=(350, 0))
    def test_mouse_down_outside_splitter_no_drag(self, _pos, _mouse):
        """Mouse down far from splitter should not start dragging."""
        self.splitter._on_mouse_down(None, None)
        self.assertFalse(self.splitter._dragging)

    @patch("components.splitter.get_item_pos", return_value=(350, 0))
    def test_mouse_down_within_extended_hit_zone(self, _pos):
        """Mouse down within +-4px of splitter edges should still trigger."""
        # 4px before the splitter start
        with patch("components.splitter.get_mouse_pos", return_value=(346, 200)):
            self.splitter._on_mouse_down(None, None)
            self.assertTrue(self.splitter._dragging)

        self.splitter._dragging = False

        # 4px after the splitter end (350 + 6 + 4 = 360)
        with patch("components.splitter.get_mouse_pos", return_value=(360, 200)):
            self.splitter._on_mouse_down(None, None)
            self.assertTrue(self.splitter._dragging)

    def test_mouse_up_stops_drag(self):
        self.splitter._dragging = True
        self.splitter._on_mouse_up(None, None)
        self.assertFalse(self.splitter._dragging)

    @patch("components.splitter.get_mouse_pos", return_value=(350, 200))
    @patch("components.splitter.get_item_pos", side_effect=Exception("item not found"))
    def test_mouse_down_get_item_pos_exception(self, _pos, _mouse):
        """If get_item_pos throws (item not yet rendered), don't crash."""
        self.splitter._on_mouse_down(None, None)
        self.assertFalse(self.splitter._dragging)


class TestVerticalSplitterUpdate(unittest.TestCase):
    """Test the per-frame update() method."""

    def setUp(self):
        self.splitter = VerticalSplitter()
        self.splitter._current_width = 350

    def test_update_noop_when_not_dragging(self):
        """update() should do nothing if not dragging."""
        self.splitter._dragging = False
        with patch("components.splitter.configure_item") as mock_cfg:
            self.splitter.update()
            mock_cfg.assert_not_called()

    @patch("components.splitter.get_mouse_pos", return_value=(408, 300))
    @patch("components.splitter.configure_item")
    def test_update_resizes_panels_during_drag(self, mock_cfg, _mouse):
        """update() should configure_item on all panels when dragging."""
        self.splitter._dragging = True

        self.splitter.update()

        self.assertEqual(self.splitter._current_width, 400)
        mock_cfg.assert_any_call("left_panel", width=400)
        mock_cfg.assert_any_call("table_search", width=380)
        mock_cfg.assert_any_call("tables_panel", width=400)

    @patch("components.splitter.get_mouse_pos", return_value=(50, 300))
    @patch("components.splitter.configure_item")
    def test_update_clamps_to_min(self, mock_cfg, _mouse):
        """Width should not go below MIN_LEFT_PANEL_WIDTH (150)."""
        self.splitter._dragging = True

        self.splitter.update()

        self.assertEqual(self.splitter._current_width, 150)
        mock_cfg.assert_any_call("left_panel", width=150)

    @patch("components.splitter.get_mouse_pos", return_value=(900, 300))
    @patch("components.splitter.configure_item")
    def test_update_clamps_to_max(self, mock_cfg, _mouse):
        """Width should not exceed MAX_LEFT_PANEL_WIDTH (600)."""
        self.splitter._dragging = True

        self.splitter.update()

        self.assertEqual(self.splitter._current_width, 600)
        mock_cfg.assert_any_call("left_panel", width=600)

    @patch("components.splitter.get_mouse_pos", return_value=(358, 300))
    @patch("components.splitter.configure_item")
    def test_update_skips_when_width_unchanged(self, mock_cfg, _mouse):
        """No configure_item calls if computed width equals current width."""
        self.splitter._dragging = True
        self.splitter._current_width = 350

        self.splitter.update()

        mock_cfg.assert_not_called()

    @patch("components.splitter.get_mouse_pos", return_value=(408, 300))
    @patch("components.splitter.configure_item")
    def test_update_does_not_resize_status_panel(self, mock_cfg, _mouse):
        """Status panel spans full width; splitter should not touch it."""
        self.splitter._dragging = True

        self.splitter.update()

        status_calls = [c for c in mock_cfg.call_args_list if c[0][0] == "status_panel"]
        self.assertEqual(status_calls, [])

    @patch("components.splitter.get_mouse_pos", return_value=(508, 300))
    @patch("components.splitter.configure_item")
    def test_update_configures_all_three_panels(self, mock_cfg, _mouse):
        """Exactly 3 configure_item calls for the 3 resizable elements."""
        self.splitter._dragging = True

        self.splitter.update()

        self.assertEqual(mock_cfg.call_count, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
