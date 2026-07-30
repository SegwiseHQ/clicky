#!/usr/bin/env python3
"""
ClickHouse Client - A GUI application for connecting to and querying ClickHouse databases.

This refactored version uses modular architecture for better maintainability:
- config.py: Application configuration and constants
- database.py: Database connection management
- credentials_manager.py: Credentials saving/loading
- ui_components.py: UI components (tables browser, query interface)
- data_explorer.py: Data exploration functionality
- utils.py: Utility functions
- app.py: Main application orchestration
"""

import sys

from app import ClickHouseClientApp
from release_smoke import run_release_connection_test

RELEASE_CONNECTION_TEST_FLAG = "--release-connection-test"


def main():
    """Main entry point for the ClickHouse Client application."""
    app = ClickHouseClientApp()
    app.run()


def cli(args: list[str] | None = None) -> int:
    """Dispatch command-line smoke checks or start the GUI application."""
    args = sys.argv[1:] if args is None else args
    if args == [RELEASE_CONNECTION_TEST_FLAG]:
        return run_release_connection_test()

    main()
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
