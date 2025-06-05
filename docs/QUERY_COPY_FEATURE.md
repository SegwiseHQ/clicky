# Query Results Copy Functionality

## Overview
The query results view now includes the same click-to-copy feature as the data explorer, allowing users to easily copy cell content to the system clipboard by simply clicking on any cell in the query results table.

## Problem Solved
Previously, only the data explorer had copy functionality. Users running custom SQL queries couldn't easily copy individual cell values from the results, requiring manual text selection which was cumbersome and error-prone.

## Solution Implemented

### Technical Changes

#### 1. Added Copy Callback Method
```python
def _copy_cell_to_clipboard(self, sender, app_data, user_data):
    """Copy cell content to clipboard when clicked."""
    try:
        cell_text = user_data if user_data else ""
        set_clipboard_text(cell_text)
        
        if self.status_callback:
            preview = cell_text[:50] + "..." if len(cell_text) > 50 else cell_text
            self.status_callback(f"Copied to clipboard: {preview}", False)
    except Exception as e:
        if self.status_callback:
            self.status_callback(f"Error copying to clipboard: {str(e)}", True)
```

#### 2. Added Cell Value Formatting
```python
def _format_cell_value(self, val) -> str:
    """Format a cell value for display."""
    if val is None:
        return "NULL"
    elif isinstance(val, bytes):
        try:
            cell_value = val.decode('utf-8', errors='replace')
        except:
            cell_value = str(val)
    elif isinstance(val, str):
        try:
            cell_value = val.encode('utf-8', errors='replace').decode('utf-8')
        except:
            cell_value = str(val)
    else:
        cell_value = str(val)
    
    return cell_value
```

#### 3. Changed Cell Creation to Use Selectable Elements
**Before:**
```python
for cell_value in string_row:
    add_text(cell_value)
```

**After:**
```python
for col_idx, cell_value in enumerate(row):
    formatted_cell = self._format_cell_value(cell_value)
    original_cell = str(cell_value) if cell_value is not None else "NULL"
    
    cell_tag = f"query_cell_{self.table_counter}_{row_idx}_{col_idx}"
    add_selectable(
        label=formatted_cell,
        tag=cell_tag,
        callback=self._copy_cell_to_clipboard,
        user_data=original_cell
    )
```

## Features

### User Experience
- **One-click copying**: Click any cell in query results to copy its content
- **Visual feedback**: Status bar shows confirmation with preview of copied text
- **Data preservation**: Original data format maintained during copy operation
- **Type handling**: Properly handles strings, numbers, NULL values, Unicode, and binary data

### Data Type Support
- **Strings**: Copied as-is with proper UTF-8 encoding
- **Numbers**: Converted to string format for clipboard
- **NULL values**: Displayed and copied as "NULL"
- **Unicode content**: Properly encoded (emojis, international characters, etc.)
- **Binary data**: Decoded to UTF-8 with error handling
- **Special characters**: Safely handled with fallback encoding

### Error Handling
- **Encoding errors**: Graceful fallback with safe string conversion
- **Clipboard failures**: Error messages displayed in status bar
- **Missing data**: NULL/empty values handled appropriately
- **Exception handling**: Robust error handling prevents crashes

## Integration

### Consistent with Data Explorer
The query results copy functionality is implemented identically to the data explorer:
- Same callback method signature
- Same status feedback system
- Same data formatting logic
- Same error handling approach

### Status Bar Integration
- Success messages show copied content preview
- Error messages display if copy operation fails
- Consistent with existing status feedback patterns

### Theme Integration
- Uses existing selectable element themes
- Maintains visual consistency with rest of application
- Respects user's theme preferences

## Testing

Comprehensive testing has been performed:
- ✅ Basic copy operations
- ✅ Various data types (string, number, NULL, Unicode, binary)
- ✅ Status feedback verification
- ✅ Clipboard integration testing
- ✅ Error condition handling
- ✅ Integration with existing query functionality

## Usage Examples

### Basic Usage
1. **Run a SQL query**: Enter your query and click "Run Query"
2. **View results**: Query results appear in the results table
3. **Copy cell data**: Click on any cell to copy its content to clipboard
4. **Confirmation**: Status bar shows "Copied to clipboard: [preview]"

### Example Scenarios
- Copy email addresses from query results for external use
- Copy numeric IDs for use in other queries
- Copy text content for documentation or reporting
- Copy NULL values for data validation purposes

## File Modified
- **`ui_components.py`**: Enhanced `QueryInterface` class with copy functionality

## Benefits
1. **Improved workflow**: No more manual text selection
2. **Consistent UX**: Same behavior as data explorer
3. **Data accuracy**: Original data preserved during copy
4. **User feedback**: Clear confirmation of copy operations
5. **Robust handling**: Supports all ClickHouse data types

This enhancement brings the query results view to feature parity with the data explorer, providing a seamless and consistent user experience throughout the application.
