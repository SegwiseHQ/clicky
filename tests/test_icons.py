#!/usr/bin/env python3
"""Test script to verify Font Awesome icons are working."""

import os
import sys

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from icon_manager import icon_manager


def test_icons():
    """Test icon manager functionality."""
    print("=== Icon Manager Test ===")
    print(f"Using Font Awesome: {icon_manager.use_font_awesome}")
    print(f"Table icon: '{icon_manager.get('table')}'")
    print(f"Database icon: '{icon_manager.get('database')}'")
    print(f"Query icon: '{icon_manager.get('query')}'")
    print(f"Connect icon: '{icon_manager.get('connect')}'")
    print(f"Success icon: '{icon_manager.get('success')}'")
    print(f"Error icon: '{icon_manager.get('error')}'")
    
    # Enable Font Awesome and test again
    print("\n=== After enabling Font Awesome ===")
    icon_manager.enable_font_awesome()
    print(f"Using Font Awesome: {icon_manager.use_font_awesome}")
    print(f"Table icon: '{icon_manager.get('table')}'")
    print(f"Database icon: '{icon_manager.get('database')}'")
    print(f"Query icon: '{icon_manager.get('query')}'")
    print(f"Connect icon: '{icon_manager.get('connect')}'")
    print(f"Success icon: '{icon_manager.get('success')}'")
    print(f"Error icon: '{icon_manager.get('error')}'")

if __name__ == "__main__":
    test_icons()
