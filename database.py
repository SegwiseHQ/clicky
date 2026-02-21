"""Database connection management for ClickHouse Client."""

import threading
import traceback

import clickhouse_connect

from config import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_QUERY_RETRIES,
    DEFAULT_SEND_RECEIVE_TIMEOUT,
    cipher_suite,
)


class DatabaseManager:
    """Manages ClickHouse database connections.

    clickhouse_connect clients are not thread-safe; all calls are serialised
    with a threading.Lock so that multiple background threads cannot issue
    concurrent requests on the same HTTP connection.
    """

    def __init__(self):
        self.client: clickhouse_connect.Client | None = None
        self.is_connected = False
        self.connection_info = {}
        self._lock = threading.Lock()  # serialise all DB access

    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        send_receive_timeout: int = DEFAULT_SEND_RECEIVE_TIMEOUT,
        query_retries: int = DEFAULT_QUERY_RETRIES,
    ) -> tuple[bool, str]:
        """
        Connect to ClickHouse database.

        Args:
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database: Database name
            connect_timeout: HTTP connection timeout in seconds
            send_receive_timeout: Send/receive timeout in seconds
            query_retries: Maximum number of retries for requests

        Returns:
            tuple: (success: bool, message: str)
        """
        with self._lock:
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
                    port=port,
                    username=username,
                    password=password,
                    database=database,
                    secure=True,
                    connect_timeout=connect_timeout,
                    send_receive_timeout=send_receive_timeout,
                    query_retries=query_retries,
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

    def test_credentials(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        send_receive_timeout: int = DEFAULT_SEND_RECEIVE_TIMEOUT,
        query_retries: int = DEFAULT_QUERY_RETRIES,
    ) -> tuple[bool, str]:
        """
        Test connection credentials without storing the connection.

        Args:
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database: Database name
            connect_timeout: HTTP connection timeout in seconds
            send_receive_timeout: Send/receive timeout in seconds
            query_retries: Maximum number of retries for requests

        Returns:
            tuple: (success: bool, message: str)
        """
        with self._lock:
            try:
                # Validate inputs
                if not all([host, str(port), username, database]):
                    return False, "All fields except password must be filled"

                # Validate port
                try:
                    port = int(port)
                except ValueError:
                    return False, f"Port must be a number, got: {port}"

                # Create temporary client for testing
                test_client = clickhouse_connect.get_client(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    database=database,
                    secure=True,
                    connect_timeout=connect_timeout,
                    send_receive_timeout=send_receive_timeout,
                    query_retries=query_retries,
                )

                # Test connection
                test_client.query("SELECT 1")

                # Close test client (don't store it)
                test_client = None

                return True, f"Credentials are valid for {host}:{port}"

            except Exception as e:
                error_msg = "Credential test failed:\n"
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
        with self._lock:
            if not self.client:
                raise Exception("Not connected to database")
            return self.client.query(query)

    def get_tables(self) -> list[str]:
        """Get list of all tables in the database."""
        with self._lock:
            if not self.client:
                return []
            try:
                result = self.client.query("SHOW TABLES")
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
        with self._lock:
            if not self.client:
                return []
            try:
                query = f"DESCRIBE TABLE `{table_name.strip()}`"
                result = self.client.query(query)
                return [(str(row[0]), str(row[1])) for row in result.result_rows]
            except Exception:
                return []


class ConnectionPool:
    """Per-tab connection pool — one clickhouse_connect.Client per tab, created lazily.

    The lock only guards the _clients dict; actual I/O (get_client, query) happens
    outside the lock so each tab's connection is fully independent.
    """

    def __init__(self):
        self._credentials: dict | None = None
        self._clients: dict[int, object] = {}
        self._lock = threading.Lock()

    def configure(self, credentials: dict | None) -> None:
        """Store (or clear) the credentials used to create new clients."""
        with self._lock:
            self._credentials = credentials

    @property
    def is_configured(self) -> bool:
        return self._credentials is not None

    def get_or_create_client(self, tab_id: int):
        """Return the cached client for tab_id, creating one if needed."""
        with self._lock:
            if tab_id in self._clients:
                return self._clients[tab_id]
            if not self._credentials:
                raise Exception("Connection pool is not configured")
            creds = dict(self._credentials)  # snapshot before releasing lock

        client = clickhouse_connect.get_client(
            host=creds["host"],
            port=int(creds["port"]),
            username=creds["username"],
            password=creds.get("password", ""),
            database=creds["database"],
            secure=True,
            connect_timeout=creds.get("connect_timeout", DEFAULT_CONNECT_TIMEOUT),
            send_receive_timeout=creds.get(
                "send_receive_timeout", DEFAULT_SEND_RECEIVE_TIMEOUT
            ),
            query_retries=creds.get("query_retries", DEFAULT_QUERY_RETRIES),
        )

        with self._lock:
            if tab_id not in self._clients:
                self._clients[tab_id] = client
            return self._clients[tab_id]

    def execute_query(self, tab_id: int, query: str):
        """Execute a query on the client for the given tab."""
        client = self.get_or_create_client(tab_id)
        return client.query(query)

    def release(self, tab_id: int) -> None:
        """Remove the client for a closed tab."""
        with self._lock:
            self._clients.pop(tab_id, None)

    def release_all(self) -> None:
        """Clear all clients (called on disconnect)."""
        with self._lock:
            self._clients.clear()


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
    except Exception:
        return ""
