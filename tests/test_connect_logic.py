#!/usr/bin/env python3
"""Test auto-connect functionality with stored credentials."""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME
from credentials_manager import CredentialsManager
from database import DatabaseManager


class MockUIHelpers:
    """Mock UIHelpers for testing."""
    @staticmethod
    def safe_get_value(tag, default):
        # Simulate form values not being available (like when connecting from menu)
        print(f"[MOCK] safe_get_value called for {tag}, returning default: {default}")
        return default

def test_connect_logic():
    """Test the connection logic with stored credentials."""
    print("Testing connection logic with stored credentials...")
    
    # Initialize components
    creds_manager = CredentialsManager()
    db_manager = DatabaseManager()
    
    # Load credentials like auto_load_and_connect does
    success, credentials, message = creds_manager.load_credentials_legacy()
    print(f"[DEBUG] Load credentials result: success={success}, message={message}")
    
    if not success or not credentials:
        print("❌ No credentials available for testing")
        return
    
    print(f"[DEBUG] Credentials found: {credentials}")
    
    # Store credentials like the app does
    stored_credentials = credentials
    
    # Simulate the connect_callback logic
    print("\n--- Simulating connect_callback logic ---")
    
    # Test both scenarios: with and without stored credentials
    scenarios = [
        ("With stored credentials", stored_credentials),
        ("Without stored credentials (form fallback)", None)
    ]
    
    for scenario_name, stored_creds in scenarios:
        print(f"\n{scenario_name}:")
        
        if stored_creds:
            print("[DEBUG] Using stored credentials for connection")
            host = stored_creds.get("host", DEFAULT_HOST)
            port = stored_creds.get("port", DEFAULT_PORT)
            username = stored_creds.get("user", DEFAULT_USERNAME)
            password = stored_creds.get("password", "")
            database = stored_creds.get("database", DEFAULT_DATABASE)
        else:
            print("[DEBUG] Using form values for connection (would be defaults)")
            # This simulates what would happen if form inputs don't exist
            host = MockUIHelpers.safe_get_value("host_input", DEFAULT_HOST)
            port = MockUIHelpers.safe_get_value("port_input", DEFAULT_PORT)
            username = MockUIHelpers.safe_get_value("username_input", DEFAULT_USERNAME)
            password = MockUIHelpers.safe_get_value("password_input", "")
            database = MockUIHelpers.safe_get_value("database_input", DEFAULT_DATABASE)
        
        print(f"[DEBUG] Connection parameters: host={host}, port={port}, username={username}, database={database}")
        
        # Test connection
        try:
            success, conn_message = db_manager.connect(host, int(port), username, password, database)
            print(f"[DEBUG] Connection attempt result: success={success}")
            if success:
                print(f"✅ {scenario_name}: Connection successful!")
                print(f"   Message: {conn_message}")
                db_manager.disconnect()
            else:
                print(f"❌ {scenario_name}: Connection failed")
                print(f"   Message: {conn_message}")
        except Exception as e:
            print(f"❌ {scenario_name}: Connection error - {e}")

if __name__ == "__main__":
    test_connect_logic()
