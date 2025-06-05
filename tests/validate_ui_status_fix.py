#!/usr/bin/env python3
"""Validate that UI status indicator fixes are working correctly."""

import os
import sys
from unittest.mock import MagicMock

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME
from credentials_manager import CredentialsManager
from database import DatabaseManager
from ui_components import UIComponents


class StatusTracker:
    """Track status updates during the workflow."""
    
    def __init__(self):
        self.status_messages = []
        self.error_states = []
    
    def status_callback(self, message, is_error=False):
        """Mock status callback that tracks all messages."""
        self.status_messages.append(message)
        self.error_states.append(is_error)
        print(f"Status: {'❌' if is_error else '✅'} {message}")


def validate_ui_status_fix():
    """Validate that the UI status fix is working correctly."""
    print("=== Validating UI Status Indicator Fix ===")
    
    # Load credentials
    creds_manager = CredentialsManager()
    success, credentials, message = creds_manager.load_credentials_legacy()
    
    if not success or not credentials:
        print("❌ No credentials available")
        return False
    
    print(f"✅ Credentials loaded: {credentials['host']}")
    
    # Create database manager
    db_manager = DatabaseManager()
    
    # Create status tracker
    status_tracker = StatusTracker()
    
    # Create mock UI components
    ui_components = UIComponents(db_manager, status_tracker.status_callback)
    
    # Mock DearPyGUI functions that would be called in refresh_tables
    import ui_components as ui_comp_module
    ui_comp_module.delete_item = MagicMock()
    ui_comp_module.add_text = MagicMock()
    ui_comp_module.add_selectable = MagicMock()
    
    print("\n--- Testing Workflow ---")
    
    # Step 1: Initial state (should show not connected)
    print("\n1. Initial refresh_tables() call:")
    ui_components.refresh_tables()
    
    # Step 2: Connect to database
    print("\n2. Connecting to database:")
    host = credentials.get("host", DEFAULT_HOST)
    port = credentials.get("port", DEFAULT_PORT) 
    username = credentials.get("user", DEFAULT_USERNAME)
    password = credentials.get("password", "")
    database = credentials.get("database", DEFAULT_DATABASE)
    
    success, conn_message = db_manager.connect(host, int(port), username, password, database)
    
    if success:
        # Simulate what happens in the UI when connection succeeds
        status_tracker.status_callback(conn_message, False)
        print(f"✅ Connection successful: {conn_message}")
    else:
        print(f"❌ Connection failed: {conn_message}")
        return False
    
    # Step 3: Refresh tables after connection (this was the problematic part)
    print("\n3. refresh_tables() after connection:")
    ui_components.refresh_tables()
    
    # Analyze results
    print("\n--- Analysis ---")
    print(f"Total status messages: {len(status_tracker.status_messages)}")
    for i, (msg, is_error) in enumerate(zip(status_tracker.status_messages, status_tracker.error_states)):
        print(f"  {i+1}. {'❌' if is_error else '✅'} {msg}")
    
    # Check if the last message is still the success message
    if status_tracker.status_messages:
        last_message = status_tracker.status_messages[-1]
        last_is_error = status_tracker.error_states[-1]
        
        if "Connected successfully" in last_message and not last_is_error:
            print("\n✅ SUCCESS: Last status message is still the success message!")
            print("✅ UI status indicators should now show connected state correctly.")
            return True
        else:
            print(f"\n❌ ISSUE: Last status message is: {last_message} (error: {last_is_error})")
            return False
    else:
        print("\n❌ No status messages recorded")
        return False


if __name__ == "__main__":
    success = validate_ui_status_fix()
    sys.exit(0 if success else 1)
