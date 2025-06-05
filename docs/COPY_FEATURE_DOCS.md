# Data Explorer Copy Functionality

## Overview
The data explorer now includes a click-to-copy feature that allows users to easily copy cell content to the system clipboard by simply clicking on any cell in the data table.

## How It Works

### User Experience
1. **Open Data Explorer**: Double-click any table in the database browser
2. **View Data**: The data explorer displays the table content in a formatted table
3. **Copy Cell Content**: Click on any cell to copy its content to the clipboard
4. **Confirmation**: The status bar shows a confirmation message with a preview of the copied text

### Technical Implementation

#### Key Components

1. **Copy Callback Method** (`_copy_cell_to_clipboard`)
   - Handles the clipboard copy operation
   - Receives cell content through `user_data` parameter
   - Uses `set_clipboard_text()` from DearPyGui
   - Provides user feedback through status callback

2. **Enhanced Selectable Cells**
   ```python
   add_selectable(
       label=cell_value,
       tag=f"cell_{row_idx}_{col_idx}",
       callback=self._copy_cell_to_clipboard,
       user_data=cell_value  # Actual cell content for copying
   )
   ```

3. **Status Feedback**
   - Shows confirmation when text is copied
   - Displays a preview of copied content (truncated if long)
   - Integrates with existing status bar system

#### Data Type Handling

The copy functionality properly handles various data types:

- **Strings**: Copied as-is with proper encoding
- **Numbers**: Converted to string format
- **NULL values**: Displayed and copied as "NULL"
- **Binary data**: Decoded with error handling
- **Special characters**: Properly encoded (Unicode, emojis, etc.)
- **Long text**: Truncated for display but full content copied

#### Error Handling

- **Encoding errors**: Fallback to error message with safe copying
- **Clipboard failures**: Graceful degradation with console logging
- **Missing data**: Handles None/empty values appropriately

## Benefits

1. **Enhanced User Experience**: Quick and easy data copying without manual text selection
2. **System Integration**: Uses native clipboard functionality
3. **Data Preservation**: Maintains original data formatting and encoding
4. **Visual Feedback**: Clear confirmation of copy operations
5. **Robust**: Handles edge cases and various data types

## Usage Examples

### Basic Usage
- Click on cell containing "John Doe" → "John Doe" copied to clipboard
- Click on cell containing "12345" → "12345" copied to clipboard
- Click on cell containing NULL → "NULL" copied to clipboard

### Advanced Usage
- Long text is fully copied even if truncated in display
- Special characters and Unicode content copy correctly
- Error cells (if any) copy their error message for debugging

## Integration

The copy functionality integrates seamlessly with:
- Existing data explorer interface
- Status bar messaging system
- Theme and styling system
- Error handling framework
- Database query results processing

## Files Modified

- `data_explorer.py`: Added copy functionality and enhanced cell creation
- Enhanced existing methods without breaking compatibility
- Maintained all existing functionality while adding new features

## Testing

The feature has been tested with:
- Various data types (strings, numbers, NULL, binary)
- Special characters and Unicode content
- Long text content
- Error conditions
- System clipboard integration
- Status feedback system

## Future Enhancements

Potential improvements could include:
- Right-click context menu for additional copy options
- Copy entire row or column functionality
- Export selected cells to different formats
- Keyboard shortcuts for copy operations
