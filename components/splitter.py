"""Vertical splitter for resizable left/right panes."""

from dearpygui.dearpygui import (
    add_child_window,
    add_mouse_click_handler,
    add_mouse_release_handler,
    configure_item,
    get_item_pos,
    get_mouse_pos,
    handler_registry,
)

from config import MAX_LEFT_PANEL_WIDTH, MIN_LEFT_PANEL_WIDTH, SPLITTER_WIDTH


class VerticalSplitter:
    """Draggable vertical splitter between left and right panes."""

    def __init__(self):
        self._dragging = False
        self._splitter_tag = "vertical_splitter"

    def create(self, current_width):
        """Create the splitter widget. Call inside the horizontal group."""
        add_child_window(
            tag=self._splitter_tag,
            width=SPLITTER_WIDTH,
            height=-1,
            border=False,
        )

        # Mouse handlers for drag
        with handler_registry(tag="splitter_handler_registry"):
            add_mouse_click_handler(callback=self._on_mouse_down)
            add_mouse_release_handler(callback=self._on_mouse_up)

        self._current_width = current_width

    def _on_mouse_down(self, sender, app_data):
        """Start drag if mouse is over the splitter region."""
        mx, _ = get_mouse_pos(local=False)
        try:
            sx, _ = get_item_pos(self._splitter_tag)
        except Exception:
            return
        # Hit-test: allow a few extra pixels for easier grabbing
        if sx - 4 <= mx <= sx + SPLITTER_WIDTH + 4:
            self._dragging = True

    def _on_mouse_up(self, sender, app_data):
        self._dragging = False

    def update(self):
        """Call each frame. Resizes panes while dragging."""
        if not self._dragging:
            return

        mx, _ = get_mouse_pos(local=False)

        # Mouse X relative to viewport is roughly the desired left panel width
        # Account for a small window-chrome offset (~8px on most OSes)
        new_w = int(mx - 8)
        new_w = max(MIN_LEFT_PANEL_WIDTH, min(MAX_LEFT_PANEL_WIDTH, new_w))

        if new_w == self._current_width:
            return

        self._current_width = new_w

        configure_item("left_panel", width=new_w)
        configure_item("table_search", width=new_w - 20)
        configure_item("tables_panel", width=new_w)
