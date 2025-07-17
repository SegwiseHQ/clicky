#!/usr/bin/env python3
"""
Test script to verify column type functionality
"""
import os
import sys

sys.path.append(os.path.dirname(__file__))

def test_query_parsing():
    """Test query parsing functionality"""
    print("\nTesting query parsing...")

    # Import the QueryInterface to test regex
    from components.query_interface import QueryInterface

    # Create a mock query interface
    class MockDB:
        def get_table_columns(self, table_name):
            # Mock table columns for testing
            if table_name == "users":
                return [("id", "UInt32"), ("name", "String"), ("email", "String")]
            elif table_name == "orders":
                return [("order_id", "UInt64"), ("user_id", "UInt32"), ("total", "Float64")]
            return []

    query_interface = QueryInterface(MockDB(), None, None)

    # Test queries
    test_cases = [
        ("SELECT * FROM users", ["id", "name", "email"], {"id": "UInt32", "name": "String", "email": "String"}),
        ("SELECT id, name FROM users", ["id", "name"], {"id": "UInt32", "name": "String"}),
        ("SELECT order_id FROM orders", ["order_id"], {"order_id": "UInt64"}),
        ("SELECT COUNT(*) FROM users", ["count()"], {}),  # Aggregate functions won't match
    ]

    for query, columns, expected_types in test_cases:
        result_types = query_interface._get_column_types_from_query(query, columns)
        print(f"Query: {query}")
        print(f"  Columns: {columns}")
        print(f"  Expected types: {expected_types}")
        print(f"  Got types: {result_types}")

        # Check if we got the expected results for columns that should match
        success = True
        for col, expected_type in expected_types.items():
            if result_types.get(col) != expected_type:
                success = False
                break

        if success:
            print("  ✓ PASS")
        else:
            print("  ✗ FAIL")

    return True

if __name__ == "__main__":
    print("=== Column Type Enhancement Test ===")

    try:
        test_query_parsing()
        print("\n=== All tests completed ===")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


import os
import sys

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
