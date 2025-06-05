#!/usr/bin/env python3
"""Debug script to check connection status timing."""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_DATABASE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME
from credentials_manager import CredentialsManager
from database import DatabaseManager


def debug_connection_status():
    """Debug connection status and timing."""
    print("=== Debugging Connection Status ===")
    
    # Load credentials
    creds_manager = CredentialsManager()
    success, credentials, message = creds_manager.load_credentials_legacy()
    
    if not success or not credentials:
        print("❌ No credentials available")
        return
    
    print(f"Credentials loaded: {credentials}")
    
    # Test connection
    db_manager = DatabaseManager()
    
    print(f"Before connect: is_connected = {db_manager.is_connected}")
    
    # Connect
    host = credentials.get("host", DEFAULT_HOST)
    port = credentials.get("port", DEFAULT_PORT)
    username = credentials.get("user", DEFAULT_USERNAME)
    password = credentials.get("password", "")
    database = credentials.get("database", DEFAULT_DATABASE)
    
    success, conn_message = db_manager.connect(host, int(port), username, password, database)
    
    print(f"Connect result: success={success}")
    print(f"Connect message: {conn_message}")
    print(f"After connect: is_connected = {db_manager.is_connected}")
    
    if success:
        # Test the scenario that happens in refresh_tables
        print("\n--- Testing refresh_tables scenario ---")
        
        # This is exactly what happens in refresh_tables()
        if not db_manager.is_connected:
            print("❌ BUG: db_manager.is_connected is False even after successful connection!")
        else:
            print("✅ db_manager.is_connected is True as expected")
            
        # Test getting tables
        try:
            tables = db_manager.get_tables()
            print(f"✅ get_tables() works: {len(tables)} tables found")
        except Exception as e:
            print(f"❌ get_tables() failed: {e}")
    
    # Clean up
    db_manager.disconnect()
    print(f"After disconnect: is_connected = {db_manager.is_connected}")

if __name__ == "__main__":
    debug_connection_status()
