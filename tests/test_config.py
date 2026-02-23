"""
Test configuration and utilities for the ClickHouse Client test suite.
"""

import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
