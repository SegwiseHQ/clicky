"""
Unit tests for database.py module.

This module tests the DatabaseManager class and related functions
for ClickHouse database connection management.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add the parent directory to the path so we can import database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock all the dependencies before importing the module
sys.modules["clickhouse_connect"] = MagicMock()
config_mock = MagicMock()
config_mock.DEFAULT_CONNECT_TIMEOUT = 10
config_mock.DEFAULT_SEND_RECEIVE_TIMEOUT = 30
config_mock.DEFAULT_QUERY_RETRIES = 2
sys.modules["config"] = config_mock

# Now import the database module
import database  # noqa: E402


class TestDatabaseManager(unittest.TestCase):
    """Test cases for the DatabaseManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db_manager = database.DatabaseManager()

    def test_init(self):
        """Test DatabaseManager initialization."""
        self.assertIsNone(self.db_manager.client)
        self.assertFalse(self.db_manager.is_connected)
        self.assertEqual(self.db_manager.connection_info, {})

    @patch("database.clickhouse_connect")
    def test_connect_success(self, mock_clickhouse_connect):
        """Test successful database connection."""
        # Arrange
        mock_client = Mock()
        mock_clickhouse_connect.get_client.return_value = mock_client
        mock_client.query.return_value = None  # Successful test query

        # Act
        success, message = self.db_manager.connect(
            host="localhost",
            port=8123,
            username="default",
            password="password",
            database="default",
        )

        # Assert
        self.assertTrue(success)
        self.assertEqual(message, "Connected successfully to localhost:8123")
        self.assertTrue(self.db_manager.is_connected)
        self.assertEqual(self.db_manager.client, mock_client)
        self.assertEqual(
            self.db_manager.connection_info,
            {
                "host": "localhost",
                "port": 8123,
                "username": "default",
                "database": "default",
            },
        )

        # Verify client creation parameters
        mock_clickhouse_connect.get_client.assert_called_once_with(
            host="localhost",
            port=8123,
            username="default",
            password="password",
            database="default",
            secure=True,
            connect_timeout=10,
            send_receive_timeout=30,
            query_retries=2,
        )
        mock_client.query.assert_called_once_with("SELECT 1")

    @patch("database.clickhouse_connect")
    def test_connect_with_custom_timeouts(self, mock_clickhouse_connect):
        """Test successful database connection with custom timeout and retry values."""
        # Arrange
        mock_client = Mock()
        mock_clickhouse_connect.get_client.return_value = mock_client
        mock_client.query.return_value = None  # Successful test query

        # Act
        success, message = self.db_manager.connect(
            host="localhost",
            port=8123,
            username="default",
            password="password",
            database="default",
            connect_timeout=5,
            send_receive_timeout=60,
            query_retries=1,
        )

        # Assert
        self.assertTrue(success)
        self.assertEqual(message, "Connected successfully to localhost:8123")

        # Verify client creation parameters with custom timeouts
        mock_clickhouse_connect.get_client.assert_called_once_with(
            host="localhost",
            port=8123,
            username="default",
            password="password",
            database="default",
            secure=True,
            connect_timeout=5,
            send_receive_timeout=60,
            query_retries=1,
        )

    @patch("database.clickhouse_connect")
    def test_connect_missing_host(self, mock_clickhouse_connect):
        """Test connection with missing host."""
        # Act
        success, message = self.db_manager.connect(
            host="",
            port=8123,
            username="default",
            password="password",
            database="default",
        )

        # Assert
        self.assertFalse(success)
        self.assertEqual(message, "All fields except password must be filled")
        self.assertFalse(self.db_manager.is_connected)
        self.assertIsNone(self.db_manager.client)

    @patch("database.clickhouse_connect")
    def test_connect_missing_username(self, mock_clickhouse_connect):
        """Test connection with missing username."""
        # Act
        success, message = self.db_manager.connect(
            host="localhost",
            port=8123,
            username="",
            password="password",
            database="default",
        )

        # Assert
        self.assertFalse(success)
        self.assertEqual(message, "All fields except password must be filled")

    @patch("database.clickhouse_connect")
    def test_connect_missing_database(self, mock_clickhouse_connect):
        """Test connection with missing database."""
        # Act
        success, message = self.db_manager.connect(
            host="localhost",
            port=8123,
            username="default",
            password="password",
            database="",
        )

        # Assert
        self.assertFalse(success)
        self.assertEqual(message, "All fields except password must be filled")

    @patch("database.clickhouse_connect")
    def test_connect_invalid_port_string(self, mock_clickhouse_connect):
        """Test connection with invalid port (string)."""
        # Act
        success, message = self.db_manager.connect(
            host="localhost",
            port="invalid_port",
            username="default",
            password="password",
            database="default",
        )

        # Assert
        self.assertFalse(success)
        self.assertEqual(message, "Port must be a number, got: invalid_port")

    @patch("database.clickhouse_connect")
    def test_connect_port_conversion(self, mock_clickhouse_connect):
        """Test connection with port as string that can be converted to int."""
        # Arrange
        mock_client = Mock()
        mock_clickhouse_connect.get_client.return_value = mock_client
        mock_client.query.return_value = None

        # Act
        success, message = self.db_manager.connect(
            host="localhost",
            port="8123",  # String port
            username="default",
            password="password",
            database="default",
        )

        # Assert
        self.assertTrue(success)
        self.assertEqual(
            self.db_manager.connection_info["port"], 8123
        )  # Should be converted to int

    @patch("database.clickhouse_connect")
    def test_connect_client_creation_exception(self, mock_clickhouse_connect):
        """Test connection when client creation fails."""
        # Arrange
        mock_clickhouse_connect.get_client.side_effect = Exception("Connection error")

        # Act
        success, message = self.db_manager.connect(
            host="localhost",
            port=8123,
            username="default",
            password="password",
            database="default",
        )

        # Assert
        self.assertFalse(success)
        self.assertIn("Connection failed:", message)
        self.assertIn("Exception", message)
        self.assertIn("Connection error", message)
        self.assertFalse(self.db_manager.is_connected)
        self.assertIsNone(self.db_manager.client)

    @patch("database.clickhouse_connect")
    def test_connect_test_query_exception(self, mock_clickhouse_connect):
        """Test connection when test query fails."""
        # Arrange
        mock_client = Mock()
        mock_clickhouse_connect.get_client.return_value = mock_client
        mock_client.query.side_effect = Exception("Query failed")

        # Act
        success, message = self.db_manager.connect(
            host="localhost",
            port=8123,
            username="default",
            password="password",
            database="default",
        )

        # Assert
        self.assertFalse(success)
        self.assertIn("Connection failed:", message)
        self.assertIn("Query failed", message)
        self.assertFalse(self.db_manager.is_connected)
        self.assertIsNone(self.db_manager.client)

    def test_disconnect_when_connected(self):
        """Test disconnecting when there is an active connection."""
        # Arrange
        self.db_manager.client = Mock()
        self.db_manager.is_connected = True
        self.db_manager.connection_info = {"host": "localhost"}

        # Act
        message = self.db_manager.disconnect()

        # Assert
        self.assertEqual(message, "Disconnected from database")
        self.assertIsNone(self.db_manager.client)
        self.assertFalse(self.db_manager.is_connected)
        self.assertEqual(self.db_manager.connection_info, {})

    def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected."""
        # Act
        message = self.db_manager.disconnect()

        # Assert
        self.assertEqual(message, "Not connected to database")
        self.assertIsNone(self.db_manager.client)
        self.assertFalse(self.db_manager.is_connected)

    def test_execute_query_success(self):
        """Test successful query execution."""
        # Arrange
        mock_client = Mock()
        mock_result = Mock()
        mock_client.query.return_value = mock_result
        self.db_manager.client = mock_client

        # Act
        result = self.db_manager.execute_query("SELECT * FROM table")

        # Assert
        self.assertEqual(result, mock_result)
        mock_client.query.assert_called_once_with("SELECT * FROM table")

    def test_execute_query_not_connected(self):
        """Test query execution when not connected."""
        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.db_manager.execute_query("SELECT * FROM table")

        self.assertEqual(str(context.exception), "Not connected to database")

    def test_get_tables_success(self):
        """Test successful table retrieval."""
        # Arrange
        mock_client = Mock()
        mock_result = Mock()
        mock_result.result_rows = [["table1"], ["table2"], ["table3"]]
        mock_client.query.return_value = mock_result
        self.db_manager.client = mock_client

        # Act
        tables = self.db_manager.get_tables()

        # Assert
        self.assertEqual(tables, ["table1", "table2", "table3"])
        mock_client.query.assert_called_once_with("SHOW TABLES")

    def test_get_tables_not_connected(self):
        """Test table retrieval when not connected."""
        # Act
        tables = self.db_manager.get_tables()

        # Assert
        self.assertEqual(tables, [])

    def test_get_tables_exception(self):
        """Test table retrieval when query fails."""
        # Arrange
        mock_client = Mock()
        mock_client.query.side_effect = Exception("Query failed")
        self.db_manager.client = mock_client

        # Act
        tables = self.db_manager.get_tables()

        # Assert
        self.assertEqual(tables, [])

    def test_get_table_columns_success(self):
        """Test successful column retrieval."""
        # Arrange
        mock_client = Mock()
        mock_result = Mock()
        mock_result.result_rows = [
            ["id", "UInt64"],
            ["name", "String"],
            ["created_at", "DateTime"],
        ]
        mock_client.query.return_value = mock_result
        self.db_manager.client = mock_client

        # Act
        columns = self.db_manager.get_table_columns("test_table")

        # Assert
        expected_columns = [
            ("id", "UInt64"),
            ("name", "String"),
            ("created_at", "DateTime"),
        ]
        self.assertEqual(columns, expected_columns)
        mock_client.query.assert_called_once_with("DESCRIBE TABLE `test_table`")

    def test_get_table_columns_with_spaces(self):
        """Test column retrieval with table name that has spaces."""
        # Arrange
        mock_client = Mock()
        mock_result = Mock()
        mock_result.result_rows = [["col1", "String"]]
        mock_client.query.return_value = mock_result
        self.db_manager.client = mock_client

        # Act
        self.db_manager.get_table_columns("  test_table  ")

        # Assert
        mock_client.query.assert_called_once_with("DESCRIBE TABLE `test_table`")

    def test_get_table_columns_not_connected(self):
        """Test column retrieval when not connected."""
        # Act
        columns = self.db_manager.get_table_columns("test_table")

        # Assert
        self.assertEqual(columns, [])

    def test_get_table_columns_exception(self):
        """Test column retrieval when query fails."""
        # Arrange
        mock_client = Mock()
        mock_client.query.side_effect = Exception("Query failed")
        self.db_manager.client = mock_client

        # Act
        columns = self.db_manager.get_table_columns("test_table")

        # Assert
        self.assertEqual(columns, [])


class TestPasswordFunctions(unittest.TestCase):
    """Test cases for password encryption/decryption functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset the config mock before each test
        database.cipher_suite = MagicMock()

    def test_encrypt_password_success(self):
        """Test successful password encryption."""
        # Arrange
        database.cipher_suite.encrypt.return_value = b"encrypted_password"

        # Act
        result = database.encrypt_password("my_password")

        # Assert
        self.assertEqual(result, "encrypted_password")
        database.cipher_suite.encrypt.assert_called_once_with(b"my_password")

    def test_encrypt_password_empty(self):
        """Test encrypting empty password."""
        # Act
        result = database.encrypt_password("")

        # Assert
        self.assertEqual(result, "")
        database.cipher_suite.encrypt.assert_not_called()

    def test_encrypt_password_none(self):
        """Test encrypting None password."""
        # Act
        result = database.encrypt_password(None)

        # Assert
        self.assertEqual(result, "")
        database.cipher_suite.encrypt.assert_not_called()

    def test_decrypt_password_success(self):
        """Test successful password decryption."""
        # Arrange
        database.cipher_suite.decrypt.return_value = b"decrypted_password"

        # Act
        result = database.decrypt_password("encrypted_password")

        # Assert
        self.assertEqual(result, "decrypted_password")
        database.cipher_suite.decrypt.assert_called_once_with(b"encrypted_password")

    def test_decrypt_password_empty(self):
        """Test decrypting empty password."""
        # Act
        result = database.decrypt_password("")

        # Assert
        self.assertEqual(result, "")
        database.cipher_suite.decrypt.assert_not_called()

    def test_decrypt_password_exception(self):
        """Test decryption when cipher fails."""
        # Arrange
        database.cipher_suite.decrypt.side_effect = Exception("Decryption failed")

        # Act
        result = database.decrypt_password("invalid_encrypted")

        # Assert
        self.assertEqual(result, "")


