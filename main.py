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

from app import ClickHouseClientApp


def main():
    """Main entry point for the ClickHouse Client application."""
    app = ClickHouseClientApp()
    app.run()


if __name__ == "__main__":
    main()
