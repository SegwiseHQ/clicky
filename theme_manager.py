"""Theme and visual styling manager for ClickHouse Client."""

from dearpygui.dearpygui import *

from config import (
    COLOR_ACCENT,
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_BUTTON_DANGER,
    COLOR_BUTTON_PRIMARY,
    COLOR_BUTTON_SECONDARY,
    COLOR_BUTTON_SUCCESS,
    COLOR_CONNECTED,
    COLOR_DISCONNECTED,
    COLOR_ERROR,
    COLOR_EXPLORER_TITLE,
    COLOR_INFO,
    COLOR_PRIMARY,
    COLOR_STATUS_BG,
    COLOR_SUCCESS,
    COLOR_SURFACE,
    COLOR_TABLE_HEADER,
    COLOR_TABLE_ROW_ALT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
)


class ThemeManager:
    """Manages application themes and visual styling."""

    def __init__(self):
        self.themes = {}
        self._create_themes()

    def _create_themes(self):
        """Create all application themes."""
        self._create_global_theme()
        self._create_button_themes()
        self._create_table_themes()
        self._create_window_themes()
        self._create_input_themes()
        self._create_text_themes()

    def _create_global_theme(self):
        """Create the main application theme."""
        with theme() as self.themes['global']:
            with theme_component(mvAll):
                # Window background
                add_theme_color(mvThemeCol_WindowBg, COLOR_BACKGROUND)
                add_theme_color(mvThemeCol_ChildBg, COLOR_SURFACE)
                add_theme_color(mvThemeCol_PopupBg, COLOR_SURFACE)

                # Borders
                add_theme_color(mvThemeCol_Border, COLOR_BORDER)
                add_theme_color(mvThemeCol_BorderShadow, (0, 0, 0, 0))

                # Text
                add_theme_color(mvThemeCol_Text, COLOR_TEXT_PRIMARY)
                add_theme_color(mvThemeCol_TextDisabled, COLOR_TEXT_SECONDARY)

                # Scrollbars
                add_theme_color(mvThemeCol_ScrollbarBg, COLOR_SURFACE)
                add_theme_color(mvThemeCol_ScrollbarGrab, COLOR_ACCENT)
                add_theme_color(mvThemeCol_ScrollbarGrabHovered, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_ScrollbarGrabActive, COLOR_PRIMARY)

                # Frame background (for inputs, combos, etc.)
                add_theme_color(mvThemeCol_FrameBg, COLOR_SURFACE)
                add_theme_color(mvThemeCol_FrameBgHovered, COLOR_BORDER)
                add_theme_color(mvThemeCol_FrameBgActive, COLOR_ACCENT)

                # Headers
                add_theme_color(mvThemeCol_Header, COLOR_ACCENT)
                add_theme_color(mvThemeCol_HeaderHovered, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_HeaderActive, COLOR_PRIMARY)

                # Separators
                add_theme_color(mvThemeCol_Separator, COLOR_BORDER)
                add_theme_color(mvThemeCol_SeparatorHovered, COLOR_ACCENT)
                add_theme_color(mvThemeCol_SeparatorActive, COLOR_PRIMARY)

                # Resize grip
                add_theme_color(mvThemeCol_ResizeGrip, COLOR_ACCENT)
                add_theme_color(mvThemeCol_ResizeGripHovered, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_ResizeGripActive, COLOR_PRIMARY)

                # Tabs
                add_theme_color(mvThemeCol_Tab, COLOR_SURFACE)
                add_theme_color(mvThemeCol_TabHovered, COLOR_ACCENT)
                add_theme_color(mvThemeCol_TabActive, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_TabUnfocused, COLOR_SURFACE)
                add_theme_color(mvThemeCol_TabUnfocusedActive, COLOR_BORDER)

                # Style adjustments
                add_theme_style(mvStyleVar_WindowRounding, 8)
                add_theme_style(mvStyleVar_ChildRounding, 6)
                add_theme_style(mvStyleVar_FrameRounding, 4)
                add_theme_style(mvStyleVar_PopupRounding, 6)
                add_theme_style(mvStyleVar_ScrollbarRounding, 4)
                add_theme_style(mvStyleVar_GrabRounding, 4)
                add_theme_style(mvStyleVar_TabRounding, 4)
                add_theme_style(mvStyleVar_WindowPadding, 12, 12)
                add_theme_style(mvStyleVar_FramePadding, 8, 6)
                add_theme_style(mvStyleVar_ItemSpacing, 8, 6)
                add_theme_style(mvStyleVar_ItemInnerSpacing, 6, 6)
                add_theme_style(mvStyleVar_IndentSpacing, 20)

    def _create_button_themes(self):
        """Create button themes for different button types."""
        # Primary button theme
        with theme() as self.themes['button_primary']:
            with theme_component(mvButton):
                add_theme_color(mvThemeCol_Button, COLOR_BUTTON_PRIMARY)
                add_theme_color(mvThemeCol_ButtonHovered, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_ButtonActive, COLOR_ACCENT)
                add_theme_color(mvThemeCol_Text, (255, 255, 255))
                add_theme_style(mvStyleVar_FrameRounding, 6)
                add_theme_style(mvStyleVar_FramePadding, 12, 8)

        # Success button theme
        with theme() as self.themes['button_success']:
            with theme_component(mvButton):
                add_theme_color(mvThemeCol_Button, COLOR_BUTTON_SUCCESS)
                add_theme_color(mvThemeCol_ButtonHovered, COLOR_SUCCESS)
                add_theme_color(mvThemeCol_ButtonActive, (32, 134, 55))
                add_theme_color(mvThemeCol_Text, (255, 255, 255))
                add_theme_style(mvStyleVar_FrameRounding, 6)
                add_theme_style(mvStyleVar_FramePadding, 12, 8)

        # Danger button theme
        with theme() as self.themes['button_danger']:
            with theme_component(mvButton):
                add_theme_color(mvThemeCol_Button, COLOR_BUTTON_DANGER)
                add_theme_color(mvThemeCol_ButtonHovered, COLOR_ERROR)
                add_theme_color(mvThemeCol_ButtonActive, (176, 42, 55))
                add_theme_color(mvThemeCol_Text, (255, 255, 255))
                add_theme_style(mvStyleVar_FrameRounding, 6)
                add_theme_style(mvStyleVar_FramePadding, 12, 8)

        # Secondary button theme
        with theme() as self.themes['button_secondary']:
            with theme_component(mvButton):
                add_theme_color(mvThemeCol_Button, COLOR_BUTTON_SECONDARY)
                add_theme_color(mvThemeCol_ButtonHovered, COLOR_BORDER)
                add_theme_color(mvThemeCol_ButtonActive, COLOR_TEXT_SECONDARY)
                add_theme_color(mvThemeCol_Text, COLOR_TEXT_PRIMARY)
                add_theme_style(mvStyleVar_FrameRounding, 6)
                add_theme_style(mvStyleVar_FramePadding, 12, 8)

    def _create_table_themes(self):
        """Create table-specific themes."""
        # Enhanced table theme
        with theme() as self.themes['table_enhanced']:
            with theme_component(mvTable):
                add_theme_color(mvThemeCol_Header, COLOR_TABLE_HEADER)
                add_theme_color(mvThemeCol_HeaderHovered, COLOR_ACCENT)
                add_theme_color(mvThemeCol_HeaderActive, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_TableHeaderBg, COLOR_TABLE_HEADER)
                add_theme_color(mvThemeCol_TableBorderStrong, COLOR_BORDER)
                add_theme_color(mvThemeCol_TableBorderLight, COLOR_BORDER)
                add_theme_color(mvThemeCol_TableRowBg, (0, 0, 0, 0))
                add_theme_color(mvThemeCol_TableRowBgAlt, COLOR_TABLE_ROW_ALT)
                add_theme_style(mvStyleVar_CellPadding, 12, 8)
                add_theme_style(mvStyleVar_ItemSpacing, 0, 2)

        # Left-aligned table button theme
        with theme() as self.themes['table_button']:
            with theme_component(mvButton):
                add_theme_style(mvStyleVar_ButtonTextAlign, 0.0, 0.5)
                add_theme_color(mvThemeCol_Button, COLOR_SURFACE)
                add_theme_color(mvThemeCol_ButtonHovered, COLOR_ACCENT)
                add_theme_color(mvThemeCol_ButtonActive, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_Text, COLOR_TEXT_PRIMARY)
                add_theme_style(mvStyleVar_FrameRounding, 4)
                add_theme_style(mvStyleVar_FramePadding, 8, 6)

        # Selected table button theme - highlighted with accent color
        with theme() as self.themes["selected_table_button"]:
            with theme_component(mvButton):
                add_theme_style(mvStyleVar_ButtonTextAlign, 0.0, 0.5)
                add_theme_color(mvThemeCol_Button, COLOR_ACCENT)
                add_theme_color(mvThemeCol_ButtonHovered, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_ButtonActive, COLOR_PRIMARY)
                add_theme_color(mvThemeCol_Text, COLOR_TEXT_PRIMARY)
                add_theme_style(mvStyleVar_FrameRounding, 4)
                add_theme_style(mvStyleVar_FramePadding, 8, 6)

    def _create_window_themes(self):
        """Create window-specific themes."""
        # Status window theme
        with theme() as self.themes['status_window']:
            with theme_component(mvChildWindow):
                add_theme_color(mvThemeCol_ChildBg, COLOR_STATUS_BG)
                add_theme_color(mvThemeCol_Border, COLOR_BORDER)
                add_theme_style(mvStyleVar_ChildRounding, 6)
                add_theme_style(mvStyleVar_WindowPadding, 10, 10)

        # Tables panel theme
        with theme() as self.themes['tables_panel']:
            with theme_component(mvChildWindow):
                add_theme_color(mvThemeCol_ChildBg, COLOR_SURFACE)
                add_theme_color(mvThemeCol_Border, COLOR_BORDER)
                add_theme_style(mvStyleVar_ChildRounding, 8)
                add_theme_style(mvStyleVar_WindowPadding, 8, 8)

    def _create_input_themes(self):
        """Create input field themes."""
        # Enhanced input theme
        with theme() as self.themes['input_enhanced']:
            with theme_component(mvInputText):
                add_theme_color(mvThemeCol_FrameBg, COLOR_SURFACE)
                add_theme_color(mvThemeCol_FrameBgHovered, COLOR_BORDER)
                add_theme_color(mvThemeCol_FrameBgActive, COLOR_ACCENT)
                add_theme_color(mvThemeCol_Text, COLOR_TEXT_PRIMARY)
                add_theme_style(mvStyleVar_FrameRounding, 4)
                add_theme_style(mvStyleVar_FramePadding, 8, 6)

        # Combo box theme
        with theme() as self.themes['combo_enhanced']:
            with theme_component(mvCombo):
                add_theme_color(mvThemeCol_FrameBg, COLOR_SURFACE)
                add_theme_color(mvThemeCol_FrameBgHovered, COLOR_BORDER)
                add_theme_color(mvThemeCol_FrameBgActive, COLOR_ACCENT)
                add_theme_color(mvThemeCol_Text, COLOR_TEXT_PRIMARY)
                add_theme_color(mvThemeCol_Button, COLOR_ACCENT)
                add_theme_color(mvThemeCol_ButtonHovered, COLOR_PRIMARY)
                add_theme_style(mvStyleVar_FrameRounding, 4)
                add_theme_style(mvStyleVar_FramePadding, 8, 6)

    def _create_text_themes(self):
        """Create text-specific themes."""
        # Header text theme
        with theme() as self.themes['header_text']:
            with theme_component(mvText):
                add_theme_color(mvThemeCol_Text, COLOR_EXPLORER_TITLE)

        # Success text theme
        with theme() as self.themes['success_text']:
            with theme_component(mvText):
                add_theme_color(mvThemeCol_Text, COLOR_SUCCESS)

        # Error text theme
        with theme() as self.themes['error_text']:
            with theme_component(mvText):
                add_theme_color(mvThemeCol_Text, COLOR_ERROR)

        # Warning text theme
        with theme() as self.themes['warning_text']:
            with theme_component(mvText):
                add_theme_color(mvThemeCol_Text, COLOR_WARNING)

        # Info text theme
        with theme() as self.themes['info_text']:
            with theme_component(mvText):
                add_theme_color(mvThemeCol_Text, COLOR_INFO)

        # Column text theme
        with theme() as self.themes['column_text']:
            with theme_component(mvText):
                add_theme_color(mvThemeCol_Text, COLOR_SUCCESS)

    def apply_global_theme(self):
        """Apply the global theme to the application."""
        bind_theme(self.themes['global'])

    def get_theme(self, theme_name: str):
        """Get a specific theme by name."""
        return self.themes.get(theme_name)

    def create_connection_indicator_theme(self, connected: bool):
        """Create a dynamic theme for connection indicator."""
        theme_name = f'connection_indicator_{"connected" if connected else "disconnected"}'

        if theme_name not in self.themes:
            with theme() as self.themes[theme_name]:
                with theme_component(mvText):
                    color = COLOR_CONNECTED if connected else COLOR_DISCONNECTED
                    add_theme_color(mvThemeCol_Text, color)

        return self.themes[theme_name]
