import pytest
from click.testing import CliRunner

from weni_cli.cli import project
from weni_cli.store import STORE_TOKEN_KEY, STORE_PROJECT_UUID_KEY


@pytest.fixture
def mock_store(mocker):
    """Mock the Store class methods"""
    store_mock = mocker.patch("weni_cli.commands.project_use.Store")
    store_instance = store_mock.return_value
    # Default to logged in state
    store_instance.get.return_value = "fake-token"
    return store_instance


@pytest.fixture
def mock_cli_client(mocker):
    """Mock the CLIClient class methods"""
    client_mock = mocker.patch("weni_cli.commands.project_use.CLIClient")
    client_instance = client_mock.return_value

    # Set up specific method behaviors
    client_instance.check_project_permission.return_value = None

    # Add response attribute to mimic the actual client behavior if needed
    client_instance.response = mocker.MagicMock()
    client_instance.response.status_code = 200
    client_instance.response.json.return_value = {"status": "success"}

    return client_instance


@pytest.fixture
def mock_formatter(mocker):
    """Mock the Formatter class methods"""
    formatter_mock = mocker.patch("weni_cli.commands.project_use.Formatter")
    formatter_instance = formatter_mock.return_value
    return formatter_instance


def test_project_use_success(mock_store, mock_cli_client, mock_formatter):
    """Test the successful project use command flow"""
    runner = CliRunner()
    project_uuid = "123456"

    result = runner.invoke(project, ["use", project_uuid])

    # Check CLI client was called with correct project UUID
    mock_cli_client.check_project_permission.assert_called_once_with(project_uuid)

    # Check store was updated with project UUID
    mock_store.set.assert_called_once_with(STORE_PROJECT_UUID_KEY, project_uuid)

    # Check success message was displayed
    mock_formatter.print_success_panel.assert_called_once()
    assert project_uuid in mock_formatter.print_success_panel.call_args[0][0]

    # Verify no errors were displayed
    mock_formatter.print_error_panel.assert_not_called()

    # Check command ran successfully
    assert result.exit_code == 0


def test_project_use_not_logged_in(mock_store, mock_cli_client, mock_formatter):
    """Test project use command when user is not logged in"""
    # Set up mock to simulate not logged in
    mock_store.get.return_value = None

    runner = CliRunner()
    result = runner.invoke(project, ["use", "123456"])

    # Check store.get was called with token key
    mock_store.get.assert_called_once_with(STORE_TOKEN_KEY)

    # Check CLI client was not called (since user isn't logged in)
    mock_cli_client.check_project_permission.assert_not_called()

    # Check store was not updated
    mock_store.set.assert_not_called()

    # Verify error message was displayed with formatter
    mock_formatter.print_error_panel.assert_called_once()
    assert "not logged in" in mock_formatter.print_error_panel.call_args[0][0].lower()

    # Verify no success message was displayed
    mock_formatter.print_success_panel.assert_not_called()

    # Check command ran without crashing
    assert result.exit_code == 0


def test_project_use_permission_error(mock_store, mock_cli_client, mock_formatter):
    """Test project use command when permission check fails"""
    # Set up mock to simulate permission error
    error_message = "You don't have permission to access this project"
    mock_cli_client.check_project_permission.side_effect = Exception(error_message)

    runner = CliRunner()
    project_uuid = "123456"

    result = runner.invoke(project, ["use", project_uuid])

    # Check CLI client was called
    mock_cli_client.check_project_permission.assert_called_once_with(project_uuid)

    # Check store was not updated
    mock_store.set.assert_not_called()

    # Verify error was displayed
    mock_formatter.print_error_panel.assert_called_once()
    # Ensure error message is passed to the formatter
    assert mock_formatter.print_error_panel.call_args[0][0].args[0] == error_message

    # Verify no success message was displayed
    mock_formatter.print_success_panel.assert_not_called()

    # Check command ran without crashing, but showed the error
    assert result.exit_code == 0


def test_project_use_with_invalid_uuid(mock_store, mock_cli_client, mock_formatter):
    """Test project use command with invalid project UUID format"""
    # Set up mock to simulate validation error for invalid UUID
    validation_error = "Invalid project UUID format"
    mock_cli_client.check_project_permission.side_effect = ValueError(validation_error)

    runner = CliRunner()
    invalid_uuid = "invalid-uuid"

    result = runner.invoke(project, ["use", invalid_uuid])

    # Check CLI client was called with the invalid UUID
    mock_cli_client.check_project_permission.assert_called_once_with(invalid_uuid)

    # Check store was not updated
    mock_store.set.assert_not_called()

    # Verify error was displayed
    mock_formatter.print_error_panel.assert_called_once()

    # Verify no success message was displayed
    mock_formatter.print_success_panel.assert_not_called()

    # Check command ran without crashing
    assert result.exit_code == 0


def test_project_use_with_nonexistent_project(mock_store, mock_cli_client, mock_formatter):
    """Test project use command with a UUID that doesn't exist"""
    # Set up mock to simulate 404 error for non-existent project
    not_found_error = "Project not found"
    mock_cli_client.check_project_permission.side_effect = Exception(not_found_error)
    mock_cli_client.response.status_code = 404

    runner = CliRunner()
    nonexistent_uuid = "00000000-0000-0000-0000-000000000000"

    result = runner.invoke(project, ["use", nonexistent_uuid])

    # Check CLI client was called
    mock_cli_client.check_project_permission.assert_called_once_with(nonexistent_uuid)

    # Check store was not updated
    mock_store.set.assert_not_called()

    # Verify error was displayed
    mock_formatter.print_error_panel.assert_called_once()

    # Verify no success message was displayed
    mock_formatter.print_success_panel.assert_not_called()

    # Check command ran without crashing
    assert result.exit_code == 0
