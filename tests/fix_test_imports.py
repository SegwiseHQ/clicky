#!/usr/bin/env python3
"""Fix import paths in test files after moving to tests/ directory."""

import os
import re
import sys


def fix_imports_in_file(filepath):
    """Fix import statements in a test file."""
    print(f"Fixing imports in {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Add sys.path modification at the top if needed
    if 'sys.path' not in content and ('from ' in content or 'import ' in content):
        # Find the position after the shebang and docstring
        lines = content.split('\n')
        insert_pos = 0
        
        # Skip shebang
        if lines[0].startswith('#!'):
            insert_pos = 1
            
        # Skip docstring
        if insert_pos < len(lines) and lines[insert_pos].strip().startswith('"""'):
            # Find end of docstring
            in_docstring = True
            insert_pos += 1
            while insert_pos < len(lines) and in_docstring:
                if '"""' in lines[insert_pos]:
                    insert_pos += 1
                    break
                insert_pos += 1
        
        # Insert sys.path modification
        path_fix = """
import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
        
        lines.insert(insert_pos, path_fix.strip())
        content = '\n'.join(lines)
    
    # Write back the modified content
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Updated {filepath}")
    else:
        print(f"  - No changes needed for {filepath}")

def main():
    """Fix imports in all test files."""
    tests_dir = '/Users/shobhit/Documents/workspace/python/clicky/tests'
    
    print("=== FIXING IMPORT PATHS IN TEST FILES ===")
    print("Adding sys.path modifications to access parent directory modules...")
    print()
    
    # Process all Python files in tests directory
    for filename in os.listdir(tests_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(tests_dir, filename)
            fix_imports_in_file(filepath)
    
    print()
    print("✅ Import path fixes completed!")
    print()
    print("Now you can run tests from the project root with:")
    print("  python3 tests/test_icons.py")
    print("  python3 tests/test_column_resizing.py")
    print("  etc.")

if __name__ == "__main__":
    main()
