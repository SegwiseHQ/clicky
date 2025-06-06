"""Configuration and constants for the ClickHouse Client."""

import base64
import hashlib
import os

from cryptography.fernet import Fernet

# Application constants
# Use user's home directory for credentials file to support bundled apps
CREDENTIALS_FILE = os.path.expanduser("~/.clickhouse_credentials.json")
DEFAULT_HOST = "localhost"
DEFAULT_PORT = "9000"
DEFAULT_USERNAME = "default"
DEFAULT_DATABASE = "default"
MAX_ROWS_LIMIT = 1000
DEFAULT_LIMIT = 100
DOUBLE_CLICK_THRESHOLD = 0.5
MAX_CELL_LENGTH = 300

# UI constants
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 768
TABLES_PANEL_WIDTH = 350
STATUS_WINDOW_HEIGHT = 80
QUERY_INPUT_HEIGHT = 150
TABLE_ROW_HEIGHT = 25
TABLE_BUTTON_HEIGHT = 30
COLUMN_WIDTH = 400  # Updated to match data explorer width
RESULTS_COLUMN_WIDTH = 350  # Updated to match query results width

# Data Explorer panel settings
ROW_DETAILS_PANEL_WIDTH = 400  # Width of the row details panel on the right
ROW_DETAILS_PANEL_MIN_WIDTH = 250  # Minimum width for the row details panel
ROW_DETAILS_PANEL_MAX_WIDTH = 600  # Maximum width for the row details panel

# Colors (RGB tuples) - Enhanced color palette
COLOR_SUCCESS = (40, 167, 69)        # Bootstrap success green
COLOR_ERROR = (220, 53, 69)          # Bootstrap danger red  
COLOR_WARNING = (255, 193, 7)        # Bootstrap warning yellow
COLOR_INFO = (23, 162, 184)          # Bootstrap info blue
COLOR_PRIMARY = (0, 123, 255)        # Bootstrap primary blue
COLOR_SECONDARY = (108, 117, 125)    # Bootstrap secondary gray
COLOR_DARK = (52, 58, 64)            # Bootstrap dark gray
COLOR_LIGHT = (248, 249, 250)        # Bootstrap light gray

# Table and UI element colors
COLOR_COLUMN = (40, 167, 69)         # Green for column names
COLOR_TABLE_HEADER = (33, 37, 41)    # Dark header background
COLOR_TABLE_ROW_ALT = (248, 249, 250) # Alternating row color
COLOR_CONNECTED = (40, 167, 69)      # Connection indicator green
COLOR_DISCONNECTED = (220, 53, 69)   # Connection indicator red

# Background and text colors
COLOR_BACKGROUND = (26, 32, 44)      # Dark blue-gray background
COLOR_SURFACE = (45, 55, 72)         # Slightly lighter surface
COLOR_TEXT_PRIMARY = (237, 242, 247) # Light text
COLOR_TEXT_SECONDARY = (160, 174, 192) # Muted text
COLOR_ACCENT = (66, 153, 225)        # Blue accent color

# Button colors
COLOR_BUTTON_PRIMARY = (66, 153, 225) # Primary button
COLOR_BUTTON_SUCCESS = (40, 167, 69)  # Success button  
COLOR_BUTTON_DANGER = (220, 53, 69)   # Danger button
COLOR_BUTTON_SECONDARY = (74, 85, 104) # Secondary button

# Special element colors
COLOR_EXPLORER_TITLE = (255, 193, 7)  # Explorer title yellow
COLOR_STATUS_BG = (45, 55, 72)        # Status background
COLOR_BORDER = (74, 85, 104)          # Border color

# Icons and symbols (Font Awesome Unicode)
ICON_DATABASE = "\uf1c0"      # fa-database
ICON_TABLE = "\uf0ce"         # fa-table
ICON_COLUMN = "\uf0db"        # fa-columns
ICON_CONNECT = "\uf0c1"       # fa-link
ICON_DISCONNECT = "\uf127"    # fa-unlink
ICON_SUCCESS = "\uf00c"       # fa-check
ICON_ERROR = "\uf00d"         # fa-times
ICON_WARNING = "\uf071"       # fa-exclamation-triangle
ICON_INFO = "\uf05a"          # fa-info-circle
ICON_REFRESH = "\uf021"       # fa-refresh
ICON_SAVE = "\uf0c7"          # fa-save
ICON_LOAD = "\uf07c"          # fa-folder-open
ICON_DELETE = "\uf1f8"        # fa-trash
ICON_SEARCH = "\uf002"        # fa-search
ICON_FILTER = "\uf0b0"        # fa-filter
ICON_EXPORT = "\uf019"        # fa-download
ICON_QUERY = "\uf1c9"         # fa-code
ICON_EXPLORER = "\uf067"      # fa-plus
ICON_SETTINGS = "\uf013"      # fa-cog
ICON_STATUS_CONNECTED = "\uf111"     # fa-circle
ICON_STATUS_DISCONNECTED = "\uf10c" # fa-circle-o
ICON_ARROW_DOWN = "\uf078"    # fa-chevron-down
ICON_ARROW_RIGHT = "\uf054"   # fa-chevron-right
ICON_LOADING = "\uf110"       # fa-spinner

# Simple bracketed text icons - reliable across all systems
SIMPLE_ICONS = {
    "ICON_DATABASE": "[DB]",
    "ICON_TABLE": "[T]",
    "ICON_COLUMN": "[C]",
    "ICON_CONNECT": "[C]",
    "ICON_DISCONNECT": "[D]",
    "ICON_SUCCESS": "[OK]",
    "ICON_ERROR": "[ERR]",
    "ICON_WARNING": "[WARN]",
    "ICON_INFO": "[INFO]",
    "ICON_REFRESH": "[R]",
    "ICON_SAVE": "[S]",
    "ICON_LOAD": "[L]",
    "ICON_DELETE": "[DEL]",
    "ICON_SEARCH": "[SEARCH]",
    "ICON_FILTER": "[FILTER]",
    "ICON_EXPORT": "[EXPORT]",
    "ICON_QUERY": "[Q]",
    "ICON_EXPLORER": "[EXPLORE]",
    "ICON_SETTINGS": "[SET]",
    "ICON_STATUS_CONNECTED": "[ONLINE]",
    "ICON_STATUS_DISCONNECTED": "[OFFLINE]",
    "ICON_ARROW_DOWN": "[v]",
    "ICON_ARROW_RIGHT": "[>]",
    "ICON_LOADING": "[...]"
}

def get_encryption_key():
    """Generate encryption key from machine-specific data."""
    machine_data = f"{os.getlogin()}{os.getcwd()}"
    return base64.urlsafe_b64encode(hashlib.sha256(machine_data.encode()).digest())

# Initialize encryption
ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)
