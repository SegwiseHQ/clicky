"""Database connection management for ClickHouse Client."""

import re
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
            new_client = None
            previous_client = None
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
                previous_client = self.client
                new_client = clickhouse_connect.get_client(
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
                new_client.query("SELECT 1")

                # Store connection info
                self.client = new_client
                self.connection_info = {
                    "host": host,
                    "port": port,
                    "username": username,
                    "database": database,
                }
                self.is_connected = True
                if previous_client is not None and previous_client is not new_client:
                    self._close_client(previous_client)

                return True, f"Connected successfully to {host}:{port}"

            except Exception as e:
                self._close_client(new_client)
                if previous_client is not new_client:
                    self._close_client(previous_client)
                self.client = None
                self.is_connected = False
                self.connection_info = {}
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
            test_client = None
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

                return True, f"Credentials are valid for {host}:{port}"

            except Exception as e:
                error_msg = "Credential test failed:\n"
                error_msg += f"Error type: {type(e).__name__}\n"
                error_msg += f"Error message: {str(e)}\n"
                error_msg += f"Details:\n{traceback.format_exc()}"
                return False, error_msg
            finally:
                self._close_client(test_client)

    def disconnect(self) -> str:
        """
        Disconnect from database.

        Returns:
            str: Status message
        """
        with self._lock:
            client = self.client
            if not client:
                return "Not connected to database"
            self.client = None
            self.is_connected = False
            self.connection_info = {}

        self._close_client(client)
        return "Disconnected from database"

    @staticmethod
    def _close_client(client) -> None:
        """Close a ClickHouse client without masking the caller's result."""
        if client is None:
            return
        try:
            client.close()
        except Exception:
            pass

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
        """Store credentials and close clients tied to a different connection."""
        credentials = dict(credentials) if credentials is not None else None
        with self._lock:
            if credentials == self._credentials:
                return
            clients = list(self._clients.values())
            self._clients.clear()
            self._credentials = credentials

        for client in clients:
            try:
                client.close()
            except Exception:
                pass

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
            existing_client = self._clients.get(tab_id)
            if existing_client is None:
                self._clients[tab_id] = client
                return client

        # Another worker won the creation race for this tab. Keep the cached
        # connection and release the redundant HTTP client immediately.
        try:
            client.close()
        except Exception:
            pass
        return existing_client

    def execute_query(self, tab_id: int, query: str):
        """Execute a query, refreshing once if its connection reports unknown table."""
        client = self.get_or_create_client(tab_id)
        try:
            return client.query(query)
        except Exception as error:
            if not self._is_unknown_table_error(error):
                raise

            # Query tabs keep independent HTTP clients.  After a table rename, a
            # long-lived client can remain attached to a server that has not yet
            # observed the new table name, even though the explorer's connection
            # already has.  Recreate this tab's client and retry exactly once.
            self.release(tab_id)
            refreshed_client = self.get_or_create_client(tab_id)
            return refreshed_client.query(query)

    def release(self, tab_id: int) -> None:
        """Close and remove the client for a closed or stale tab."""
        with self._lock:
            client = self._clients.pop(tab_id, None)

        if client is not None:
            try:
                client.close()
            except Exception:
                pass

    def close_all(self) -> None:
        """Close every per-tab client."""
        with self._lock:
            clients = list(self._clients.values())
            self._clients.clear()

        for client in clients:
            try:
                client.close()
            except Exception:
                pass

    @staticmethod
    def _is_unknown_table_error(error: Exception) -> bool:
        """Return whether ClickHouse reported UNKNOWN_TABLE (error code 60)."""
        message = str(error).upper()
        return "UNKNOWN_TABLE" in message or bool(
            re.search(r"\bCODE\s*:?\s*60\b", message)
        )


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
