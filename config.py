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

# Connection timeout settings (in seconds)
DEFAULT_CONNECT_TIMEOUT = 5  # HTTP connection timeout
DEFAULT_SEND_RECEIVE_TIMEOUT = 30  # Send/receive timeout
DEFAULT_QUERY_RETRIES = 2  # Maximum number of retries for requests

# UI constants
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 768
TABLES_PANEL_WIDTH = 350
QUERY_INPUT_HEIGHT = 150
TABLE_ROW_HEIGHT = 25
TABLE_BUTTON_HEIGHT = 30

# Data Explorer panel settings

# Colors (RGB tuples) - Enhanced color palette
COLOR_SUCCESS = (40, 167, 69)  # Bootstrap success green
COLOR_ERROR = (220, 53, 69)  # Bootstrap danger red
COLOR_WARNING = (255, 193, 7)  # Bootstrap warning yellow
COLOR_INFO = (23, 162, 184)  # Bootstrap info blue
COLOR_PRIMARY = (0, 123, 255)  # Bootstrap primary blue

# Table and UI element colors
COLOR_COLUMN = (40, 167, 69)  # Green for column names
COLOR_TABLE_HEADER = (33, 37, 41)  # Dark header background
COLOR_TABLE_ROW_ALT = (248, 249, 250)  # Alternating row color
COLOR_CONNECTED = (40, 167, 69)  # Connection indicator green
COLOR_DISCONNECTED = (220, 53, 69)  # Connection indicator red

# Background and text colors
COLOR_BACKGROUND = (32, 32, 32)  # Dark gray background
COLOR_SURFACE = (48, 48, 48)  # Slightly lighter surface
COLOR_TEXT_PRIMARY = (237, 242, 247)  # Light text
COLOR_TEXT_SECONDARY = (160, 174, 192)  # Muted text
COLOR_ACCENT = (70, 130, 180)  # Darker blue accent color

# Button colors - Desaturated palette for better contrast balance
COLOR_BUTTON_PRIMARY = (59, 130, 246)  # #3B82F6 (blue-500) - Connect button
COLOR_BUTTON_SUCCESS = (16, 185, 129)  # #10B981 (emerald-500) - Save As button
COLOR_BUTTON_DANGER = (239, 68, 68)  # #EF4444 (red-500 toned down) - Delete button
COLOR_BUTTON_SECONDARY = (
    107,
    114,
    128,
)  # #6B7280 (gray-500) - Disconnect/secondary buttons

# Special element colors
COLOR_EXPLORER_TITLE = (220, 220, 220)  # Light gray title text
COLOR_STATUS_BG = (25, 77, 51)  # Dark green status banner background
COLOR_BORDER = (74, 85, 104)  # Border color

# Icons and symbols (Font Awesome Unicode)

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
    "ICON_LOADING": "[...]",
}


def get_encryption_key():
    """Generate encryption key from machine-specific data."""
    machine_data = f"{os.getlogin()}{os.getcwd()}"
    return base64.urlsafe_b64encode(hashlib.sha256(machine_data.encode()).digest())


# Initialize encryption
ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)
