#!/usr/bin/env python3
"""Test script to verify credential mapping fix."""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from credentials_manager import CredentialsManager
from database import DatabaseManager


def test_credential_loading():
    """Test that credentials are loaded and can be used for connection."""
    print("Testing credential loading and mapping...")
    
    # Initialize credentials manager
    creds_manager = CredentialsManager()
    
    # Load default credentials
    success, credentials, message = creds_manager.load_credentials_legacy()
    print(f"Load result: {success}")
    print(f"Message: {message}")
    
    if success and credentials:
        print(f"Loaded credentials:")
        print(f"  Host: {credentials['host']}")
        print(f"  Port: {credentials['port']}")
        print(f"  User: {credentials['user']}")
        print(f"  Database: {credentials['database']}")
        print(f"  Password: {'*' * len(credentials['password']) if credentials['password'] else 'None'}")
        
        # Test connection with loaded credentials
        print("\nTesting connection with loaded credentials...")
        db_manager = DatabaseManager()
        
        try:
            success, conn_message = db_manager.connect(
                host=credentials['host'],
                port=int(credentials['port']),
                username=credentials['user'],
                password=credentials['password'],
                database=credentials['database']
            )
            
            print(f"Connection result: {success}")
            print(f"Connection message: {conn_message}")
            
            if success:
                print("✅ Credential mapping fix working correctly!")
                
                # Test a simple query
                try:
                    result = db_manager.client.query("SELECT 1 as test")
                    print(f"Test query result: {result.result_rows}")
                    print("✅ Connection is fully functional!")
                except Exception as e:
                    print(f"⚠️  Query test failed: {e}")
                
                # Disconnect
                db_manager.disconnect()
            else:
                print("❌ Connection failed with loaded credentials")
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            
    else:
        print("❌ Failed to load credentials")

if __name__ == "__main__":
    test_credential_loading()
