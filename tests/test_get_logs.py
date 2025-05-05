import pytest
from unittest.mock import MagicMock, patch

from weni_cli.commands.logs.get import GetLogsHandler
from click.testing import CliRunner
from weni_cli.cli import cli


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
    handler.get_logs("test-agent", "test-tool", "2022-01-01", "2022-01-02", pattern=None)

    # Verify client was called with correct parameters
    assert mock_cli_client.get_tool_logs.call_count == 1
    args, kwargs = mock_cli_client.get_tool_logs.call_args
    assert args == ("test-agent", "test-tool", "2022-01-01", "2022-01-02", None, None)
    assert kwargs == {}

    # Verify the logs were printed via console.pager
    # We check if console.print was called, implying the pager displayed something.
    mock_console.print.assert_called_once()
    printed_content = mock_console.print.call_args[0][0]
    assert "First log message" in printed_content
    assert "Second log message" in printed_content


def test_get_logs_error(mock_cli_client, mock_formatter, mock_console):
    """Test handling of error response."""
    # Setup mock response with error
    error_message = "Failed to fetch logs"
    mock_cli_client.get_tool_logs.return_value = ({}, error_message)

    # Call the method
    handler = GetLogsHandler()
    handler.get_logs("test-agent", "test-tool", "2022-01-01", "2022-01-02", pattern=None)

    # Verify client was called with correct parameters
    assert mock_cli_client.get_tool_logs.call_count == 1
    args, kwargs = mock_cli_client.get_tool_logs.call_args
    assert args == ("test-agent", "test-tool", "2022-01-01", "2022-01-02", None, None)
    assert kwargs == {}

    # Verify error was printed
    mock_formatter.print_error_panel.assert_called_once_with(error_message)


def test_get_logs_empty(mock_cli_client, mock_formatter, mock_console):
    """Test handling of empty logs response."""
    # Setup mock response with empty logs
    mock_cli_client.get_tool_logs.return_value = ({}, None)

    # Call the method
    handler = GetLogsHandler()
    handler.get_logs("test-agent", "test-tool", "2022-01-01", "2022-01-02", pattern=None)

    # Verify client was called with correct parameters
    assert mock_cli_client.get_tool_logs.call_count == 1
    args, kwargs = mock_cli_client.get_tool_logs.call_args
    assert args == ("test-agent", "test-tool", "2022-01-01", "2022-01-02", None, None)
    assert kwargs == {}

    # Verify error was printed
    mock_formatter.print_error_panel.assert_called_once_with("No logs found")


# CLI Invocation Tests
def test_cli_get_logs_success(mocker):
    """Test CLI invocation of the get logs command with successful response."""
    # Mock the GetLogsHandler
    mock_handler = MagicMock()
    mocker.patch("weni_cli.commands.logs.get.GetLogsHandler", return_value=mock_handler)

    # Create CLI runner
    runner = CliRunner()

    # Invoke the CLI command
    result = runner.invoke(
        cli, ["get", "logs", "--agent", "test-agent", "--tool", "test-tool"]
    )

    # Verify CLI command executed successfully
    assert result.exit_code == 0

    # Verify handler was called with correct parameters
    mock_handler.get_logs.assert_called_once_with(
        agent="test-agent", tool="test-tool", start_time=None, end_time=None, pattern=None
    )


def test_cli_get_logs_with_time_range_and_pattern(mocker):
    """Test CLI invocation with time range and pattern parameters."""
    # Mock the GetLogsHandler
    mock_handler = MagicMock()
    mocker.patch("weni_cli.commands.logs.get.GetLogsHandler", return_value=mock_handler)

    # Create CLI runner
    runner = CliRunner()

    # Invoke the CLI command with time range and pattern
    result = runner.invoke(
        cli, [
            "get", "logs",
            "--agent", "test-agent",
            "--tool", "test-tool",
            "--start-time", "2023-01-01T00:00:00",
            "--end-time", "2023-01-02T00:00:00",
            "--pattern", "error"
        ]
    )

    # Verify CLI command executed successfully
    assert result.exit_code == 0

    # Verify handler was called with correct parameters
    mock_handler.get_logs.assert_called_once()
    call_args = mock_handler.get_logs.call_args[1]
    assert call_args["agent"] == "test-agent"
    assert call_args["tool"] == "test-tool"
    assert call_args["start_time"] is not None  # DateTime object was created
    assert call_args["end_time"] is not None    # DateTime object was created
    assert call_args["pattern"] == "error"


