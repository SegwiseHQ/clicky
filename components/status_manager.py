"""Status manager component for ClickHouse Client."""

import time

from dearpygui.dearpygui import *

from config import COLOR_ERROR, COLOR_SUCCESS, TABLES_PANEL_WIDTH


class StatusManager:
    """Manages status messages display."""

    theme_manager = None  # Class variable to store theme manager

    @classmethod
    def set_theme_manager(cls, theme_manager):
        """Set the theme manager for styling status messages."""
        cls.theme_manager = theme_manager

    @staticmethod
    def show_status(message: str, error: bool = False):
        """Display a status message."""
        delete_item("status_text", children_only=True)
        if error:
            # For errors, show in both text and copyable input
            error_text_tag = f"error_text_{time.time()}"
            add_text(
                message,
                parent="status_text",
                color=COLOR_ERROR,
                tag=error_text_tag,
                wrap=TABLES_PANEL_WIDTH - 20,
            )
            if StatusManager.theme_manager:
                bind_item_theme(
                    error_text_tag, StatusManager.theme_manager.get_theme("error_text")
                )

            add_input_text(
                parent="status_text",
                default_value=message,
                readonly=True,
                multiline=True,
                width=-1,
                height=60,
            )
        else:
            success_text_tag = f"success_text_{time.time()}"
            add_text(
                message,
                parent="status_text",
                color=COLOR_SUCCESS,
                tag=success_text_tag,
                wrap=TABLES_PANEL_WIDTH - 20,
            )
            if StatusManager.theme_manager:
                bind_item_theme(
                    success_text_tag,
                    StatusManager.theme_manager.get_theme("success_text"),
                )
