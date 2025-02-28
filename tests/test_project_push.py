import os
import requests_mock
import pytest
import json
import zipfile
import io

from click.testing import CliRunner

from weni_cli.cli import project
from weni_cli.commands.init import (
    SAMPLE_AGENT_DEFINITION_YAML,
    SAMPLE_ORDER_STATUS_SKILL_PY,
    SAMPLE_ORDER_DETAILS_SKILL_PY,
    SKILLS_FOLDER,
)
from weni_cli.commands.project_push import ProjectPushHandler


@pytest.fixture(autouse=True)
def slow_down_tests(mocker):
    mocker.resetall()


def create_mocked_files():
    with open("agents.json", "w") as f:
        f.write(SAMPLE_AGENT_DEFINITION_YAML)

    try:
        os.mkdir(SKILLS_FOLDER)
        os.mkdir(f"{SKILLS_FOLDER}/order_status")
        os.mkdir(f"{SKILLS_FOLDER}/order_details")
    except FileExistsError:
        pass

    with open(f"{SKILLS_FOLDER}/order_status/lambda_function.py", "w") as f:
        f.write(SAMPLE_ORDER_STATUS_SKILL_PY)

    with open(f"{SKILLS_FOLDER}/order_details/lambda_function.py", "w") as f:
        f.write(SAMPLE_ORDER_DETAILS_SKILL_PY)

    with open(f"{SKILLS_FOLDER}/order_details/requirements.txt", "w") as f:
        f.write("")


@requests_mock.Mocker(kw="requests_mock")
def test_project_push(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")

    # Mock the streaming response for successful push
    response_line1 = json.dumps({"success": True, "progress": 0.5, "message": "Processing agents"}) + "\n"
    response_line2 = json.dumps({"success": True, "progress": 1.0, "message": "Successfully pushed agents"}) + "\n"
    mock_response = response_line1 + response_line2

    requests_mock.post("https://cli.cloud.weni.ai/api/v1/agents", status_code=200, text=mock_response)

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()

        # Mock the store values - project_uuid, token, and base_url
        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://cli.cloud.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == "Pushing agents\nDefinition pushed successfully\n"


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_with_force_update(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")

    # Mock the streaming response for successful push
    response_line1 = json.dumps({"success": True, "progress": 0.5, "message": "Processing agents"}) + "\n"
    response_line2 = json.dumps({"success": True, "progress": 1.0, "message": "Successfully pushed agents"}) + "\n"
    mock_response = response_line1 + response_line2

    requests_mock.post("https://cli.cloud.weni.ai/api/v1/agents", status_code=200, text=mock_response)

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()

        # Mock the store values - project_uuid, token, and base_url
        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://cli.cloud.weni.ai"])

        result = runner.invoke(project, ["push", "--force-update", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == "Pushing agents\nDefinition pushed successfully\n"


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_file_not_found(mocker, **kwargs):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)
        assert result.exit_code == 2
        assert (
            result.output
            == "Usage: project push [OPTIONS] DEFINITION\nTry 'project push --help' for help.\n\nError: Invalid value for 'DEFINITION': File 'agents.json' does not exist.\n"
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_project_not_found(mocker, **kwargs):
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()

        mocker.patch("weni_cli.store.Store.get", side_effect=[""])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)
        assert result.exit_code == 0
        assert result.output == "No project selected, please select a project first\n"


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_error(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")

    # Mock the streaming response for failed push
    error_response = json.dumps({"success": False, "message": "Failed to push agents", "request_id": "12345"}) + "\n"

    requests_mock.post("https://cli.cloud.weni.ai/api/v1/agents", status_code=400, text=error_response)

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://cli.cloud.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert (
            result.output
            == 'Error: Failed to push agents: {"success": false, "message": "Failed to push agents", "request_id": "12345"}\n\n'
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_invalid_definition(mocker, **kwargs):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("agents.json", "w") as f:
            f.write('agents:\ntest: -123\n  name: "Jon Snow"')

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://cli.cloud.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert (
            result.output
            == 'Failed to parse definition file: mapping values are not allowed here\n  in "agents.json", line 3, column 7\n'
        )


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_empty_definition(mocker, **kwargs):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("agents.json", "w") as f:
            f.write("")

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://cli.cloud.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == "Error: Empty definition file\n"


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_missing_skill_file(mocker, **kwargs):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("agents.json", "w") as f:
            f.write(SAMPLE_AGENT_DEFINITION_YAML)

        mocker.patch("weni_cli.store.Store.get", side_effect=["123456", "456789", "https://cli.cloud.weni.ai"])

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert result.output == "Failed to prepare skill: Folder skills/order_status not found\n"


def test_validate_parameters_valid():
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": "User name", "type": "string", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert error is None
    assert result == parameters


def test_validate_parameters_invalid_type():
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": "User name", "type": "invalid_type", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "type must be one of: string, number, integer, boolean, array" in error


def test_validate_parameters_missing_description():
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"type": "string", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "description is required" in error


def test_validate_parameters_invalid_description_type():
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": 123, "type": "string", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "description must be a string" in error


def test_validate_parameters_missing_type():
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": "User name", "required": True}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "type is required" in error


def test_validate_parameters_invalid_required_type():
    handler = ProjectPushHandler()
    parameters = [{"user_name": {"description": "User name", "type": "string", "required": "yes"}}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "'required' field must be a boolean" in error


def test_validate_parameters_invalid_contact_field_type():
    handler = ProjectPushHandler()
    parameters = [
        {"user_name": {"description": "User name", "type": "string", "required": True, "contact_field": "yes"}}
    ]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "contact_field must be a boolean" in error


def test_validate_parameters_invalid_contact_field_name():
    handler = ProjectPushHandler()
    parameters = [
        {"123invalid": {"description": "User name", "type": "string", "required": True, "contact_field": True}}
    ]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "parameter name must match the regex of a valid contact field" in error


def test_validate_parameters_not_dict():
    handler = ProjectPushHandler()
    parameters = [{"user_name": "not an object"}]
    result, error = handler.validate_parameters(parameters)
    assert result is None
    assert "must be an object" in error


def test_validate_parameters_none():
    handler = ProjectPushHandler()
    result, error = handler.validate_parameters(None)
    assert result is None
    assert error is None


def test_is_valid_contact_field_name():
    handler = ProjectPushHandler()
    assert handler.is_valid_contact_field_name("valid_field") is True
    assert handler.is_valid_contact_field_name("validField") is False
    assert handler.is_valid_contact_field_name("123invalid") is False
    assert handler.is_valid_contact_field_name("_invalid") is False


def test_format_definition():
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
    handler = ProjectPushHandler()
    result = handler.create_skill_folder_zip("test_skill", "nonexistent_path")
    assert result is None


def test_create_skill_folder_zip_exception(monkeypatch):
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
