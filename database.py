"""Database connection management for ClickHouse Client."""

import traceback
from typing import Optional

import clickhouse_connect

from config import cipher_suite


class DatabaseManager:
    """Manages ClickHouse database connections."""

    def __init__(self):
        self.client: Optional[clickhouse_connect.Client] = None
        self.is_connected = False
        self.connection_info = {}

    def connect(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> tuple[bool, str]:
        """
        Connect to ClickHouse database.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Validate inputs
            if not all([host, str(port), username, database]):
                return False, "All fields except password must be filled"

            # Validate port
            try:
                port = int(port)
            except ValueError:
                return False, f"Port must be a number, got: {port}"

            # Create client
            self.client = clickhouse_connect.get_client(
                host=host,
                username=username,
                password=password,
                database=database,
                secure=True,
            )

            # Test connection
            self.client.query("SELECT 1")

            # Store connection info
            self.connection_info = {
                "host": host,
                "port": port,
                "username": username,
                "database": database,
            }
            self.is_connected = True

            return True, f"Connected successfully to {host}:{port}"

        except Exception as e:
            self.client = None
            self.is_connected = False
            error_msg = "Connection failed:\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += f"Error message: {str(e)}\n"
            error_msg += f"Details:\n{traceback.format_exc()}"
            return False, error_msg

    def disconnect(self) -> str:
        """
        Disconnect from database.

        Returns:
            str: Status message
        """
        if self.client:
            self.client = None
            self.is_connected = False
            self.connection_info = {}
            return "Disconnected from database"
        else:
            return "Not connected to database"

    def execute_query(self, query: str):
        """
        Execute a query and return results.

        Args:
            query: SQL query string

        Returns:
            Query result object or None if error
        """
        if not self.client:
            raise Exception("Not connected to database")

        return self.client.query(query)

    def get_tables(self) -> list[str]:
        """Get list of all tables in the database."""
        if not self.client:
            return []

        try:
            result = self.execute_query("SHOW TABLES")
            return [str(row[0]) for row in result.result_rows]
        except Exception:
            return []

    def get_table_columns(self, table_name: str) -> list[tuple[str, str]]:
        """
        Get column information for a table.

        Args:
            table_name: Name of the table

        Returns:
            List of (column_name, column_type) tuples
        """
        if not self.client:
            return []

        try:
            query = f"DESCRIBE TABLE `{table_name.strip()}`"
            result = self.execute_query(query)

            columns = []
            for row in result.result_rows:
                column_name = str(row[0])
                column_type = str(row[1])
                columns.append((column_name, column_type))

            return columns
        except Exception:
            return []


def encrypt_password(password: str) -> str:
    """Encrypt password for storage."""
    if not password:
        return ""
    return cipher_suite.encrypt(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """Decrypt password from storage."""
    if not encrypted:
        return ""
    try:
        return cipher_suite.decrypt(encrypted.encode()).decode()
    except:
        return ""
