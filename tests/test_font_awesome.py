#!/usr/bin/env python3
"""Test Font Awesome icons in DearPyGUI."""

from dearpygui.dearpygui import *

from font_manager import get_font_awesome_path
from icon_manager import icon_manager


def test_font_awesome_gui():
    """Test Font Awesome icons in a DearPyGUI window."""
    create_context()
    create_viewport(title="Font Awesome Test", width=400, height=300)
    
    # Load Font Awesome font
    font_path = get_font_awesome_path()
    print(f"Font Awesome path: {font_path}")
    
    if font_path:
        with font_registry():
            add_font(font_path, 16, tag="font_awesome")
            print("Font Awesome loaded successfully")
    
    with window(label="Font Awesome Test", tag="main_window"):
        # Test with ASCII icons first
        add_text("ASCII Icons:")
        add_text(f"Table: {icon_manager.get('table')}")
        add_text(f"Database: {icon_manager.get('database')}")
        add_text(f"Success: {icon_manager.get('success')}")
        add_text(f"Error: {icon_manager.get('error')}")
        
        add_separator()
        
        # Enable Font Awesome and test
        icon_manager.enable_font_awesome()
        add_text("Font Awesome Icons:")
        
        # Create text elements with Font Awesome font
        add_text(f"Table: {icon_manager.get('table')}", tag="fa_table")
        add_text(f"Database: {icon_manager.get('database')}", tag="fa_database")
        add_text(f"Success: {icon_manager.get('success')}", tag="fa_success")
        add_text(f"Error: {icon_manager.get('error')}", tag="fa_error")
        
        # Bind Font Awesome font to these elements
        if font_path:
            try:
                bind_item_font("fa_table", "font_awesome")
                bind_item_font("fa_database", "font_awesome")
                bind_item_font("fa_success", "font_awesome")
                bind_item_font("fa_error", "font_awesome")
                print("Font Awesome bound to text elements")
            except Exception as e:
                print(f"Error binding font: {e}")
    
    set_primary_window("main_window", True)
    start_dearpygui()
    destroy_context()


if __name__ == "__main__":
    test_font_awesome_gui()


import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
