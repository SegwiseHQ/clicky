"""Release smoke checks executed from the frozen Clicky application."""

import sys

PLAYGROUND_HOST = "play.clickhouse.com"
PLAYGROUND_PORT = 443
PLAYGROUND_USERNAME = "explorer"
PLAYGROUND_DATABASE = "default"


def run_release_connection_test() -> int:
    """Connect to the public ClickHouse Playground using the packaged TLS stack."""
    from database import DatabaseManager

    database_manager = DatabaseManager()
    try:
        success, message = database_manager.connect(
            host=PLAYGROUND_HOST,
            port=PLAYGROUND_PORT,
            username=PLAYGROUND_USERNAME,
            password="",
            database=PLAYGROUND_DATABASE,
        )
        if not success:
            print(message, file=sys.stderr)
            return 1

        print(message)
        return 0
    finally:
        database_manager.disconnect()
