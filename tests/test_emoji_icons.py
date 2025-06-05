#!/usr/bin/env python3
"""Test Unicode emoji icons."""

from icon_manager import icon_manager


def test_unicode_icons():
    """Test Unicode emoji icons."""
    print("=== Unicode Emoji Icon Test ===")
    print(f"Using Unicode: {icon_manager.use_unicode}")
    print(f"Database: {icon_manager.get('database')}")
    print(f"Table: {icon_manager.get('table')}")
    print(f"Connect: {icon_manager.get('connect')}")
    print(f"Success: {icon_manager.get('success')}")
    print(f"Error: {icon_manager.get('error')}")
    print(f"Warning: {icon_manager.get('warning')}")
    print(f"Info: {icon_manager.get('info')}")
    print(f"Settings: {icon_manager.get('settings')}")
    
    print(f"\n=== Fallback ASCII Icons ===")
    icon_manager.enable_fallback_icons()
    print(f"Using Unicode: {icon_manager.use_unicode}")
    print(f"Database: {icon_manager.get('database')}")
    print(f"Table: {icon_manager.get('table')}")
    print(f"Connect: {icon_manager.get('connect')}")
    print(f"Success: {icon_manager.get('success')}")
    print(f"Error: {icon_manager.get('error')}")
    print(f"Warning: {icon_manager.get('warning')}")
    print(f"Info: {icon_manager.get('info')}")
    print(f"Settings: {icon_manager.get('settings')}")


if __name__ == "__main__":
    test_unicode_icons()


import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
