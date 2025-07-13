#!/usr/bin/env python3
"""Debug the status issue with auto-connect."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

from app import ClickHouseClientApp


def test_auto_connect():
    """Test the auto-connect functionality and status updates."""
    print("=== Testing Auto-Connect Status Issue ===")
    
    # Create app instance
    app = ClickHouseClientApp()
    
    # Mock the DearPyGUI functions to avoid actual UI creation

    # Create mock functions to track what's happening
    status_messages = []
    ui_updates = []
    
    def mock_add_text(text, parent=None, color=None, tag=None):
        ui_updates.append(f"add_text: {text} (parent={parent}, color={color})")
        return True
    
    def mock_delete_item(item, children_only=False):
        ui_updates.append(f"delete_item: {item} (children_only={children_only})")
        return True
    
    def mock_bind_item_theme(item, theme):
        ui_updates.append(f"bind_item_theme: {item} -> {theme}")
        return True
    
    def mock_configure_item(item, **kwargs):
        ui_updates.append(f"configure_item: {item} -> {kwargs}")
        return True
    
    # Mock the UI functions
    import dearpygui.dearpygui as dpg
    dpg.add_text = mock_add_text
    dpg.delete_item = mock_delete_item
    dpg.bind_item_theme = mock_bind_item_theme
    dpg.configure_item = mock_configure_item
    
    # Mock status manager
    class MockStatusManager:
        @staticmethod
        def show_status(message, error=False):
            status_messages.append(f"Status: {message} (error={error})")
            print(f"[STATUS] {message} (error={error})")
    
    # Replace the StatusManager
    import app
    app.StatusManager = MockStatusManager
    
    # Test the auto-connect process
    print("\n1. Testing auto_load_and_connect...")
    try:
        app.auto_load_and_connect()
        print("✓ Auto-connect completed without exception")
    except Exception as e:
        print(f"✗ Auto-connect failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n2. Status messages captured: {len(status_messages)}")
    for msg in status_messages:
        print(f"  - {msg}")
    
    print(f"\n3. UI updates captured: {len(ui_updates)}")
    for update in ui_updates:
        print(f"  - {update}")
    
    # Test the table refresh specifically
    print("\n4. Testing table refresh...")
    try:
        app.table_browser.refresh_tables()
        print("✓ Table refresh completed")
    except Exception as e:
        print(f"✗ Table refresh failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auto_connect()
