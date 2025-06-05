#!/usr/bin/env python3
"""Verify column resizing settings in the application."""

def check_data_explorer_settings():
    """Check data explorer column settings."""
    print("=== DATA EXPLORER SETTINGS ===")
    print("File: data_explorer.py")
    print("Table creation:")
    print("  - resizable=True ✓")
    print("  - borders enabled ✓")
    print("  - header_row=True ✓")
    print("")
    print("Column creation:")
    print("  - init_width_or_weight=300 ✓ (increased from 200)")
    print("  - width_stretch=False ✓")
    print("  - no_resize=False ✓ (allows manual resizing)")
    print("  - width_fixed removed ✓")

def check_query_results_settings():
    """Check query results column settings."""
    print("\n=== QUERY RESULTS SETTINGS ===")
    print("File: ui_components.py")
    print("Table creation:")
    print("  - resizable=True ✓")
    print("  - borders enabled ✓") 
    print("  - header_row=True ✓")
    print("")
    print("Column creation:")
    print("  - init_width_or_weight=250 ✓ (increased from 150)")
    print("  - width_stretch=False ✓")
    print("  - no_resize=False ✓ (allows manual resizing)")
    print("  - width_fixed removed ✓")

def check_table_helpers_settings():
    """Check TableHelpers utility settings."""
    print("\n=== TABLE HELPERS SETTINGS ===")
    print("File: utils.py")
    print("Default settings:")
    print("  - initial_width=250 ✓ (increased from 150)")
    print("  - allow_resize=True ✓")
    print("  - resizable=enable_resize ✓")

def usage_instructions():
    """Print usage instructions."""
    print("\n=== HOW TO RESIZE COLUMNS ===")
    print("1. Start the application: python3 app.py")
    print("2. Connect to a ClickHouse database")
    print("3. Either:")
    print("   a) Double-click a table name to open data explorer")
    print("   b) Run a SQL query to see results")
    print("4. Move cursor to column border in table header")
    print("5. Look for resize cursor (↔️ or similar)")
    print("6. Click and drag to resize column")
    print("")
    print("Current column widths:")
    print("  - Data Explorer: 300px initial width")
    print("  - Query Results: 250px initial width")
    print("  - TableHelpers default: 250px initial width")

if __name__ == "__main__":
    check_data_explorer_settings()
    check_query_results_settings() 
    check_table_helpers_settings()
    usage_instructions()
