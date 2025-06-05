# Credentials File Permission Fix

## Problem
When the ClickHouse client app was bundled with PyInstaller for macOS distribution, the app bundle becomes read-only, causing credential save operations to fail with permission errors. The app was trying to write `clickhouse_credentials.json` to the application directory, which is not writable in bundled apps.

## Solution
Modified the credentials file location to use the user's home directory instead of the application directory.

### Changes Made

#### 1. Updated `config.py`
```python
# Before
CREDENTIALS_FILE = "clickhouse_credentials.json"

# After  
CREDENTIALS_FILE = os.path.expanduser("~/.clickhouse_credentials.json")
```

#### 2. Enhanced `credentials_manager.py`
- Added directory creation logic in `__init__()` method
- Added proper error handling for `PermissionError` in save/delete operations
- Added fallback mechanism if directory creation fails

### Key Features
- **User-writable location**: Credentials are now saved to `~/.clickhouse_credentials.json`
- **Cross-platform compatibility**: Works on macOS, Windows, and Linux
- **Graceful error handling**: Provides clear error messages for permission issues
- **Automatic directory creation**: Creates parent directories if they don't exist
- **Fallback mechanism**: Falls back to current directory if home directory is not accessible

### Testing
The fix has been thoroughly tested with:
- Normal save/load operations
- Read-only directory scenarios (simulating bundled apps)
- Permission error handling
- Directory creation functionality

### Benefits for Bundled Apps
1. **No more permission errors**: Credentials can be saved successfully
2. **User-specific storage**: Each user has their own credentials file
3. **Persistent across app updates**: Credentials survive app reinstallation
4. **Standard practice**: Follows macOS app sandboxing guidelines

### File Location
- **Development**: `~/.clickhouse_credentials.json`
- **Bundled App**: `~/.clickhouse_credentials.json`
- **Fallback**: `clickhouse_credentials.json` (current directory)

This fix ensures the app works correctly both in development and when distributed as a bundled macOS application.
