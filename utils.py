"""Utility functions for ClickHouse Client."""

import os

from dearpygui.dearpygui import *


class FontManager:
    """Manages font loading and configuration."""

    @staticmethod
    def get_assets_path():
        """Get the path to the assets directory."""
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root and then to assets
        return os.path.join(script_dir, "assets")

    @staticmethod
    def setup_monospace_font():
        """Setup JetBrains Mono font from bundled assets."""
        with font_registry():
            # Get the bundled font path
            assets_path = FontManager.get_assets_path()
            bundled_font_path = os.path.join(
                assets_path, "fonts", "JetBrainsMono-Regular.ttf"
            )

            # Try to load the bundled font first
            if os.path.exists(bundled_font_path):
                try:
                    print(
                        f"Loading bundled JetBrains Mono font from: {bundled_font_path}"
                    )
                    monospace_font = add_font(bundled_font_path, 16)
                    bind_font(monospace_font)
                    return True
                except Exception as e:
                    print(f"Failed to load bundled font: {e}")
            else:
                print(f"Bundled font not found at: {bundled_font_path}")

            # Fallback to system fonts if bundled font fails
            print("Bundled font not available, trying system fallback fonts...")
            system_fallback_fonts = [
                ("~/Library/Fonts/JetBrainsMono-Regular.ttf", "JetBrains Mono (User)"),
                ("/System/Library/Fonts/Monaco.ttf", "Monaco"),
                ("/System/Library/Fonts/Menlo.ttc", "Menlo"),
            ]

            for font_path, font_name in system_fallback_fonts:
                try:
                    # Expand user path if needed
                    if font_path.startswith("~/"):
                        font_path = os.path.expanduser(font_path)

                    if os.path.exists(font_path):
                        print(
                            f"Loading system fallback font {font_name} from: {font_path}"
                        )
                        monospace_font = add_font(font_path, 14)
                        bind_font(monospace_font)
                        return True
                except Exception as e:
                    print(f"Failed to load {font_name} font: {e}")
                    continue

            # Use default font if all custom fonts fail
            print("Using default system font")
            return False

    @staticmethod
    def setup_bold_font():
        """Setup JetBrains Mono Bold font from bundled assets for headers."""
        assets_path = FontManager.get_assets_path()
        bundled_font_path = os.path.join(assets_path, "fonts", "JetBrainsMono-Bold.ttf")

        if os.path.exists(bundled_font_path):
            try:
                print(
                    f"Loading bundled JetBrains Mono Bold font from: {bundled_font_path}"
                )
                bold_font = add_font(bundled_font_path, 16)
                return bold_font
            except Exception as e:
                print(f"Failed to load bundled bold font: {e}")

        return None


class UIHelpers:
    """Helper functions for UI operations."""

    @staticmethod
    def safe_get_value(tag: str, default=""):
        """Safely get value from a UI component."""
        try:
            return get_value(tag) or default
        except:
            return default

    @staticmethod
    def safe_configure_item(tag: str, **kwargs):
        """Safely configure a UI item."""
        try:
            # Check if the item exists first
            if does_item_exist(tag):
                configure_item(tag, **kwargs)
                return True
            else:
                print(f"[DEBUG] Item {tag} does not exist, skipping configuration")
                return False
        except Exception as e:
            print(f"[DEBUG] Failed to configure item {tag}: {e}")
            return False

    @staticmethod
    def safe_delete_item(tag: str, children_only: bool = False):
        """Safely delete a UI item."""
        try:
            delete_item(tag, children_only=children_only)
            return True
        except:
            return False

    @staticmethod
    def safe_bind_item_theme(tag: str, theme):
        """Safely bind a theme to a UI item."""
        try:
            # Check if the item exists first
            if does_item_exist(tag):
                bind_item_theme(tag, theme)
                return True
            else:
                print(f"[DEBUG] Item {tag} does not exist, skipping theme binding")
                return False
        except Exception as e:
            print(f"[DEBUG] Failed to bind theme to {tag}: {e}")
            return False


def validate_connection_params(
    host: str, port: str, username: str, database: str
) -> tuple[bool, str]:
    """
    Validate connection parameters.

    Args:
        host: Database host
        port: Database port
        username: Database username
        database: Database name

    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not all([host, port, username, database]):
        return False, "All fields except password must be filled"

    try:
        port_int = int(port)
        if port_int <= 0 or port_int > 65535:
            return False, "Port must be between 1 and 65535"
    except ValueError:
        return False, f"Port must be a number, got: {port}"

    return True, ""


def format_connection_string(host: str, port: str, database: str) -> str:
    """Format a connection string for display."""
    return f"{host}:{port}/{database}"


class TableHelpers:
    """Helper functions for table operations."""

    @staticmethod
    def add_resizable_column(
        label: str,
        parent: str,
        initial_width: int = 350,
        allow_stretch: bool = False,
        allow_resize: bool = True,
    ):
        """
        Add a table column with standardized resizing behavior.

        Args:
            label: Column header text
            parent: Parent table tag
            initial_width: Initial column width in pixels
            allow_stretch: Whether column should stretch to fill space
            allow_resize: Whether user can manually resize the column

        Returns:
            Column tag
        """
        return add_table_column(
            label=label,
            parent=parent,
            init_width_or_weight=initial_width,
            width_stretch=allow_stretch,
            width_fixed=False,  # Explicitly allow width changes
            no_resize=not allow_resize,
        )

    @staticmethod
    def create_data_table(
        tag: str, parent: str, enable_resize: bool = True, enable_sorting: bool = False
    ):
        """
        Create a standardized data table with consistent settings.

        Args:
            tag: Table tag
            parent: Parent container tag
            enable_resize: Whether columns should be resizable
            enable_sorting: Whether columns should be sortable

        Returns:
            Table tag
        """
        return add_table(
            tag=tag,
            parent=parent,
            borders_innerH=True,
            borders_innerV=True,
            borders_outerH=True,
            borders_outerV=True,
            header_row=True,
            scrollX=True,
            scrollY=True,
            freeze_rows=1,
            height=-1,
            resizable=enable_resize,
            sortable=enable_sorting,
        )
