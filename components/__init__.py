"""Components package for ClickHouse Client."""

from .query_interface import TabbedQueryInterface
from .status_manager import StatusManager

__all__ = [
    "TabbedQueryInterface",
    "StatusManager",
]
