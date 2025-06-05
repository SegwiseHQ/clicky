# Tests Directory

This directory contains all test files for the ClickHouse Client Application, organized for better maintainability and easy execution.

## 📁 Directory Structure

```
tests/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── demo_column_types.py           # Demo script for column type features
├── test_all_fixes.py              # Comprehensive test suite
├── test_column_resizing.py        # Manual column resizing tests ✅
├── test_column_types.py           # Column type display tests
├── test_column_types_simple.py    # Simplified column type tests
├── test_comprehensive_fixes.py    # Full feature integration tests
├── test_copy_functionality.py     # Copy-to-clipboard functionality tests
├── test_credentials_fix.py        # Credential management tests
├── test_data_explorer.py          # Data explorer component tests
├── test_emoji_icons.py            # Emoji icon fallback tests
├── test_font_awesome.py           # Font Awesome icon tests
├── test_icons.py                  # Icon manager tests
├── test_query_copy.py             # Query results copy tests
├── test_resize_fix.py             # Column resize verification tests ✅
├── test_table_extraction.py       # Table name extraction tests
├── test_unicode.py                # Unicode handling tests
└── verify_column_settings.py      # Column settings verification ✅
```

## 🧪 Test Categories

### Column Functionality
- **test_column_resizing.py** - Tests manual column resizing feature
- **test_column_types.py** - Tests column type display functionality
- **test_resize_fix.py** - Verifies column resize fixes are working
- **verify_column_settings.py** - Validates column configuration settings

### Copy Functionality
- **test_copy_functionality.py** - Tests cell data copy-to-clipboard
- **test_query_copy.py** - Tests query results copy features

### UI Components
- **test_data_explorer.py** - Tests data explorer component
- **test_table_extraction.py** - Tests table name extraction logic

### Icon Management
- **test_icons.py** - Tests icon manager functionality
- **test_font_awesome.py** - Tests Font Awesome icon integration
- **test_emoji_icons.py** - Tests emoji icon fallbacks

### Data Handling
- **test_unicode.py** - Tests Unicode character handling
- **test_credentials_fix.py** - Tests credential management

### Integration Tests
- **test_all_fixes.py** - Comprehensive feature testing
- **test_comprehensive_fixes.py** - Full integration test suite

### Demo & Verification
- **demo_column_types.py** - Demonstrates column type features
- **verify_column_settings.py** - Verifies configuration settings

## 🚀 Running Tests

### Individual Tests
```bash
# From project root directory
cd /path/to/clicky

# Run specific tests
python3 tests/test_column_resizing.py
python3 tests/test_icons.py
python3 tests/verify_column_settings.py
```

### Recent Features (Recommended to run)
```bash
# Test column resizing feature (latest enhancement)
python3 tests/test_column_resizing.py
python3 tests/verify_column_settings.py

# Test copy functionality
python3 tests/test_copy_functionality.py

# Test column types display
python3 tests/test_column_types.py
```

### All Tests
```bash
# Run all tests (if pytest is installed)
python3 -m pytest tests/

# Or run manually (from project root)
for test in tests/test_*.py; do python3 "$test"; done
```

## ✅ Recent Enhancements Tested

### Manual Column Resizing (Latest)
- **Files**: `test_column_resizing.py`, `test_resize_fix.py`, `verify_column_settings.py`
- **Status**: ✅ Fully implemented and tested
- **Features**: Drag column borders to resize, increased default widths, resize cursor support

### Copy-to-Clipboard
- **Files**: `test_copy_functionality.py`, `test_query_copy.py`
- **Status**: ✅ Implemented and tested
- **Features**: Click cells to copy data, status feedback

### Column Type Display
- **Files**: `test_column_types.py`, `demo_column_types.py`
- **Status**: ✅ Implemented and tested
- **Features**: Data types shown above column names

## 🔧 Import Path Handling

All test files include automatic path resolution to import project modules:

```python
import sys
import os

# Add parent directory to Python path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

This allows tests to import project modules (e.g., `from icon_manager import icon_manager`) regardless of the working directory.

## 📝 Adding New Tests

1. Create new test file: `tests/test_your_feature.py`
2. Include the path resolution code at the top
3. Import required project modules
4. Write test functions with descriptive names
5. Add documentation to this README

## 🎯 Key Test Results

- **Column Resizing**: ✅ Working - users can drag column borders
- **Copy Functionality**: ✅ Working - click cells to copy data
- **Column Types**: ✅ Working - data types displayed in headers
- **Icon Management**: ✅ Working - icons display correctly
- **Data Explorer**: ✅ Working - table browsing and data viewing

## 🔍 Troubleshooting

If tests fail due to import errors:
1. Ensure you're running from the project root directory
2. Check that all required dependencies are installed: `pip3 install -r requirements.txt`
3. Verify the project structure matches the expected layout

For GUI-related tests that may cause segmentation faults, run them individually rather than in bulk.
