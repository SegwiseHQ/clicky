"""
Test configuration and utilities for the ClickHouse Client test suite.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_main_tests():
    """Run only the main.py tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("tests.test_main")
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def run_all_tests():
    """Run all tests in the test suite."""
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    # Default to running all tests
    run_all_tests()