def test_cli_get_logs_error(mocker):
    """Test CLI invocation with handler raising an exception."""
    # Mock the GetLogsHandler to raise an exception
    mock_handler = MagicMock()
    mock_handler.get_logs.side_effect = Exception("Test error")
    mocker.patch("weni_cli.commands.logs.get.GetLogsHandler", return_value=mock_handler)

    # Create CLI runner
    runner = CliRunner()

    # Invoke the CLI command
    result = runner.invoke(
        cli, ["get", "logs", "--agent", "test-agent", "--tool", "test-tool"]
    )

    # Verify CLI command executed successfully but handled the error
    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_cli_get_logs_missing_required_args():
    """Test CLI invocation with missing required arguments."""
    # Create CLI runner
    runner = CliRunner()

    # Invoke the CLI command without required agent
    result = runner.invoke(cli, ["get", "logs", "--tool", "test-tool"])

    # Verify CLI command failed due to missing required argument
    assert result.exit_code != 0
    assert "Missing option" in result.output
    assert "--agent" in result.output

    # Invoke the CLI command without required tool
    result = runner.invoke(cli, ["get", "logs", "--agent", "test-agent"])

    # Verify CLI command failed due to missing required argument
    assert result.exit_code != 0
    assert "Missing option" in result.output
    assert "--tool" in result.output


def test_get_logs_invalid_pattern(mock_cli_client, mock_formatter, mock_console):
    """Test handling of invalid regex pattern."""
    handler = GetLogsHandler()
    handler.get_logs("test-agent", "test-tool", None, None, pattern="%invalid%")

    mock_formatter.print_error_panel.assert_called_once_with("Regex patterns are not supported")
    mock_cli_client.get_tool_logs.assert_not_called()


@patch("weni_cli.commands.logs.get.Confirm.ask")
def test_get_logs_pagination_no_more_logs(mock_confirm_ask, mock_cli_client, mock_formatter, mock_console, mock_print):
    """Test pagination where the second page has no logs."""
    # Mock Confirm.ask to continue fetching
    mock_confirm_ask.return_value = True

    # Mock client responses for two pages
    first_page_logs = {
        "logs": [{"timestamp": "1640995200000", "message": "Log page 1"}],
        "next_token": "token_page_2"
    }
    second_page_logs = {"logs": []}  # Empty logs on the second page

    mock_cli_client.get_tool_logs.side_effect = [
        (first_page_logs, None),
        (second_page_logs, None)
    ]

    handler = GetLogsHandler()
    handler.get_logs("test-agent", "test-tool", None, None, pattern=None)

    # Verify client called twice (once for each page)
    assert mock_cli_client.get_tool_logs.call_count == 2
    # Verify first call without token
    call1_args, call1_kwargs = mock_cli_client.get_tool_logs.call_args_list[0]
    assert call1_args == ("test-agent", "test-tool", None, None, None, None)
    # Verify second call with token
    call2_args, call2_kwargs = mock_cli_client.get_tool_logs.call_args_list[1]
    assert call2_args == ("test-agent", "test-tool", None, None, None, "token_page_2")

    # Verify first page logs printed via console
    mock_console.print.assert_called_once()
    printed_content = mock_console.print.call_args[0][0]
    assert "Log page 1" in printed_content

    # Verify "No more logs found" printed (using rich.print for this specific message)
    mock_print.assert_called_once_with("[bold yellow]No more logs found.[/bold yellow]")

    # Verify Confirm.ask was called once after the first page
    mock_confirm_ask.assert_called_once_with("Fetch more logs?", default=True)


@patch("weni_cli.commands.logs.get.Confirm.ask")
@patch("weni_cli.commands.logs.get.CLIClient")
def test_cli_get_logs_pagination_user_declines(mock_cli_client_class, mock_confirm_ask, mock_formatter, mock_console):
    """Test CLI invocation with pagination where the user declines fetching more logs."""
    # Mock Confirm.ask to stop fetching
    mock_confirm_ask.return_value = False

    # Configure the mock CLIClient instance
    mock_client_instance = MagicMock()
    mock_cli_client_class.return_value = mock_client_instance

    # Mock client response for the first page
    first_page_logs = {
        "logs": [{"timestamp": "1640995200000", "message": "Log page 1 CLI"}],
        "next_token": "token_page_2_cli"
    }
    mock_client_instance.get_tool_logs.return_value = (first_page_logs, None)

    # Create CLI runner
    runner = CliRunner()

    # Invoke the CLI command
    # We don't need mocker here as we patch dependencies directly
    result = runner.invoke(
        cli, ["get", "logs", "--agent", "test-agent-cli", "--tool", "test-tool-cli"]
    )

    # Verify CLI command executed successfully
    assert result.exit_code == 0

    # Verify client called only once (for the first page)
    mock_client_instance.get_tool_logs.assert_called_once()
    args, kwargs = mock_client_instance.get_tool_logs.call_args
    assert args == ("test-agent-cli", "test-tool-cli", None, None, None, None)

    # Verify first page logs printed via console's pager
    # Check that console.print was called within the pager context
    mock_console.print.assert_called_once()
    printed_content = mock_console.print.call_args[0][0]
    assert "Log page 1 CLI" in printed_content

    # Verify Confirm.ask was called
    mock_confirm_ask.assert_called_once_with("Fetch more logs?", default=True)

    # Verify no error panels were printed
    mock_formatter.print_error_panel.assert_not_called()
