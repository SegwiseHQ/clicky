#!/usr/bin/env python3
"""
Test runner script for the ClickHouse Client application.

This script provides an easy way to run different test suites.
"""

import argparse
import os
import sys
import unittest

# Add the project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def run_main_tests():
    """Run tests for main.py only."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("tests.test_main")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_database_tests():
    """Run tests for database.py only."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("tests.test_database")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_all_tests():
    """Run all tests in the test suite."""
    loader = unittest.TestLoader()
    start_dir = os.path.join(PROJECT_ROOT, "tests")
    suite = loader.discover(start_dir, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_specific_test(test_name):
    """Run a specific test by name."""
    loader = unittest.TestLoader()
    try:
        suite = loader.loadTestsFromName(test_name)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"Error running test '{test_name}': {e}")
        return False


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="ClickHouse Client Test Runner")
    parser.add_argument(
        "target",
        nargs="?",
        choices=["all", "main", "database"],
        default="all",
        help="Which tests to run (default: all)",
    )
    parser.add_argument(
        "--test",
        help="Run a specific test by name (e.g., tests.test_main.TestMain.test_init)",
    )
    parser.add_argument("--list", action="store_true", help="List all available tests")

    args = parser.parse_args()

    if args.list:
        print("Available test modules:")
        print("  main     - Tests for main.py")
        print("  database - Tests for database.py")
        print("  all      - All tests")
        print("\nExample usage:")
        print("  python run_tests.py main")
        print("  python run_tests.py database")
        print("  python run_tests.py all")
        print("  python run_tests.py --test tests.test_main.TestMain.test_init")
        return

    if args.test:
        success = run_specific_test(args.test)
    elif args.target == "main":
        print("Running tests for main.py...")
        success = run_main_tests()
    elif args.target == "database":
        print("Running tests for database.py...")
        success = run_database_tests()
    else:  # 'all'
        print("Running all tests...")
        success = run_all_tests()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
