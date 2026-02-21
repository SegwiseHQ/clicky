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
MAX_QUERY_TABS = 5
MAX_EXPLORER_TABS = 5
DEFAULT_TAB_LABEL = "Query"
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
COLOR_SUCCESS = (34, 197, 94)  # Slightly brighter green
COLOR_ERROR = (220, 53, 69)  # Bootstrap danger red
COLOR_WARNING = (255, 193, 7)  # Bootstrap warning yellow
COLOR_INFO = (23, 162, 184)  # Bootstrap info blue
COLOR_PRIMARY = (99, 102, 241)  # Indigo-500 (modern)

# Table and UI element colors
COLOR_COLUMN = (34, 197, 94)  # Match success green
COLOR_TABLE_HEADER = (20, 20, 24)  # Match surface
COLOR_TABLE_ROW_ALT = (26, 26, 32)  # Very dark stripe (fix: was near-white)
COLOR_CONNECTED = (34, 197, 94)  # Match success green
COLOR_DISCONNECTED = (220, 53, 69)  # Connection indicator red

# Background and text colors
COLOR_BACKGROUND = (13, 13, 15)  # True dark background
COLOR_SURFACE = (20, 20, 24)  # Darker panel surface
COLOR_SURFACE_ELEVATED = (28, 28, 36)  # Inputs, elevated cards
COLOR_TEXT_PRIMARY = (226, 226, 231)  # Slightly warmer white
COLOR_TEXT_SECONDARY = (113, 113, 122)  # More muted secondary text
COLOR_ACCENT = (79, 82, 198)  # Indigo-600 (deeper)

# Button colors - Desaturated palette for better contrast balance
COLOR_BUTTON_PRIMARY = (99, 102, 241)  # Indigo-500 - Connect button
COLOR_BUTTON_SUCCESS = (16, 185, 129)  # #10B981 (emerald-500) - Save As button
COLOR_BUTTON_DANGER = (239, 68, 68)  # #EF4444 (red-500 toned down) - Delete button
COLOR_BUTTON_SECONDARY = (42, 42, 54)  # Dark ghost button

# Special element colors
COLOR_EXPLORER_TITLE = (180, 180, 195)  # Softer header
COLOR_STATUS_BG = (20, 20, 24)  # Match surface (remove dated green banner)
COLOR_BORDER = (37, 37, 46)  # Subtle, near-invisible borders

# Icons and symbols (Font Awesome Unicode)

# Unicode icons - BMP characters, render correctly in JetBrains Mono
SIMPLE_ICONS = {
    "ICON_DATABASE": "●",
    "ICON_TABLE": "≡",
    "ICON_COLUMN": "·",
    "ICON_CONNECT": "◉",
    "ICON_DISCONNECT": "○",
    "ICON_SUCCESS": "✓",
    "ICON_ERROR": "✕",
    "ICON_WARNING": "△",
    "ICON_INFO": "·",
    "ICON_REFRESH": "↻",
    "ICON_SAVE": "↓",
    "ICON_LOAD": "↑",
    "ICON_DELETE": "×",
    "ICON_SEARCH": "⌕",
    "ICON_FILTER": "▿",
    "ICON_EXPORT": "↓",
    "ICON_QUERY": "▶",
    "ICON_EXPLORER": "⊞",
    "ICON_SETTINGS": "⊙",
    "ICON_STATUS_CONNECTED": "●",
    "ICON_STATUS_DISCONNECTED": "○",
    "ICON_ARROW_DOWN": "↓",
    "ICON_ARROW_RIGHT": "›",
    "ICON_LOADING": "…",
}


def get_encryption_key():
    """Generate encryption key from machine-specific data."""
    machine_data = f"{os.getlogin()}{os.getcwd()}"
    return base64.urlsafe_b64encode(hashlib.sha256(machine_data.encode()).digest())


# Initialize encryption
ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)
