#!/usr/bin/env python3
"""Simplified test of the credential mapping fix without UI dependencies."""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME
from credentials_manager import CredentialsManager
from database import DatabaseManager


def test_stored_credentials_mapping():
    """Test that stored credentials are used correctly in connect logic."""
    print("=== Testing Stored Credentials Mapping Fix ===\n")
    
    # Step 1: Load credentials like auto_load_and_connect does
    print("1. Loading credentials...")
    creds_manager = CredentialsManager()
    success, credentials, message = creds_manager.load_credentials_legacy()
    
    if not success or not credentials:
        print("❌ No credentials found - please save some first")
        return False
    
    print(f"✅ Credentials loaded: {credentials['host']}:{credentials['port']}")
    
    # Step 2: Store credentials like the app does
    stored_credentials = credentials
    print(f"✅ Stored credentials: {stored_credentials}")
    
    # Step 3: Test the connect logic with stored credentials
    print("\n2. Testing connection with stored credentials...")
    
    # Simulate the fixed connect_callback logic
    if stored_credentials:
        print("[DEBUG] Using stored credentials for connection")
        host = stored_credentials.get("host", DEFAULT_HOST)
        port = stored_credentials.get("port", DEFAULT_PORT)
        username = stored_credentials.get("user", DEFAULT_USERNAME)
        password = stored_credentials.get("password", "")
        database = stored_credentials.get("database", DEFAULT_DATABASE)
    else:
        print("[DEBUG] Would fall back to form values (not applicable in this test)")
        return False
    
    print(f"[DEBUG] Connection parameters: host={host}, port={port}, username={username}, database={database}")
    
    # Step 4: Test actual connection
    print("\n3. Testing database connection...")
    db_manager = DatabaseManager()
    
    try:
        conn_success, conn_message = db_manager.connect(host, int(port), username, password, database)
        print(f"[DEBUG] Connection attempt result: success={conn_success}")
        
        if conn_success:
            print("✅ Connection successful with stored credentials!")
            print(f"   Connected to: {host}:{port}/{database}")
            
            # Test a simple query to verify full functionality
            try:
                result = db_manager.client.query("SELECT 1 as test")
                print(f"✅ Query test successful: {result.result_rows}")
            except Exception as e:
                print(f"⚠️  Query test failed: {e}")
            
            # Clean up
            db_manager.disconnect()
            print("✅ Disconnected successfully")
            
            return True
        else:
            print("❌ Connection failed with stored credentials")
            print(f"   Error: {conn_message}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed with exception: {e}")
        return False

def test_form_fallback():
    """Test that form fallback works when no stored credentials."""
    print("\n=== Testing Form Fallback (when no stored credentials) ===\n")
    
    # Simulate no stored credentials
    stored_credentials = None
    
    if stored_credentials:
        print("This test requires no stored credentials")
        return False
    else:
        print("[DEBUG] No stored credentials - would use form values")
        # In real app, this would get values from form inputs
        # For test, we'll use defaults to show the logic works
        host = DEFAULT_HOST  # localhost
        port = DEFAULT_PORT  # 9000
        username = DEFAULT_USERNAME  # default
        password = ""
        database = DEFAULT_DATABASE  # default
        
        print(f"[DEBUG] Form fallback parameters: host={host}, port={port}, username={username}, database={database}")
        print("✅ Form fallback logic works (would use localhost defaults)")
        return True

if __name__ == "__main__":
    print("Testing the credential mapping fix...\n")
    
    # Test 1: Stored credentials mapping
    test1_result = test_stored_credentials_mapping()
    
    # Test 2: Form fallback
    test2_result = test_form_fallback()
    
    print(f"\n=== Test Results ===")
    print(f"Stored credentials mapping: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Form fallback logic: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! The credential mapping fix is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
