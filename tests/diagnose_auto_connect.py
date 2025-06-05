#!/usr/bin/env python3
"""Test to diagnose the auto-connect and table population issue."""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME
from credentials_manager import CredentialsManager
from database import DatabaseManager


def test_auto_connect_issue():
    """Test the exact auto-connect flow to find the issue."""
    print("=== Diagnosing Auto-Connect Issue ===")
    
    # Step 1: Load credentials (like auto_load_and_connect does)
    print("1. Loading credentials...")
    creds_manager = CredentialsManager()
    success, credentials, message = creds_manager.load_credentials_legacy()
    
    if not success or not credentials:
        print("❌ No credentials available")
        return False
    
    print(f"✅ Credentials loaded: {credentials['host']}")
    
    # Step 2: Test connection logic (like connect_callback does)
    print("\n2. Testing connection...")
    db_manager = DatabaseManager()
    
    host = credentials.get("host", DEFAULT_HOST)
    port = credentials.get("port", DEFAULT_PORT)
    username = credentials.get("user", DEFAULT_USERNAME)
    password = credentials.get("password", "")
    database = credentials.get("database", DEFAULT_DATABASE)
    
    print(f"   Parameters: {host}:{port}/{database}")
    
    success, conn_message = db_manager.connect(host, int(port), username, password, database)
    
    if not success:
        print(f"❌ Connection failed: {conn_message}")
        return False
    
    print(f"✅ Connection successful: {conn_message}")
    print(f"   is_connected: {db_manager.is_connected}")
    
    # Step 3: Test table loading (like refresh_tables does)
    print("\n3. Testing table loading...")
    
    try:
        tables = db_manager.get_tables()
        print(f"✅ Tables retrieved: {len(tables)} tables")
        print(f"   Sample tables: {tables[:5] if tables else 'None'}")
        
        # This is the key test - simulating refresh_tables logic
        if not db_manager.is_connected:
            print("❌ BUG: db_manager.is_connected is False after successful connection!")
            return False
        else:
            print("✅ Database connection state is correct")
            
        # Test the rebuild logic
        if tables:
            print("✅ Tables are available for UI population")
        else:
            print("❌ No tables returned despite connection")
            return False
        
    except Exception as e:
        print(f"❌ Table loading failed: {e}")
        return False
    
    # Step 4: Test what happens if we simulate the full flow
    print("\n4. Simulating auto-connect timing...")
    
    # Simulate what happens when auto_load_and_connect calls connect_callback
    # which then calls refresh_tables
    print("   a. Connection successful")
    print("   b. Status updated with success message")
    print("   c. refresh_tables called...")
    
    # The refresh_tables logic
    if not db_manager.is_connected:
        print("   ❌ Would show 'Connect to see tables'")
        return False
    else:
        print("   ✅ Would rebuild tables list")
        try:
            tables_check = db_manager.get_tables()
            print(f"   ✅ Tables available for rebuild: {len(tables_check)}")
        except Exception as e:
            print(f"   ❌ Tables not available: {e}")
            return False
    
    print("\n5. Summary...")
    print("✅ Credentials loading: WORKS")
    print("✅ Database connection: WORKS") 
    print("✅ Table retrieval: WORKS")
    print("✅ Connection state: CORRECT")
    
    # Clean up
    db_manager.disconnect()
    
    print("\n💡 The core logic appears to be working correctly.")
    print("   The issue might be:")
    print("   - UI timing (status updates happening before UI is ready)")
    print("   - Table browser not being called with status callback")
    print("   - refresh_tables not actually populating the UI")
    
    return True


if __name__ == "__main__":
    test_auto_connect_issue()
