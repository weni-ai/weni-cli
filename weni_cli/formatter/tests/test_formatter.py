import pytest
from rich.panel import Panel

from weni_cli.formatter.formatter import Formatter


@pytest.fixture
def formatter():
    """Return a Formatter instance."""
    return Formatter()


def test_formatter_initialization():
    """Test that the Formatter initializes properly."""
    formatter = Formatter()
    assert isinstance(formatter, Formatter)


def test_print_error_panel(formatter, mocker):
    """Test the error panel creation and printing."""
    # Mock the rich.print function
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    # Test message
    error_message = "This is an error message"

    # Call the method
    formatter.print_error_panel(error_message)

    # Verify print was called once
    mock_print.assert_called_once()

    # Verify the correct Panel was created
    panel_arg = mock_print.call_args[0][0]
    assert isinstance(panel_arg, Panel)
    assert panel_arg.title == "[bold red]Error[/bold red]"
    assert error_message in panel_arg.renderable
    assert panel_arg.style == "bold red"
    assert panel_arg.expand is False


def test_print_success_panel(formatter, mocker):
    """Test the success panel creation and printing."""
    # Mock the rich.print function
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    # Test message
    success_message = "This is a success message"

    # Call the method
    formatter.print_success_panel(success_message)

    # Verify print was called once
    mock_print.assert_called_once()

    # Verify the correct Panel was created
    panel_arg = mock_print.call_args[0][0]
    assert isinstance(panel_arg, Panel)
    assert panel_arg.title == "[bold green]Success[/bold green]"
    assert success_message in panel_arg.renderable
    assert panel_arg.style == "bold green"
    assert panel_arg.expand is False


def test_print_error_panel_with_exception(formatter, mocker):
    """Test printing an error panel with an exception object."""
    # Mock the rich.print function
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    # Create an exception
    exception = ValueError("Invalid value")

    # Call the method with the exception
    formatter.print_error_panel(exception)

    # Verify the panel contains the exception message
    panel_arg = mock_print.call_args[0][0]
    assert "Invalid value" in panel_arg.renderable


def test_print_error_panel_with_empty_message(formatter, mocker):
    """Test printing an error panel with an empty message."""
    # Mock the rich.print function
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    # Call the method with an empty message
    formatter.print_error_panel("")

    # Verify the panel was created with the empty message
    panel_arg = mock_print.call_args[0][0]
    assert panel_arg.title == "[bold red]Error[/bold red]"
    assert panel_arg.style == "bold red"


def test_print_success_panel_with_formatted_message(formatter, mocker):
    """Test printing a success panel with rich text formatting in the message."""
    # Mock the rich.print function
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    # Test message with formatting
    formatted_message = "Operation completed with [bold]important[/bold] data"

    # Call the method
    formatter.print_success_panel(formatted_message)

    # Verify the formatted message is preserved
    panel_arg = mock_print.call_args[0][0]
    assert "Operation completed with [bold]important[/bold] data" in panel_arg.renderable


def test_print_error_panel_preserves_rich_formatting(formatter, mocker):
    """Test that rich formatting in error messages is preserved."""
    # Mock the rich.print function
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    # Error message with rich formatting
    formatted_error = "Failed to process [italic red]critical[/italic red] component"

    # Call the method
    formatter.print_error_panel(formatted_error)

    # Verify the formatted message is in the panel content
    panel_arg = mock_print.call_args[0][0]
    assert "Failed to process [italic red]critical[/italic red] component" in panel_arg.renderable
