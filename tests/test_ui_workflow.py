#!/usr/bin/env python3
"""
Test to isolate the UI status update issue.

This test simulates the exact sequence that happens in the real app:
1. Initialize status with "Not connected"
2. Successfully connect 
3. Call StatusManager.show_status with success message
4. Call table_browser.refresh_tables()
5. Check final status
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME
from credentials_manager import CredentialsManager
from database import DatabaseManager
from ui_components import StatusManager, TableBrowser


# Mock DearPyGUI functions since we're not running the full UI
class MockDPG:
    def __init__(self):
        self.items = {}
        self.status_text_content = "Not connected"  # Initial status
    
    def delete_item(self, tag, children_only=False):
        print(f"[MOCK] delete_item({tag}, children_only={children_only})")
    
    def add_text(self, text, parent=None, color=None, tag=None):
        if parent == "status_text":
            self.status_text_content = text
            print(f"[MOCK] Status updated to: '{text}' (color: {color})")
        else:
            print(f"[MOCK] add_text('{text}', parent={parent}, color={color}, tag={tag})")
    
    def add_input_text(self, parent=None, default_value="", readonly=False, multiline=False, width=-1, height=60):
        if parent == "status_text":
            print(f"[MOCK] Status input added: '{default_value}'")
    
    def get_current_status(self):
        return self.status_text_content

# Monkey patch DearPyGUI functions
mock_dpg = MockDPG()

import ui_components

ui_components.delete_item = mock_dpg.delete_item
ui_components.add_text = mock_dpg.add_text
ui_components.add_input_text = mock_dpg.add_input_text

# Also patch in StatusManager directly
import builtins

setattr(builtins, 'delete_item', mock_dpg.delete_item)
setattr(builtins, 'add_text', mock_dpg.add_text)
setattr(builtins, 'add_input_text', mock_dpg.add_input_text)

def test_ui_status_workflow():
    """Test the exact UI status update workflow."""
    print("=== Testing UI Status Update Workflow ===")
    
    # Step 1: Initialize with "Not connected" (this happens in _setup_status_section)
    print("\n1. Initialize status (like _setup_status_section does):")
    StatusManager.show_status("Not connected", error=True)
    print(f"   Initial status: '{mock_dpg.get_current_status()}'")
    
    # Step 2: Load credentials and setup components
    print("\n2. Load credentials and setup:")
    creds_manager = CredentialsManager()
    success, credentials, message = creds_manager.load_credentials_legacy()
    
    if not success or not credentials:
        print("❌ No credentials available for testing")
        return
    
    print(f"   ✅ Credentials loaded: {credentials['host']}")
    
    # Step 3: Connect to database (simulate connect_callback)
    print("\n3. Connect to database:")
    db_manager = DatabaseManager()
    
    host = credentials.get("host", DEFAULT_HOST)
    port = credentials.get("port", DEFAULT_PORT)
    username = credentials.get("user", DEFAULT_USERNAME)
    password = credentials.get("password", "")
    database = credentials.get("database", DEFAULT_DATABASE)
    
    success, conn_message = db_manager.connect(host, int(port), username, password, database)
    
    if not success:
        print(f"❌ Connection failed: {conn_message}")
        return
    
    print(f"   ✅ Connection successful: {conn_message}")
    
    # Step 4: Update status with success message (this happens in connect_callback)
    print("\n4. Update status with success message:")
    StatusManager.show_status(conn_message, error=False)
    print(f"   Status after success update: '{mock_dpg.get_current_status()}'")
    
    # Step 5: Call refresh_tables (this is where the issue might be)
    print("\n5. Call refresh_tables (potential issue point):")
    table_browser = TableBrowser(db_manager)
    
    # Set up a callback to monitor any status changes
    def monitor_status_callback(message, error=False):
        print(f"   [CALLBACK] Status change: '{message}' (error: {error})")
        StatusManager.show_status(message, error)
    
    table_browser.set_status_callback(monitor_status_callback)
    
    # This is the critical call that might overwrite the status
    table_browser.refresh_tables()
    
    print(f"   Final status after refresh_tables: '{mock_dpg.get_current_status()}'")
    
    # Step 6: Summary
    print(f"\n=== SUMMARY ===")
    current_status = mock_dpg.get_current_status()
    
    if "Not connected" in current_status:
        print("❌ BUG CONFIRMED: Status still shows 'Not connected' despite successful connection!")
        print("   This explains why the UI shows wrong status.")
    elif "Connected successfully" in current_status or "Found" in current_status:
        print("✅ SUCCESS: Status correctly shows connection information!")
    else:
        print(f"? UNKNOWN: Status shows: '{current_status}'")
    
    # Cleanup
    db_manager.disconnect()

if __name__ == "__main__":
    test_ui_status_workflow()
