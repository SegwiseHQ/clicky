# ClickHouse Client - Test Suite

This directory contains comprehensive unit tests for the ClickHouse Client application.

## Test Coverage

### `test_main.py`
Tests for the main entry point (`main.py`):
- **TestMain**: Tests the main function and module structure
- **TestMainModuleStructure**: Tests module documentation and structure
- **TestMainIntegration**: Integration tests for main execution flow

### `test_database.py`
Tests for the database management module (`database.py`):
- **TestDatabaseManager**: Tests the DatabaseManager class
  - Connection management (success/failure scenarios)
  - Query execution
  - Table and column retrieval
  - Disconnection
- **TestPasswordFunctions**: Tests encryption/decryption functions
- **TestDatabaseManagerIntegration**: Integration tests for complete workflows

## Running Tests

### Using the Test Runner (Recommended)

```bash
# Run all tests
python run_tests.py

# Run specific module tests
python run_tests.py main
python run_tests.py database

# Run a specific test
python run_tests.py --test tests.test_main.TestMain.test_init

# List available options
python run_tests.py --list
```

### Using unittest directly

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_main -v
python -m unittest tests.test_database -v

# Run specific test class
python -m unittest tests.test_main.TestMain -v

# Run specific test method
python -m unittest tests.test_main.TestMain.test_init -v
```

## Test Design

### Mocking Strategy
- External dependencies (`clickhouse_connect`, `config`) are mocked to ensure tests run without requiring actual database connections or configuration files
- Each test class uses appropriate mocking strategies to isolate the code under test

### Test Categories

1. **Unit Tests**: Test individual functions and methods in isolation
2. **Integration Tests**: Test interactions between components
3. **Error Handling Tests**: Test error conditions and exception handling
4. **Edge Case Tests**: Test boundary conditions and unusual inputs

### Test Structure
Each test follows the Arrange-Act-Assert pattern:
- **Arrange**: Set up test data and mocks
- **Act**: Execute the code under test
- **Assert**: Verify the expected behavior

## Test Coverage Details

### Main Module (`main.py`)
- ✅ Main function execution
- ✅ Application instantiation
- ✅ Error handling during app creation and running
- ✅ Module structure and documentation
- ✅ Import verification

### Database Module (`database.py`)

#### DatabaseManager Class
- ✅ Initialization
- ✅ Connection success scenarios
- ✅ Connection failure scenarios (missing fields, invalid ports, network errors)
- ✅ Query execution (success and failure)
- ✅ Table listing
- ✅ Column information retrieval
- ✅ Disconnection
- ✅ Error handling and edge cases

#### Password Functions
- ✅ Password encryption (success, empty input, null input)
- ✅ Password decryption (success, empty input, error handling)

#### Integration Workflows
- ✅ Complete connection workflow (connect → query → disconnect)
- ✅ Table browsing workflow (connect → list tables → get columns)
- ✅ Multiple independent connections

## Adding New Tests

When adding new tests:

1. **Create test files** following the naming convention `test_<module_name>.py`
2. **Use descriptive test method names** that explain what is being tested
3. **Include docstrings** explaining the test purpose
4. **Mock external dependencies** appropriately
5. **Follow the Arrange-Act-Assert pattern**
6. **Test both success and failure scenarios**
7. **Update this README** to document new test coverage

## Test Configuration

### Dependencies
Tests are designed to run without external dependencies by using comprehensive mocking. The following modules are mocked:
- `clickhouse_connect`: ClickHouse database client
- `config`: Application configuration including encryption keys

### Environment
Tests run in an isolated environment and do not require:
- Active ClickHouse database connections
- Configuration files
- Network connectivity
- Special permissions

## Continuous Integration

These tests are designed to be run in CI/CD environments and should:
- ✅ Run quickly (all tests complete in under 1 second)
- ✅ Be deterministic (same results every time)
- ✅ Require no external dependencies
- ✅ Provide clear failure messages
- ✅ Have comprehensive coverage of critical functionality
