"""Font Manager for loading Font Awesome icons."""

from pathlib import Path


def get_bundled_font_awesome_path():
    """Get the path to the bundled Font Awesome font."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    fa_font_path = script_dir / "assets" / "fonts" / "fa-solid-900.ttf"

    if fa_font_path.exists():
        return str(fa_font_path)
    return None


def get_font_awesome_path():
    """Get the path to Font Awesome font, preferring bundled version."""
    # Only try bundled font since main app doesn't use Font Awesome
    return get_bundled_font_awesome_path()
