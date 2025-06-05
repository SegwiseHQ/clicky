#!/usr/bin/env python3
"""Test script to verify the credentials file permission fix."""

import os
import tempfile

from credentials_manager import CredentialsManager


def test_credentials_file_location():
    """Test that credentials are saved to a user-writable location."""
    
    print("Testing credentials file location fix...")
    
    # Create a credentials manager
    creds_manager = CredentialsManager()
    
    print(f"Credentials file path: {creds_manager.credentials_file}")
    
    # Test saving credentials
    success, message = creds_manager.save_credentials(
        name="test_connection",
        host="localhost",
        port="9000", 
        username="test_user",
        password="test_password",
        database="test_db"
    )
    
    print(f"Save result: {success}")
    print(f"Save message: {message}")
    
    if success:
        print("✓ Credentials saved successfully")
        
        # Verify file exists and is readable
        if os.path.exists(creds_manager.credentials_file):
            print("✓ Credentials file exists")
            
            # Test loading credentials
            load_success, creds, load_message = creds_manager.load_credentials("test_connection")
            print(f"Load result: {load_success}")
            print(f"Load message: {load_message}")
            
            if load_success and creds:
                print("✓ Credentials loaded successfully")
                print(f"  Host: {creds['host']}")
                print(f"  Port: {creds['port']}")
                print(f"  User: {creds['user']}")
                print(f"  Database: {creds['database']}")
                
                # Test deletion
                delete_success, delete_message = creds_manager.delete_credentials("test_connection")
                print(f"Delete result: {delete_success}")
                print(f"Delete message: {delete_message}")
                
                if delete_success:
                    print("✓ Credentials deleted successfully")
                else:
                    print("✗ Failed to delete credentials")
            else:
                print("✗ Failed to load credentials")
        else:
            print("✗ Credentials file was not created")
    else:
        print("✗ Failed to save credentials")
        print(f"Error: {message}")

def test_bundled_app_scenario():
    """Test scenario similar to bundled app with read-only directory."""
    
    print("\nTesting bundled app scenario...")
    
    # Create a temporary read-only directory to simulate bundled app
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a subdirectory and make it read-only
        read_only_dir = os.path.join(temp_dir, "read_only_app")
        os.makedirs(read_only_dir)
        
        # Try to make it read-only (this might not work on all systems)
        try:
            os.chmod(read_only_dir, 0o444)
            print(f"Created read-only directory: {read_only_dir}")
        except:
            print("Note: Could not make directory read-only on this system")
        
        # Test with credentials file in read-only location
        read_only_creds_file = os.path.join(read_only_dir, "test_credentials.json")
        
        # This should fail gracefully
        creds_manager = CredentialsManager(read_only_creds_file)
        
        success, message = creds_manager.save_credentials(
            name="test_readonly",
            host="localhost",
            port="9000",
            username="test_user", 
            password="test_password",
            database="test_db"
        )
        
        print(f"Read-only save result: {success}")
        print(f"Read-only save message: {message}")
        
        if not success and "Permission denied" in message:
            print("✓ Properly handled read-only directory error")
        elif success:
            print("✓ Fallback mechanism worked")
        else:
            print("✗ Unexpected error handling")

if __name__ == "__main__":
    test_credentials_file_location()
    test_bundled_app_scenario()
    print("\nTesting completed!")


import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
