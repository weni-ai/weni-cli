import pytest
from unittest.mock import MagicMock, patch

from weni_cli.commands.logs.get import GetLogsHandler


@pytest.fixture
def mock_cli_client():
    """Mock the CLIClient instance."""
    with patch("weni_cli.commands.logs.get.CLIClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_formatter():
    """Mock the Formatter instance."""
    with patch("weni_cli.commands.logs.get.Formatter") as mock_formatter_class:
        mock_formatter_instance = MagicMock()
        mock_formatter_class.return_value = mock_formatter_instance
        yield mock_formatter_instance


@pytest.fixture
def mock_console():
    """Mock the Console instance."""
    with patch("weni_cli.commands.logs.get.Console") as mock_console_class:
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        yield mock_console


@pytest.fixture
def mock_print():
    """Mock the rich print function."""
    with patch("weni_cli.commands.logs.get.print") as mock_print:
        yield mock_print


def test_get_logs_success(mock_cli_client, mock_formatter, mock_console, mock_print):
    """Test successful retrieval and display of logs."""
    # Setup mock response
    logs_data = {
        "logs": [
            {"timestamp": "1640995200000", "message": "First log message"},
            {"timestamp": "1640995260000", "message": "Second log message"}
        ]
    }
    mock_cli_client.get_tool_logs.return_value = (logs_data, None)

    # Call the method
    handler = GetLogsHandler()
    handler.get_logs("test-agent", "test-tool", "2022-01-01", "2022-01-02")

    # Verify client was called with correct parameters
    mock_cli_client.get_tool_logs.assert_called_once_with(
        "test-agent", "test-tool", "2022-01-01", "2022-01-02"
    )

    # Verify the logs were printed
    mock_print.assert_called_once()
    # Verify Panel was used (we can check args[0][0] is Panel)
    assert "Panel" in str(mock_print.call_args[0][0])


def test_get_logs_error(mock_cli_client, mock_formatter, mock_console):
    """Test handling of error response."""
    # Setup mock response with error
    error_message = "Failed to fetch logs"
    mock_cli_client.get_tool_logs.return_value = ({}, error_message)

    # Call the method
    handler = GetLogsHandler()
    handler.get_logs("test-agent", "test-tool", "2022-01-01", "2022-01-02")

    # Verify client was called with correct parameters
    mock_cli_client.get_tool_logs.assert_called_once_with(
        "test-agent", "test-tool", "2022-01-01", "2022-01-02"
    )

    # Verify error was printed
    mock_formatter.print_error_panel.assert_called_once_with(error_message)


def test_get_logs_empty(mock_cli_client, mock_formatter, mock_console):
    """Test handling of empty logs response."""
    # Setup mock response with empty logs
    mock_cli_client.get_tool_logs.return_value = ({}, None)

    # Call the method
    handler = GetLogsHandler()
    handler.get_logs("test-agent", "test-tool", "2022-01-01", "2022-01-02")

    # Verify client was called with correct parameters
    mock_cli_client.get_tool_logs.assert_called_once_with(
        "test-agent", "test-tool", "2022-01-01", "2022-01-02"
    )

    # Verify error was printed
    mock_formatter.print_error_panel.assert_called_once_with("No logs found")
