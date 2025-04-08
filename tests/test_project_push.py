import os
import requests_mock
import pytest
import json
import importlib
from click.testing import CliRunner

from weni_cli.cli import project
from weni_cli.commands.init import (
    SAMPLE_AGENT_DEFINITION_YAML,
    SAMPLE_GET_ADDRESS_SKILL_NAME,
    SAMPLE_GET_ADDRESS_SKILL_PY,
    SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT,
    SKILLS_FOLDER,
)


def get_toolkit_version():
    """Get the version of the weni-agents-toolkit package."""
    return importlib.metadata.version("weni-agents-toolkit")


@pytest.fixture(autouse=True)
def slow_down_tests(mocker):
    """Reset all mocks before each test."""
    mocker.resetall()


@pytest.fixture
def create_mocked_files():
    """Create the necessary files for testing project push."""

    def _create():
        # Write the agent definition file
        with open("agents.json", "w") as f:
            f.write(SAMPLE_AGENT_DEFINITION_YAML)

        # Create skill directories
        try:
            os.mkdir(SKILLS_FOLDER)
            os.mkdir(f"{SKILLS_FOLDER}/{SAMPLE_GET_ADDRESS_SKILL_NAME}")
        except FileExistsError:
            pass

        # Write skill files
        with open(f"{SKILLS_FOLDER}/{SAMPLE_GET_ADDRESS_SKILL_NAME}/main.py", "w") as f:
            f.write(SAMPLE_GET_ADDRESS_SKILL_PY)

        with open(f"{SKILLS_FOLDER}/{SAMPLE_GET_ADDRESS_SKILL_NAME}/requirements.txt", "w") as f:
            f.write(SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT)

    return _create


@pytest.fixture
def mock_cli_response():
    """Mock the response from the CLI API for testing."""

    def _mock_response(
        requests_mock, status_code=200, is_success=True, message="Successfully pushed agents", request_id=None
    ):
        if is_success:
            # Mock successful streaming response
            response_line1 = json.dumps({"success": True, "progress": 0.5, "message": "Processing agents"}) + "\n"
            response_line2 = json.dumps({"success": True, "progress": 1.0, "message": message}) + "\n"
            mock_response = response_line1 + response_line2
        else:
            # Mock error response
            mock_response = json.dumps({"success": False, "message": message, "request_id": request_id}) + "\n"

        requests_mock.post("https://cli.cloud.weni.ai/api/v1/agents", status_code=status_code, text=mock_response)

    return _mock_response


@pytest.fixture
def mock_store_values():
    """Mock the Store.get method to return test values."""

    def _mock(mocker, project_uuid="123456", user_uuid="456789", token="token", base_url="https://cli.cloud.weni.ai"):
        mocker.patch("weni_cli.store.Store.get", side_effect=[project_uuid, user_uuid, token, base_url])

    return _mock


@requests_mock.Mocker(kw="requests_mock")
def test_project_push(mocker, create_mocked_files, mock_cli_response, mock_store_values, **kwargs):
    """Test that the project push command works successfully."""
    # Setup mocks
    requests_mock = kwargs.get("requests_mock")
    mock_cli_response(requests_mock)
    mock_store_values(mocker)

    # Run the command
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()
        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        # Verify results
        assert result.exit_code == 0
        assert (
            result.output
            == f"Using toolkit version: {get_toolkit_version()}\nPushing agents\nDefinition pushed successfully\n"
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_with_force_update(mocker, create_mocked_files, mock_cli_response, mock_store_values, **kwargs):
    """Test that the project push command works with the force-update flag."""
    # Setup mocks
    requests_mock = kwargs.get("requests_mock")
    mock_cli_response(requests_mock)
    mock_store_values(mocker)

    # Run the command
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()
        result = runner.invoke(project, ["push", "--force-update", "agents.json"], terminal_width=80)

        # Verify results
        assert result.exit_code == 0
        assert (
            result.output
            == f"Using toolkit version: {get_toolkit_version()}\nPushing agents\nDefinition pushed successfully\n"
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_file_not_found(mocker, **kwargs):
    """Test that the proper error is shown when the definition file is not found."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)
        assert result.exit_code == 2
        assert "Invalid value for 'DEFINITION': File 'agents.json' does not exist." in result.output


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_project_not_found(mocker, create_mocked_files, **kwargs):
    """Test that the proper error is shown when no project is selected."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()

        mocker.patch("weni_cli.store.Store.get", side_effect=[""])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)
        assert result.exit_code == 0
        assert "No project selected, please select a project first" in result.output


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_error(mocker, create_mocked_files, mock_cli_response, mock_store_values, **kwargs):
    """Test that errors from the API are properly handled."""
    # Setup mocks
    requests_mock = kwargs.get("requests_mock")
    mock_cli_response(
        requests_mock, status_code=400, is_success=False, message="Failed to push agents", request_id="12345"
    )
    mock_store_values(mocker)

    # Run the command
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()
        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        # Verify results
        assert result.exit_code == 0
        assert (
            result.output
            == f"Using toolkit version: {get_toolkit_version()}\nError: Failed to push agents - Request ID: 12345\n"
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_invalid_definition(mocker, mock_store_values, **kwargs):
    """Test that invalid YAML definitions are properly handled."""
    mock_store_values(mocker)

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create an invalid YAML file
        with open("agents.json", "w") as f:
            f.write('agents:\ntest: -123\n  name: "Jon Snow"')

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert "Failed to load definition file" in result.output
        assert "mapping values are not allowed here"


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_empty_definition(mocker, mock_store_values, **kwargs):
    """Test that empty definition files are properly handled."""
    mock_store_values(mocker)

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("agents.json", "w") as f:
            f.write("")

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert "Empty definition file" in result.output


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_missing_skill_file(mocker, mock_store_values, **kwargs):
    """Test that missing skill folders are properly handled."""
    mock_store_values(mocker)

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create definition but don't create the skill folder
        with open("agents.json", "w") as f:
            f.write(SAMPLE_AGENT_DEFINITION_YAML)

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert "Failed to create skill folder for skill Get Address in agent CEP Agent" in result.output
        assert "Folder skills/get_address not found" in result.output
