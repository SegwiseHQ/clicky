"""UI components for ClickHouse Client.

This module provides backward compatibility imports.
The actual implementations have been moved to the components/ package.
"""

# Backward compatibility imports
from components.query_interface import QueryInterface
from components.status_manager import StatusManager
from components.table_browser import TableBrowser

# Re-export for backward compatibility
__all__ = [
    "QueryInterface",
    "StatusManager",
    "TableBrowser",
]
