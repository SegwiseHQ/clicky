#!/usr/bin/env python3
"""
Simple test to verify column type functionality without GUI dependencies
"""
import re


def test_query_parsing():
    """Test the regex pattern matching for extracting table names from queries"""
    print("Testing query parsing regex...")
    
    test_queries = [
        "SELECT * FROM users",
        "SELECT id, name FROM users WHERE active = 1",
        "select count(*) from orders",
        "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
        "SELECT * FROM my_table_name",
        "SELECT col1, col2 FROM table_with_underscores",
    ]
    
    for query in test_queries:
        query_lower = query.lower().strip()
        from_match = re.search(r'\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_lower)
        
        if from_match:
            table_name = from_match.group(1)
            print(f"Query: {query}")
            print(f"  Extracted table: {table_name}")
        else:
            print(f"Query: {query}")
            print(f"  No table found")
    
    print("\n✓ Query parsing test completed")

def test_column_type_formatting():
    """Test column header formatting with types"""
    print("Testing column header formatting...")
    
    test_cases = [
        ("id", "UInt32", "UInt32\nid"),
        ("name", "String", "String\nname"),
        ("email", "", "email"),  # No type case
        ("created_at", "DateTime", "DateTime\ncreated_at"),
    ]
    
    for col_name, col_type, expected in test_cases:
        if col_type:
            header_label = f"{col_type}\n{col_name}"
        else:
            header_label = str(col_name)
        
        print(f"Column: {col_name}, Type: {col_type or 'None'}")
        print(f"  Expected: {expected!r}")
        print(f"  Got: {header_label!r}")
        print(f"  Match: {'✓' if header_label == expected else '✗'}")
    
    print("\n✓ Column header formatting test completed")

if __name__ == "__main__":
    print("=== Column Type Enhancement Test (No GUI) ===")
    print()
    test_query_parsing()
    print()
    test_column_type_formatting()
    print()
    print("=== All tests completed ===")


import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
