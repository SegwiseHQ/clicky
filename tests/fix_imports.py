#!/usr/bin/env python3
"""Fix imports in test files after moving them to tests/ directory."""

import os
import re
import sys


def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    print(f"Fixing imports in {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to match imports that need sys.path modification
    needs_syspath = False
    
    # Check for imports that need fixing
    import_patterns = [
        r'from app import',
        r'import app',
        r'from config import',
        r'import config',
        r'from database import',
        r'import database',
        r'from credentials_manager import',
        r'import credentials_manager',
        r'from ui_components import',
        r'import ui_components',
        r'from utils import',
        r'import utils',
        r'from theme_manager import',
        r'import theme_manager',
        r'from data_explorer import',
        r'import data_explorer',
        r'from icon_manager import',
        r'import icon_manager',
    ]
    
    for pattern in import_patterns:
        if re.search(pattern, content):
            needs_syspath = True
            break
    
    if needs_syspath and 'sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))' not in content:
        # Add sys.path modification at the top
        lines = content.split('\n')
        
        # Find the first import or after shebang/docstring
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('#!/usr/bin/env python3'):
                insert_index = i + 1
            elif line.startswith('"""') and insert_index == 0:
                # Find end of docstring
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().endswith('"""'):
                        insert_index = j + 1
                        break
            elif line.startswith('import ') or line.startswith('from '):
                insert_index = i
                break
        
        # Insert sys.path modification
        syspath_lines = [
            '',
            'import os',
            'import sys',
            'sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))',
            ''
        ]
        
        # Check if import os and sys already exist
        if 'import os' in content:
            syspath_lines.remove('import os')
        if 'import sys' in content:
            syspath_lines.remove('import sys')
        
        for j, syspath_line in enumerate(syspath_lines):
            lines.insert(insert_index + j, syspath_line)
        
        content = '\n'.join(lines)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"  ✓ Added sys.path modification to {filepath}")
    else:
        print(f"  - No changes needed for {filepath}")

def main():
    """Fix imports in all test files."""
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in os.listdir(tests_dir):
        if filename.endswith('.py') and filename != 'fix_imports.py' and filename != '__init__.py':
            filepath = os.path.join(tests_dir, filename)
            fix_imports_in_file(filepath)
    
    print("\n✓ Import fixing complete!")

if __name__ == "__main__":
    main()
