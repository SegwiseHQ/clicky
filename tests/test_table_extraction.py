#!/usr/bin/env python3
"""Test table name extraction functionality."""

from database import DatabaseManager
from theme_manager import ThemeManager
from ui_components import TableBrowser


def test_table_name_extraction():
    """Test table name extraction from button tags."""    
    print("=== Table Name Extraction Test ===")
    
    # Test various table name scenarios
    test_cases = [
        "table_users",
        "table_📋orders", 
        "table_🗃️products",
        "table_system_logs",
        "table_user_preferences"
    ]
    
    for button_tag in test_cases:
        print(f"Button tag: {button_tag}")
        table_name = button_tag.replace("table_", "")
        print(f"Extracted table name: '{table_name}'")
        print("---")


if __name__ == "__main__":
    test_table_name_extraction()


import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
