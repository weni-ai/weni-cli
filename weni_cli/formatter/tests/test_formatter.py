import pytest
from rich.panel import Panel
from rich.text import Text

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
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    error_message = "This is an error message"

    formatter.print_error_panel(error_message)

    mock_print.assert_called_once()

    panel_arg = mock_print.call_args[0][0]
    assert isinstance(panel_arg, Panel)
    assert panel_arg.title == "[bold red]Error[/bold red]"
    assert panel_arg.renderable == error_message
    assert panel_arg.style == "bold red"
    assert panel_arg.expand is False


def test_print_success_panel(formatter, mocker):
    """Test the success panel creation and printing."""
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    success_message = "This is a success message"

    formatter.print_success_panel(success_message)

    mock_print.assert_called_once()

    panel_arg = mock_print.call_args[0][0]
    assert isinstance(panel_arg, Panel)
    assert panel_arg.title == "[bold green]Success[/bold green]"
    assert panel_arg.renderable == success_message
    assert panel_arg.style == "bold green"
    assert panel_arg.expand is False


def test_print_error_panel_with_exception(formatter, mocker):
    """Test printing an error panel with an exception object."""
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    exception = ValueError("Invalid value")

    formatter.print_error_panel(exception)

    panel_arg = mock_print.call_args[0][0]
    renderable = panel_arg.renderable
    assert isinstance(renderable, Text)
    assert "Invalid value" in renderable.plain


def test_print_error_panel_with_empty_message(formatter, mocker):
    """Test printing an error panel with an empty message."""
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    formatter.print_error_panel("")

    panel_arg = mock_print.call_args[0][0]
    assert panel_arg.title == "[bold red]Error[/bold red]"
    assert panel_arg.renderable == ""
    assert panel_arg.style == "bold red"


def test_print_success_panel_with_formatted_message(formatter, mocker):
    """Test printing a success panel with rich text formatting in the message."""
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    formatted_message = "Operation completed with [bold]important[/bold] data"

    formatter.print_success_panel(formatted_message)

    panel_arg = mock_print.call_args[0][0]
    assert panel_arg.renderable == formatted_message


def test_print_error_panel_preserves_rich_formatting(formatter, mocker):
    """Test that rich formatting in string error messages is preserved."""
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    formatted_error = "Failed to process [italic red]critical[/italic red] component"

    formatter.print_error_panel(formatted_error)

    panel_arg = mock_print.call_args[0][0]
    assert panel_arg.renderable == formatted_error


def test_print_error_panel_with_exception_containing_brackets(formatter, mocker):
    """Test that exception messages with brackets are not interpreted as markup."""
    mock_print = mocker.patch("weni_cli.formatter.formatter.print")

    exception = ValueError("Missing key [foo] in config")

    formatter.print_error_panel(exception)

    panel_arg = mock_print.call_args[0][0]
    renderable = panel_arg.renderable
    assert isinstance(renderable, Text)
    assert renderable.plain == "Missing key [foo] in config"
