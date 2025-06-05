"""Font Manager for loading Font Awesome icons."""

import os
import urllib.request
from pathlib import Path


def download_font_awesome():
    """Download Font Awesome font file if not already present."""
    assets_dir = Path("assets")
    fonts_dir = assets_dir / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    fa_font_path = fonts_dir / "fa-solid-900.ttf"
    
    if fa_font_path.exists():
        print(f"Font Awesome font already exists at: {fa_font_path}")
        return str(fa_font_path)
    
    try:
        print("Downloading Font Awesome font...")
        # Font Awesome 6 Free Solid font URL
        font_url = "https://github.com/FortAwesome/Font-Awesome/raw/6.x/webfonts/fa-solid-900.ttf"
        
        urllib.request.urlretrieve(font_url, fa_font_path)
        print(f"Font Awesome font downloaded to: {fa_font_path}")
        return str(fa_font_path)
        
    except Exception as e:
        print(f"Failed to download Font Awesome font: {e}")
        return None

def get_font_awesome_path():
    """Get the path to Font Awesome font, downloading if necessary."""
    return download_font_awesome()

# Alternative: Use system Font Awesome if available
def find_system_font_awesome():
    """Try to find Font Awesome font in system font directories."""
    possible_paths = [
        "/System/Library/Fonts/Font Awesome 6 Free-Solid-900.otf",
        "/Library/Fonts/Font Awesome 6 Free-Solid-900.otf",
        "~/Library/Fonts/Font Awesome 6 Free-Solid-900.otf",
        "/usr/share/fonts/truetype/font-awesome/fa-solid-900.ttf",
        "~/.local/share/fonts/fa-solid-900.ttf"
    ]
    
    for path in possible_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            return expanded_path
    
    return None
