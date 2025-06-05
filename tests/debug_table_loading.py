#!/usr/bin/env python3
"""Debug table loading issue."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from credentials_manager import CredentialsManager

# Test table loading without UI
from database import DatabaseManager


def test_table_loading():
    """Test table loading logic directly."""
    print("=== Testing Table Loading Logic ===")
    
    # Initialize components
    db_manager = DatabaseManager()
    creds_manager = CredentialsManager()
    
    # Load credentials
    success, credentials, message = creds_manager.load_credentials_legacy()
    print(f"Load credentials: success={success}, message={message}")
    
    if success and credentials:
        print(f"Credentials: {credentials}")
        
        # Connect to database
        connect_success, connect_msg = db_manager.connect(
            credentials['host'],
            int(credentials['port']),
            credentials['user'],
            credentials['password'],
            credentials['database']
        )
        
        print(f"Connect result: success={connect_success}, message={connect_msg}")
        
        if connect_success:
            # Test table retrieval
            tables = db_manager.get_tables()
            print(f"Tables found: {len(tables)}")
            print(f"First 10 tables: {tables[:10]}")
            
            # Test if connection state is correct
            print(f"Is connected: {db_manager.is_connected}")
            
        else:
            print("Connection failed, cannot test table loading")
    else:
        print("No credentials found, cannot test")

if __name__ == "__main__":
    test_table_loading()
