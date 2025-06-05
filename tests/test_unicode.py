#!/usr/bin/env python3
"""Test Font Awesome character encoding."""

from font_manager import get_font_awesome_path
from icon_manager import icon_manager


def test_unicode_characters():
    """Test Unicode character handling."""
    print("=== Unicode Character Test ===")
    
    # Test Font Awesome Unicode directly
    fa_database = "\uf1c0"  # fa-database
    fa_table = "\uf0ce"     # fa-table
    fa_check = "\uf00c"     # fa-check
    
    print(f"Font Awesome database char: {repr(fa_database)}")
    print(f"Font Awesome table char: {repr(fa_table)}")
    print(f"Font Awesome check char: {repr(fa_check)}")
    
    # Test icon manager
    print(f"\nIcon manager database: {repr(icon_manager.get('database'))}")
    print(f"Icon manager table: {repr(icon_manager.get('table'))}")
    print(f"Icon manager success: {repr(icon_manager.get('success'))}")
    
    # Enable Font Awesome
    icon_manager.enable_font_awesome()
    print(f"\nAfter enabling Font Awesome:")
    print(f"Icon manager database: {repr(icon_manager.get('database'))}")
    print(f"Icon manager table: {repr(icon_manager.get('table'))}")
    print(f"Icon manager success: {repr(icon_manager.get('success'))}")
    
    # Test font path
    font_path = get_font_awesome_path()
    print(f"\nFont Awesome path: {font_path}")
    
    # Test encoding with different methods
    print(f"\nTesting different Unicode representations:")
    print(f"\\uf1c0 as bytes: {fa_database.encode('utf-8')}")
    print(f"\\uf1c0 as ord: {[ord(c) for c in fa_database]}")


if __name__ == "__main__":
    test_unicode_characters()


import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
