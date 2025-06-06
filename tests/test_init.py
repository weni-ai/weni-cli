import pytest
from click.testing import CliRunner
from pathlib import Path

from weni_cli.cli import init
from weni_cli.commands.init import (
    SAMPLE_AGENT_DEFINITION_FILE_NAME,
    TOOLS_FOLDER,
    SAMPLE_GET_ADDRESS_TOOL_NAME,
    DEFAULT_TEST_DEFINITION_FILE,
    SAMPLE_AGENT_DEFINITION_YAML,
    SAMPLE_GET_ADDRESS_TOOL_PY,
    SAMPLE_TESTS_YAML,
    SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT,
)


@pytest.fixture
def cli_runner():
    """Fixture providing a CLI runner with isolated filesystem."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


def test_init_command_exit_code(cli_runner):
    """Test that the init command executes successfully."""
    result = cli_runner.invoke(init)
    assert result.exit_code == 0, f"Command failed with output: {result.output}"


def test_init_command_creates_agent_definition_file(cli_runner):
    """Test that the init command creates the agent definition file."""
    result = cli_runner.invoke(init)

    # Check file existence
    agent_def_file = Path(SAMPLE_AGENT_DEFINITION_FILE_NAME)
    assert agent_def_file.exists(), f"Agent definition file not created: {agent_def_file}"

    # Check file content
    with open(agent_def_file, "r") as f:
        content = f.read()
    assert content == SAMPLE_AGENT_DEFINITION_YAML, "Agent definition file has incorrect content"

    # Check output message
    assert f"Sample agent definition file created in: {SAMPLE_AGENT_DEFINITION_FILE_NAME}" in result.output


def test_init_command_creates_tool_files(cli_runner):
    """Test that the init command creates the tool files."""
    result = cli_runner.invoke(init)

    # Check main.py
    tool_file = Path(f"{TOOLS_FOLDER}/{SAMPLE_GET_ADDRESS_TOOL_NAME}/main.py")
    assert tool_file.exists(), f"Tool file not created: {tool_file}"

    # Check content of main.py
    with open(tool_file, "r") as f:
        content = f.read()
    assert content == SAMPLE_GET_ADDRESS_TOOL_PY, "Tool file has incorrect content"

    # Check requirements.txt
    requirements_file = Path(f"{TOOLS_FOLDER}/{SAMPLE_GET_ADDRESS_TOOL_NAME}/requirements.txt")
    assert requirements_file.exists(), f"Requirements file not created: {requirements_file}"

    # Check content of requirements.txt
    with open(requirements_file, "r") as f:
        content = f.read()
    assert content == SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT, "Requirements file has incorrect content"

    # Check output messages
    assert f"Sample tool {SAMPLE_GET_ADDRESS_TOOL_NAME} created in:" in result.output
    assert f"Sample requirements file for {SAMPLE_GET_ADDRESS_TOOL_NAME} created in:" in result.output


def test_init_command_creates_test_files(cli_runner):
    """Test that the init command creates the test files."""
    result = cli_runner.invoke(init)

    # Check test file
    test_file = Path(f"{TOOLS_FOLDER}/{SAMPLE_GET_ADDRESS_TOOL_NAME}/{DEFAULT_TEST_DEFINITION_FILE}")
    assert test_file.exists(), f"Test file not created: {test_file}"

    # Check content of test file
    with open(test_file, "r") as f:
        content = f.read()
    assert content == SAMPLE_TESTS_YAML, "Test file has incorrect content"

    # Check output message
    assert f"Sample tests file for {SAMPLE_GET_ADDRESS_TOOL_NAME} created in:" in result.output


def test_init_command_creates_required_directories(cli_runner):
    """Test that the init command creates all required directories."""
    cli_runner.invoke(init)

    # Check tools directory
    tools_dir = Path(TOOLS_FOLDER)
    assert tools_dir.exists() and tools_dir.is_dir(), f"Tools directory not created: {tools_dir}"

    # Check tool-specific directory
    tool_dir = Path(f"{TOOLS_FOLDER}/{SAMPLE_GET_ADDRESS_TOOL_NAME}")
    assert tool_dir.exists() and tool_dir.is_dir(), f"Tool directory not created: {tool_dir}"


def test_init_ensure_directory_error(cli_runner, mocker):
    """Test exception handling in _ensure_directory when an unexpected error occurs."""
    # Mock os.mkdir to raise a non-FileExistsError exception
    mock_mkdir = mocker.patch("os.mkdir")
    mock_mkdir.side_effect = PermissionError("Permission denied")

    # Mock click.echo to verify error message
    mock_echo = mocker.patch("rich_click.echo")

    # Create an instance of InitHandler and call the method directly
    from weni_cli.commands.init import InitHandler

    handler = InitHandler()

    # Call the method with a test directory
    test_dir = "test_directory"
    handler._ensure_directory(test_dir)

    # Verify the exception was caught and error message was displayed
    mock_echo.assert_called_once_with(f"Error creating directory {test_dir}: Permission denied")


def test_init_write_file_error(cli_runner, mocker):
    """Test exception handling in _write_file when an error occurs."""
    # Mock open to raise an exception
    mock_open = mocker.patch("builtins.open")
    mock_open.side_effect = PermissionError("Permission denied")

    # Mock click.echo to verify error message
    mock_echo = mocker.patch("rich_click.echo")

    # Create an instance of InitHandler and call the method directly
    from weni_cli.commands.init import InitHandler

    handler = InitHandler()

    # Call the method with test values
    test_filename = "test_file.py"
    test_content = "test content"
    test_description = "Test file"

    handler._write_file(test_filename, test_content, test_description)

    # Verify the exception was caught and error message was displayed
    mock_echo.assert_called_once_with(f"Error creating {test_description} at {test_filename}: Permission denied")


def test_init_ensure_directory_file_exists_error(cli_runner, mocker):
    """Test exception handling in _ensure_directory when FileExistsError occurs."""
    # Mock os.mkdir to raise FileExistsError
    mock_mkdir = mocker.patch("os.mkdir")
    mock_mkdir.side_effect = FileExistsError("File exists")

    # Mock click.echo to verify it's not called for FileExistsError
    mock_echo = mocker.patch("rich_click.echo")

    # Create an instance of InitHandler and call the method directly
    from weni_cli.commands.init import InitHandler

    handler = InitHandler()

    # Call the method with a test directory
    test_dir = "test_directory"
    handler._ensure_directory(test_dir)

    # Verify mkdir was called but echo wasn't called (pass is executed)
    mock_mkdir.assert_called_once_with(test_dir)
    mock_echo.assert_not_called()
