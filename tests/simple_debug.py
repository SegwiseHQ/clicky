#!/usr/bin/env python3
"""Simple debug test for table loading."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from credentials_manager import CredentialsManager
from database import DatabaseManager

print("=== Simple Table Loading Test ===")

# Test 1: Basic database connection
db_manager = DatabaseManager()
creds_manager = CredentialsManager()

print("1. Loading credentials...")
success, credentials, message = creds_manager.load_credentials_legacy()
print(f"   Result: success={success}, message='{message}'")

if success and credentials:
    print(f"   Credentials loaded: host={credentials.get('host')}, port={credentials.get('port')}, user={credentials.get('user')}, database={credentials.get('database')}")
    
    print("2. Connecting to database...")
    connect_success, connect_msg = db_manager.connect(
        credentials['host'],
        int(credentials['port']),
        credentials['user'],
        credentials['password'],
        credentials['database']
    )
    print(f"   Result: success={connect_success}, message='{connect_msg}'")
    
    if connect_success:
        print("3. Checking connection status...")
        print(f"   Is connected: {db_manager.is_connected}")
        
        print("4. Getting tables...")
        try:
            tables = db_manager.get_tables()
            print(f"   Found {len(tables)} tables")
            if len(tables) > 0:
                print(f"   First 5 tables: {tables[:5]}")
            else:
                print("   No tables found!")
        except Exception as e:
            print(f"   Error getting tables: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("   Cannot test table loading - connection failed")
else:
    print("   Cannot test table loading - no credentials")

print("\n=== Test Complete ===")
