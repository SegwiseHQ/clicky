#!/usr/bin/env python3
"""Final validation to ensure the UI status indicator fixes are in place."""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_refresh_tables_fix():
    """Check that the refresh_tables method has the fix in place."""
    print("=== Checking refresh_tables Fix ===")
    
    try:
        # Read the ui_components.py file
        with open("ui_components.py", "r") as f:
            content = f.read()
        
        # Check for the fix: refresh_tables should NOT call status_callback with error
        # Look for the specific refresh_tables method
        refresh_method_start = content.find("def refresh_tables(self):")
        if refresh_method_start == -1:
            print("❌ Could not find refresh_tables method")
            return False
        
        # Get the refresh_tables method content (roughly)
        next_method = content.find("\n    def ", refresh_method_start + 1)
        if next_method == -1:
            next_method = len(content)
        
        refresh_method = content[refresh_method_start:next_method]
        
        # Check that refresh_tables does NOT call status_callback with "Not connected" error
        if 'self.status_callback("Not connected' in refresh_method:
            print("❌ BUG: refresh_tables still contains problematic status callback")
            return False
        else:
            print("✅ refresh_tables fix confirmed: no status overwrite")
        
        # Check that refresh_tables handles disconnected state correctly
        if 'add_text("Connect to see tables", parent="tables_list", color=COLOR_INFO)' in content:
            print("✅ refresh_tables correctly shows 'Connect to see tables'")
        else:
            print("❌ refresh_tables missing proper disconnected state handling")
            return False
        
        # Check that refresh_tables shows table count on success
        if 'f"Found {len(tables)} tables"' in content:
            print("✅ refresh_tables shows success message with table count")
        else:
            print("❌ refresh_tables missing success status message")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking refresh_tables fix: {e}")
        return False


def check_app_initialization_fix():
    """Check that the app initialization timing fix is in place."""
    print("\n=== Checking App Initialization Fix ===")
    
    try:
        # Read the app.py file
        with open("app.py", "r") as f:
            content = f.read()
        
        # Find the run method
        run_method_start = content.find("def run(self):")
        if run_method_start == -1:
            print("❌ Could not find run method in app.py")
            return False
        
        # Get the run method content (roughly)
        run_method_end = content.find("\n    def ", run_method_start + 1)
        if run_method_end == -1:
            run_method_end = len(content)
        
        run_method = content[run_method_start:run_method_end]
        
        # Check the order of calls
        setup_ui_pos = run_method.find("self.setup_ui()")
        setup_dearpygui_pos = run_method.find("setup_dearpygui()")
        show_viewport_pos = run_method.find("show_viewport()")
        auto_load_pos = run_method.find("self.auto_load_and_connect()")
        start_dearpygui_pos = run_method.find("start_dearpygui()")
        
        if all(pos != -1 for pos in [setup_ui_pos, setup_dearpygui_pos, show_viewport_pos, auto_load_pos, start_dearpygui_pos]):
            # Check that auto_load_and_connect comes after show_viewport but before start_dearpygui
            if show_viewport_pos < auto_load_pos < start_dearpygui_pos:
                print("✅ App initialization timing fix confirmed")
                print("   Order: setup_ui() → setup_dearpygui() → show_viewport() → auto_load_and_connect() → start_dearpygui()")
                return True
            else:
                print("❌ App initialization order is incorrect")
                print(f"   show_viewport: {show_viewport_pos}, auto_load: {auto_load_pos}, start_dearpygui: {start_dearpygui_pos}")
                return False
        else:
            print("❌ Could not find all required method calls in run()")
            return False
            
    except Exception as e:
        print(f"❌ Error checking app initialization fix: {e}")
        return False


def check_database_connection():
    """Quick check that database connection is working."""
    print("\n=== Checking Database Connection ===")
    
    try:
        from config import (
            DEFAULT_DATABASE,
            DEFAULT_HOST,
            DEFAULT_PORT,
            DEFAULT_USERNAME,
        )
        from credentials_manager import CredentialsManager
        from database import DatabaseManager

        # Load credentials
        creds_manager = CredentialsManager()
        success, credentials, message = creds_manager.load_credentials_legacy()
        
        if not success or not credentials:
            print("❌ No credentials available")
            return False
        
        print(f"✅ Credentials loaded: {credentials['host']}")
        
        # Test connection
        db_manager = DatabaseManager()
        host = credentials.get("host", DEFAULT_HOST)
        port = credentials.get("port", DEFAULT_PORT)
        username = credentials.get("user", DEFAULT_USERNAME)
        password = credentials.get("password", "")
        database = credentials.get("database", DEFAULT_DATABASE)
        
        success, conn_message = db_manager.connect(host, int(port), username, password, database)
        
        if success:
            print(f"✅ Database connection working: {conn_message}")
            tables = db_manager.get_tables()
            print(f"✅ Table listing working: {len(tables)} tables found")
            db_manager.disconnect()
            return True
        else:
            print(f"❌ Database connection failed: {conn_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database connection: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🔍 UI Status Indicator Fix Validation")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check 1: refresh_tables fix
    if not check_refresh_tables_fix():
        all_checks_passed = False
    
    # Check 2: app initialization fix  
    if not check_app_initialization_fix():
        all_checks_passed = False
    
    # Check 3: database connection
    if not check_database_connection():
        all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
        print("✅ UI status indicator fixes are in place and working")
        print("✅ Connection status should now display correctly in the application")
        print("✅ Left panel should show table list instead of 'Connect to see tables'")
    else:
        print("❌ SOME VALIDATION CHECKS FAILED")
        print("   Please review the failed checks above")
    
    return all_checks_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
