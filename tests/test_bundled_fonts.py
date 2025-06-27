#!/usr/bin/env python3
"""Test script to verify bundled fonts are working correctly."""

import os
import sys

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import FontManager


def test_bundled_fonts():
    """Test that bundled fonts can be loaded."""
    print("Testing bundled font loading...")
    
    # Test assets path
    assets_path = FontManager.get_assets_path()
    print(f"Assets path: {assets_path}")
    
    # Check if fonts directory exists
    fonts_dir = os.path.join(assets_path, "fonts")
    if not os.path.exists(fonts_dir):
        print(f"❌ Fonts directory not found: {fonts_dir}")
        return False
    
    print(f"✅ Fonts directory found: {fonts_dir}")
    
    # List all fonts
    font_files = [f for f in os.listdir(fonts_dir) if f.endswith('.ttf')]
    print(f"Available fonts: {font_files}")
    
    # Check specific fonts
    required_fonts = [
        "JetBrainsMono-Regular.ttf",
        "JetBrainsMono-Bold.ttf",
        "fa-solid-900.ttf"
    ]
    
    all_fonts_present = True
    for font_file in required_fonts:
        font_path = os.path.join(fonts_dir, font_file)
        if os.path.exists(font_path):
            file_size = os.path.getsize(font_path)
            print(f"✅ {font_file} found ({file_size:,} bytes)")
        else:
            print(f"❌ {font_file} not found")
            all_fonts_present = False
    
    return all_fonts_present


def test_font_loading():
    """Test font loading without GUI."""
    print("\nTesting font path resolution...")
    
    # Test the font manager methods
    try:
        assets_path = FontManager.get_assets_path()
        regular_font_path = os.path.join(assets_path, "fonts", "JetBrainsMono-Regular.ttf")
        bold_font_path = os.path.join(assets_path, "fonts", "JetBrainsMono-Bold.ttf")
        
        print(f"Regular font path: {regular_font_path}")
        print(f"Bold font path: {bold_font_path}")
        
        if os.path.exists(regular_font_path):
            print("✅ Regular font path is valid")
        else:
            print("❌ Regular font path is invalid")
            
        if os.path.exists(bold_font_path):
            print("✅ Bold font path is valid")
        else:
            print("❌ Bold font path is invalid")
            
    except Exception as e:
        print(f"❌ Error testing font paths: {e}")
        return False
        
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("BUNDLED FONTS TEST")
    print("=" * 50)
    
    success = True
    
    # Test font files exist
    if not test_bundled_fonts():
        success = False
    
    # Test font loading logic
    if not test_font_loading():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Bundled fonts are ready to use.")
    else:
        print("❌ Some tests failed. Check the output above.")
    print("=" * 50)