class TestDatabaseManagerIntegration(unittest.TestCase):
    """Integration tests for DatabaseManager workflow."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        pass

    @patch.object(database, "clickhouse_connect")
    def test_full_connection_workflow(self, mock_clickhouse_connect):
        """Test complete connection workflow: connect -> query -> disconnect."""
        # Arrange
        mock_client = Mock()
        mock_clickhouse_connect.get_client.return_value = mock_client
        mock_client.query.return_value = None

        db_manager = database.DatabaseManager()

        # Act 1: Connect
        success, message = db_manager.connect(
            host="localhost",
            port=8123,
            username="default",
            password="password",
            database="default",
        )

        # Assert 1: Connection successful
        self.assertTrue(success)
        self.assertTrue(db_manager.is_connected)

        # Act 2: Execute query
        mock_query_result = Mock()
        mock_client.query.return_value = mock_query_result
        query_result = db_manager.execute_query("SELECT COUNT(*) FROM table")

        # Assert 2: Query executed
        self.assertEqual(query_result, mock_query_result)

        # Act 3: Disconnect
        disconnect_message = db_manager.disconnect()

        # Assert 3: Disconnected
        self.assertEqual(disconnect_message, "Disconnected from database")
        self.assertFalse(db_manager.is_connected)
        self.assertIsNone(db_manager.client)

    @patch.object(database, "clickhouse_connect")
    def test_tables_and_columns_workflow(self, mock_clickhouse_connect):
        """Test workflow for browsing tables and columns."""
        # Arrange
        mock_client = Mock()
        mock_clickhouse_connect.get_client.return_value = mock_client

        # Mock connection test query
        mock_client.query.return_value = None  # For connection test

        db_manager = database.DatabaseManager()
        db_manager.connect("localhost", 8123, "default", "password", "default")

        # Mock tables query
        tables_result = Mock()
        tables_result.result_rows = [["users"], ["orders"], ["products"]]

        # Mock columns query
        columns_result = Mock()
        columns_result.result_rows = [
            ["id", "UInt64"],
            ["email", "String"],
            ["created_at", "DateTime"],
        ]

        # Reset query mock and set up side effects
        mock_client.query.reset_mock()
        mock_client.query.side_effect = [
            tables_result,  # SHOW TABLES
            columns_result,  # DESCRIBE TABLE
        ]

        # Act: Get tables
        tables = db_manager.get_tables()

        # Assert: Tables retrieved
        self.assertEqual(tables, ["users", "orders", "products"])

        # Act: Get columns for a table
        columns = db_manager.get_table_columns("users")

        # Assert: Columns retrieved
        expected_columns = [
            ("id", "UInt64"),
            ("email", "String"),
            ("created_at", "DateTime"),
        ]
        self.assertEqual(columns, expected_columns)

    @patch.object(database, "clickhouse_connect")
    def test_multiple_connections(self, mock_clickhouse_connect):
        """Test that multiple DatabaseManager instances work independently."""
        # Arrange
        mock_client1 = Mock()
        mock_client2 = Mock()
        mock_clickhouse_connect.get_client.side_effect = [mock_client1, mock_client2]

        db_manager1 = database.DatabaseManager()
        db_manager2 = database.DatabaseManager()

        # Act: Connect both managers
        db_manager1.connect("host1", 8123, "user1", "pass1", "db1")
        db_manager2.connect("host2", 9000, "user2", "pass2", "db2")

        # Assert: Both have independent connections
        self.assertEqual(db_manager1.client, mock_client1)
        self.assertEqual(db_manager2.client, mock_client2)
        self.assertEqual(db_manager1.connection_info["host"], "host1")
        self.assertEqual(db_manager2.connection_info["host"], "host2")


if __name__ == "__main__":
    # Configure test runner
    unittest.main(verbosity=2)
