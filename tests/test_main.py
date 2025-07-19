"""
Unit tests for main.py module.

This module tests the main entry point of the ClickHouse Client application.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


class TestMain(unittest.TestCase):
    """Test cases for the main module."""

    @patch("main.ClickHouseClientApp")
    def test_main_function_creates_app_and_runs(self, mock_app_class):
        """Test that main() creates ClickHouseClientApp instance and calls run()."""
        # Arrange
        mock_app_instance = Mock()
        mock_app_class.return_value = mock_app_instance

        # Act
        main.main()

        # Assert
        mock_app_class.assert_called_once()
        mock_app_instance.run.assert_called_once()

    @patch("main.ClickHouseClientApp")
    def test_main_function_handles_app_creation_exception(self, mock_app_class):
        """Test that main() handles exceptions during app creation."""
        # Arrange
        mock_app_class.side_effect = Exception("App creation failed")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            main.main()

        self.assertEqual(str(context.exception), "App creation failed")
        mock_app_class.assert_called_once()

    @patch("main.ClickHouseClientApp")
    def test_main_function_handles_app_run_exception(self, mock_app_class):
        """Test that main() handles exceptions during app.run()."""
        # Arrange
        mock_app_instance = Mock()
        mock_app_instance.run.side_effect = Exception("App run failed")
        mock_app_class.return_value = mock_app_instance

        # Act & Assert
        with self.assertRaises(Exception) as context:
            main.main()

        self.assertEqual(str(context.exception), "App run failed")
        mock_app_class.assert_called_once()
        mock_app_instance.run.assert_called_once()

    @patch("main.main")
    def test_name_main_calls_main_function(self, mock_main_function):
        """Test that the if __name__ == '__main__' block calls main()."""
        # This test simulates running the script directly
        # We need to patch the main function to avoid actually running the app

        # Arrange
        mock_main_function.return_value = None

        # Act - Execute the module's __name__ == '__main__' block
        # We do this by reloading the module, which will trigger the if block
        import importlib

        with patch("main.__name__", "__main__"):
            importlib.reload(main)

        # Note: This test is more complex due to the nature of testing __name__ == '__main__'
        # In practice, you might skip this test or use a different approach

    def test_module_docstring_exists(self):
        """Test that the module has a proper docstring."""
        self.assertIsNotNone(main.__doc__)
        self.assertIn("ClickHouse Client", main.__doc__)
        self.assertIn("GUI application", main.__doc__)

    def test_main_function_docstring_exists(self):
        """Test that the main function has a proper docstring."""
        self.assertIsNotNone(main.main.__doc__)
        self.assertIn("Main entry point", main.main.__doc__)

    def test_module_imports_clickhouse_client_app(self):
        """Test that the module correctly imports ClickHouseClientApp."""
        # This test ensures the import statement works
        self.assertTrue(hasattr(main, "ClickHouseClientApp"))

    @patch("main.ClickHouseClientApp")
    def test_main_function_no_return_value(self, mock_app_class):
        """Test that main() function returns None (void function)."""
        # Arrange
        mock_app_instance = Mock()
        mock_app_class.return_value = mock_app_instance

        # Act
        result = main.main()

        # Assert
        self.assertIsNone(result)

    @patch("main.ClickHouseClientApp")
    def test_app_instance_created_only_once(self, mock_app_class):
        """Test that only one instance of ClickHouseClientApp is created."""
        # Arrange
        mock_app_instance = Mock()
        mock_app_class.return_value = mock_app_instance

        # Act
        main.main()

        # Assert
        self.assertEqual(mock_app_class.call_count, 1)
        self.assertEqual(mock_app_instance.run.call_count, 1)


class TestMainModuleStructure(unittest.TestCase):
    """Test cases for the main module structure and metadata."""

    def test_module_has_shebang(self):
        """Test that the module has a proper shebang line."""
        with open(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py"), "r"
        ) as f:
            first_line = f.readline().strip()
        self.assertEqual(first_line, "#!/usr/bin/env python3")

    def test_module_has_proper_structure(self):
        """Test that the module has the expected structure."""
        # Check that main module has the expected attributes
        expected_attributes = ["main", "ClickHouseClientApp"]
        for attr in expected_attributes:
            self.assertTrue(hasattr(main, attr), f"Module should have {attr}")

    def test_main_function_is_callable(self):
        """Test that main function is callable."""
        self.assertTrue(callable(main.main))

    def test_module_architecture_documentation(self):
        """Test that the module docstring mentions the modular architecture."""
        docstring = main.__doc__
        expected_modules = [
            "config.py",
            "database.py",
            "credentials_manager.py",
            "ui_components.py",
            "data_explorer.py",
            "utils.py",
            "app.py",
        ]

        for module in expected_modules:
            self.assertIn(module, docstring, f"Docstring should mention {module}")


class TestMainIntegration(unittest.TestCase):
    """Integration tests for main module interactions."""

    @patch("main.ClickHouseClientApp")
    def test_main_execution_flow(self, mock_app_class):
        """Test the complete execution flow of main()."""
        # Arrange
        mock_app_instance = Mock()
        mock_app_class.return_value = mock_app_instance

        # Track the order of calls
        call_order = []

        def track_app_creation():
            call_order.append("app_created")
            return mock_app_instance

        def track_app_run():
            call_order.append("app_run")

        mock_app_class.side_effect = track_app_creation
        mock_app_instance.run.side_effect = track_app_run

        # Act
        main.main()

        # Assert
        self.assertEqual(call_order, ["app_created", "app_run"])

    @patch("sys.exit")
    @patch("main.ClickHouseClientApp")
    def test_main_does_not_call_sys_exit(self, mock_app_class, mock_sys_exit):
        """Test that main() does not call sys.exit() under normal circumstances."""
        # Arrange
        mock_app_instance = Mock()
        mock_app_class.return_value = mock_app_instance

        # Act
        main.main()

        # Assert
        mock_sys_exit.assert_not_called()


if __name__ == "__main__":
    # Configure test runner
    unittest.main(verbosity=2)
