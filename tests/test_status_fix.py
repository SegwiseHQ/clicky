#!/usr/bin/env python3
"""Test the UI status fix for connection indicators."""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME
from credentials_manager import CredentialsManager
from database import DatabaseManager
from ui_components import TableBrowser


class MockStatusCallback:
    """Mock status callback to track status messages."""
    
    def __init__(self):
        self.messages = []
    
    def __call__(self, message, error=False):
        """Record status messages."""
        self.messages.append({
            'message': message,
            'error': error,
            'timestamp': len(self.messages)
        })
        print(f"STATUS: {'ERROR' if error else 'INFO'} - {message}")

def test_status_fix():
    """Test that status messages aren't overwritten during table refresh."""
    print("=== Testing UI Status Fix ===")
    
    # Load credentials
    creds_manager = CredentialsManager()
    success, credentials, message = creds_manager.load_credentials_legacy()
    
    if not success or not credentials:
        print("❌ No credentials available for testing")
        return
    
    print(f"✅ Credentials loaded: {credentials['host']}")
    
    # Set up components
    db_manager = DatabaseManager()
    mock_status = MockStatusCallback()
    table_browser = TableBrowser(db_manager)
    table_browser.set_status_callback(mock_status)
    
    # Test connection
    host = credentials.get("host", DEFAULT_HOST)
    port = credentials.get("port", DEFAULT_PORT)
    username = credentials.get("user", DEFAULT_USERNAME)
    password = credentials.get("password", "")
    database = credentials.get("database", DEFAULT_DATABASE)
    
    print(f"\n--- Testing Connection Flow ---")
    print(f"Connecting to: {host}:{port}/{database}")
    
    # Step 1: Connect
    success, conn_message = db_manager.connect(host, int(port), username, password, database)
    
    if not success:
        print(f"❌ Connection failed: {conn_message}")
        return
    
    print(f"✅ Connection successful: {conn_message}")
    
    # Step 2: Simulate what happens in connect_callback
    mock_status(conn_message, False)  # This simulates StatusManager.show_status(message)
    
    print(f"Status after connection success: {mock_status.messages[-1]}")
    
    # Step 3: Call refresh_tables (this is where the bug was)
    print("\n--- Testing refresh_tables (the fixed method) ---")
    table_browser.refresh_tables()
    
    # Check if status was overwritten
    if len(mock_status.messages) > 1:
        last_status = mock_status.messages[-1]
        if last_status['error'] and "Not connected" in last_status['message']:
            print("❌ BUG: refresh_tables overwrote success status with error!")
        else:
            print(f"✅ SUCCESS: Status shows: {last_status['message']}")
    else:
        print("✅ SUCCESS: No status overwrite occurred")
    
    print(f"\n--- Final Status Messages ---")
    for i, msg in enumerate(mock_status.messages):
        print(f"{i+1}. {'ERROR' if msg['error'] else 'INFO'}: {msg['message']}")
    
    # Clean up
    db_manager.disconnect()
    print("\n✅ Test completed")

if __name__ == "__main__":
    test_status_fix()
