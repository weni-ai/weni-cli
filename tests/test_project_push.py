import os
import requests_mock
import pytest
import json
import zipfile
import io
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
from weni_cli.commands.project_push import ProjectPushHandler


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
        assert result.output == "No project selected, please select a project first\n"


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
            == f'Using toolkit version: {get_toolkit_version()}\nError: Failed to push agents: {{"success": false, "message": "Failed to push agents", "request_id": "12345"}}\n\n'
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
        assert (
            result.output
            == 'Failed to parse definition file: mapping values are not allowed here\n  in "agents.json", line 3, column 7\n'
        )


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
        assert result.output == "Error: Empty definition file\n"


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
        assert result.output == f"Failed to prepare skill: Folder skills/{SAMPLE_GET_ADDRESS_SKILL_NAME} not found\n"


def test_validate_parameters_valid():
    """Test that valid parameters pass validation."""
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": "User name", "type": "string", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert error is None
    assert result == parameters


def test_validate_parameters_invalid_type():
    """Test that invalid parameter types are rejected."""
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": "User name", "type": "invalid_type", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "type must be one of: string, number, integer, boolean, array" in error


def test_validate_parameters_missing_description():
    """Test that parameters without descriptions are rejected."""
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"type": "string", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "description is required" in error


def test_validate_parameters_invalid_description_type():
    """Test that parameters with non-string descriptions are rejected."""
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": 123, "type": "string", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "description must be a string" in error


def test_validate_parameters_missing_type():
    """Test that parameters without types are rejected."""
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": "User name", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "type is required" in error


def test_validate_parameters_invalid_required_type():
    """Test that parameters with non-boolean required fields are rejected."""
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": "User name", "type": "string", "required": "yes"}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "'required' field must be a boolean" in error


def test_validate_parameters_invalid_contact_field_type():
    """Test that parameters with non-boolean contact_field are rejected."""
    handler = ProjectPushHandler()
    parameters = [
        {"user_name": {"description": "User name", "type": "string", "required": True, "contact_field": "yes"}}
    ]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "contact_field must be a boolean" in error


def test_validate_parameters_invalid_contact_field_name():
    """Test that contact fields with invalid names are rejected."""
    handler = ProjectPushHandler()
    parameters = [
        {"123invalid": {"description": "User name", "type": "string", "required": True, "contact_field": True}}
    ]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "parameter name must match the regex of a valid contact field" in error


def test_validate_parameters_not_dict():
    """Test that non-dictionary parameter values are rejected."""
    handler = ProjectPushHandler()
    parameters = [{"user_name": "not an object"}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "must be an object" in error


def test_validate_parameters_none():
    """Test that None parameters are handled correctly."""
    handler = ProjectPushHandler()
    result, error = handler.validate_parameters(None)
    assert result is None
    assert error is None


def test_is_valid_contact_field_name():
    """Test the contact field name validation logic."""
    handler = ProjectPushHandler()
    assert handler.is_valid_contact_field_name("valid_field") is True
    assert handler.is_valid_contact_field_name("validField") is False
    assert handler.is_valid_contact_field_name("123invalid") is False
    assert handler.is_valid_contact_field_name("_invalid") is False


def test_format_definition():
    """Test that the definition formatter works correctly."""
    handler = ProjectPushHandler()
    definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "skills": [
                    {
                        "test_skill": {
                            "name": "Test Skill",
                            "description": "Skill description",
                            "source": {"path": "skills/test_skill"},
                            "parameters": [
                                {
                                    "param1": {
                                        "description": "Parameter 1",
                                        "type": "string",
                                        "required": True,
                                    }
                                }
                            ],
                        }
                    }
                ],
            }
        }
    }

    formatted = handler.format_definition(definition)
    assert formatted is not None
    assert "agents" in formatted
    assert "test_agent" in formatted["agents"]

    agent = formatted["agents"]["test_agent"]
    assert agent["slug"] == "test-agent"
    assert isinstance(agent["skills"], list)
    assert len(agent["skills"]) == 1

    skill = agent["skills"][0]
    assert skill["slug"] == "test-skill"
    assert skill["name"] == "Test Skill"
    assert skill["description"] == "Skill description"
    assert skill["source"] == {"path": "skills/test_skill"}
    assert skill["parameters"] is not None


def test_format_definition_skill_error():
    """Test that formatting errors in skills are properly handled."""
    handler = ProjectPushHandler()
    definition = {
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "skills": [
                    {
                        "test_skill": {
                            "name": "Test Skill",
                            "description": "Skill description",
                            "source": {"path": "skills/test_skill"},
                            "parameters": [
                                {
                                    "param1": {
                                        "description": 123,  # Invalid description type
                                        "type": "string",
                                        "required": True,
                                    }
                                }
                            ],
                        }
                    }
                ],
            }
        }
    }

    formatted = handler.format_definition(definition)
    assert formatted is None


def test_create_skill_folder_zip_path_not_exists():
    """Test that non-existent skill paths are properly handled."""
    handler = ProjectPushHandler()
    result = handler.create_skill_folder_zip("test_skill", "nonexistent_path")
    assert result is None


def test_create_skill_folder_zip_exception(monkeypatch):
    """Test that exceptions in zip creation are properly handled."""
    handler = ProjectPushHandler()

    # Mock os.path.exists to return True
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    # Mock os.remove to do nothing
    monkeypatch.setattr(os, "remove", lambda path: None)

    # Mock os.walk to raise an exception
    def mock_walk(path):
        raise Exception("Test exception")

    monkeypatch.setattr(os, "walk", mock_walk)

    result = handler.create_skill_folder_zip("test_skill", "skills/test_skill")
    assert result is None


def test_create_skill_folder_zip_success(monkeypatch, tmp_path):
    """Test that skill zip creation works successfully."""
    handler = ProjectPushHandler()

    # Create a temporary skill directory
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()

    # Create a dummy file
    test_file = skill_dir / "test_file.py"
    test_file.write_text("# Test file")

    # Mock ZipFile to use our buffer
    class MockZipFile:
        def __init__(self, path, mode):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def write(self, file_path, arcname):
            pass

    monkeypatch.setattr(zipfile, "ZipFile", MockZipFile)

    # Mock open to return a file-like object
    mock_file = io.BytesIO(b"mock content")

    def mock_open(path, mode="r"):
        return mock_file

    monkeypatch.setattr("builtins.open", mock_open)

    result = handler.create_skill_folder_zip("test_skill", str(skill_dir))

    # Verify the result is our mock file
    assert result == mock_file
