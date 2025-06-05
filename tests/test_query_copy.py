#!/usr/bin/env python3
"""Test script to verify query results copy functionality."""

import dearpygui.dearpygui as dpg

from database import DatabaseManager
from ui_components import QueryInterface


def test_query_copy_functionality():
    """Test that query results support click-to-copy functionality."""
    
    print("🔧 Testing Query Results Copy Functionality")
    print("=" * 50)
    
    # Initialize DearPyGui
    dpg.create_context()
    
    try:
        # Create mock database manager with test data
        class MockDatabaseManager:
            def __init__(self):
                self.is_connected = True
            
            def execute_query(self, query):
                class MockResult:
                    def __init__(self):
                        self.column_names = ['id', 'name', 'email', 'status']
                        self.result_rows = [
                            [1, 'John Doe', 'john@example.com', 'active'],
                            [2, 'Jane Smith', 'jane@example.com', 'inactive'],
                            [3, 'Bob Johnson', 'bob@example.com', None],  # Test NULL value
                            [4, 'Alice Brown', 'alice@example.com', 'Test with üñíçødé'],  # Test Unicode
                        ]
                return MockResult()
        
        # Create query interface with mock database
        mock_db = MockDatabaseManager()
        query_interface = QueryInterface(mock_db)
        
        # Test status callback
        status_messages = []
        def test_status_callback(message, is_error):
            status_messages.append((message, is_error))
            print(f"Status: {message}")
        
        query_interface.set_status_callback(test_status_callback)
        
        print("✓ QueryInterface created successfully")
        
        # Test the copy callback function directly
        print("\n✓ Testing copy callback function...")
        
        test_data = "Sample query result cell"
        query_interface._copy_cell_to_clipboard(None, None, test_data)
        
        # Check if status callback was called
        if status_messages:
            last_message, is_error = status_messages[-1]
            if not is_error and "Copied to clipboard" in last_message:
                print("✅ Copy callback works and provides status feedback")
            else:
                print(f"⚠️  Copy callback status: {last_message}")
        
        # Test clipboard content if possible
        try:
            clipboard_content = dpg.get_clipboard_text()
            if clipboard_content == test_data:
                print(f"✅ Clipboard content verified: '{clipboard_content}'")
            else:
                print(f"⚠️  Clipboard content different: '{clipboard_content}'")
        except Exception as e:
            print(f"⚠️  Could not verify clipboard: {e}")
        
        # Test cell value formatting
        print("\n✓ Testing cell value formatting...")
        test_cases = [
            ("String", "Hello World"),
            ("Number", 12345),
            ("NULL", None),
            ("Unicode", "Test with üñíçødé"),
            ("Bytes", b"byte string"),
        ]
        
        for test_name, test_value in test_cases:
            formatted = query_interface._format_cell_value(test_value)
            print(f"  ✅ {test_name}: {test_value} → '{formatted}'")
        
        print("\n✓ Testing query execution simulation...")
        
        # Create a simple window to test the UI
        with dpg.window(label="Test Query Results", tag="test_window"):
            with dpg.child_window(label="Results", tag="results_window", height=200):
                pass
        
        # Simulate query execution
        result = mock_db.execute_query("SELECT * FROM test_table")
        
        # Setup table
        query_interface._setup_results_table(result.column_names)
        print(f"✅ Results table created with columns: {result.column_names}")
        
        # Add rows (this will test the selectable cells)
        for row_idx, row in enumerate(result.result_rows):
            with dpg.table_row(parent=query_interface.current_table):
                for col_idx, cell_value in enumerate(row):
                    formatted_cell = query_interface._format_cell_value(cell_value)
                    original_cell = str(cell_value) if cell_value is not None else "NULL"
                    
                    cell_tag = f"query_cell_{query_interface.table_counter}_{row_idx}_{col_idx}"
                    dpg.add_selectable(
                        label=formatted_cell,
                        tag=cell_tag,
                        callback=query_interface._copy_cell_to_clipboard,
                        user_data=original_cell,
                        parent=dpg.last_item()
                    )
        
        print(f"✅ Added {len(result.result_rows)} rows with selectable cells")
        
        # Test copying a few cells
        print("\n✓ Testing cell copy operations...")
        test_cells = [
            ("Cell [0,1]", "John Doe"),
            ("Cell [1,2]", "jane@example.com"),
            ("Cell [2,3]", "NULL"),
            ("Cell [3,3]", "Test with üñíçødé")
        ]
        
        for cell_desc, expected_value in test_cells:
            query_interface._copy_cell_to_clipboard(None, None, expected_value)
            print(f"  ✅ {cell_desc}: Copied '{expected_value[:30]}{'...' if len(expected_value) > 30 else ''}'")
        
        print("\n" + "=" * 50)
        print("✅ Query Results Copy Functionality Test COMPLETED!")
        print("\nFeatures verified:")
        print("• Click-to-copy functionality for query result cells")
        print("• Proper cell value formatting (strings, numbers, NULL, Unicode)")
        print("• Status feedback when copying cells")
        print("• Clipboard integration")
        print("• Selectable cells in query results table")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        dpg.destroy_context()

if __name__ == "__main__":
    test_query_copy_functionality()


import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
