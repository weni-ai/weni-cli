import os
import requests_mock
import pytest
import json
import importlib
import yaml
from click.testing import CliRunner

from weni_cli.cli import project
from weni_cli.commands.init import (
    SAMPLE_AGENT_DEFINITION_YAML,
    SAMPLE_GET_ADDRESS_TOOL_NAME,
    SAMPLE_GET_ADDRESS_TOOL_PY,
    SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT,
    TOOLS_FOLDER,
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

        # Create tool directories
        try:
            os.mkdir(TOOLS_FOLDER)
            os.mkdir(f"{TOOLS_FOLDER}/{SAMPLE_GET_ADDRESS_TOOL_NAME}")
        except FileExistsError:
            pass

        # Write tool files
        with open(f"{TOOLS_FOLDER}/{SAMPLE_GET_ADDRESS_TOOL_NAME}/main.py", "w") as f:
            f.write(SAMPLE_GET_ADDRESS_TOOL_PY)

        with open(f"{TOOLS_FOLDER}/{SAMPLE_GET_ADDRESS_TOOL_NAME}/requirements.txt", "w") as f:
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
        expected_output = (
            f"Using toolkit version: {get_toolkit_version()}\n"
            "╭─ Error ──────────────────────────────────────────────────────────────╮\n"
            "│                                                                      │\n"
            "│ Failed to push definition: Failed to push agents - Request ID: 12345 │\n"
            "│                                                                      │\n"
            "╰──────────────────────────────────────────────────────────────────────╯\n"
        )
        assert result.output == expected_output


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
def test_project_push_missing_tool_file(mocker, mock_store_values, **kwargs):
    """Test that missing tool folders are properly handled."""
    mock_store_values(mocker)

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create definition but don't create the tool folder
        with open("agents.json", "w") as f:
            f.write(SAMPLE_AGENT_DEFINITION_YAML)

        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value

        result = runner.invoke(project, ["push", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        error_call = formatter_instance.print_error_panel.call_args
        message = error_call.args[0]
        title = error_call.kwargs.get("title", "")
        assert "Failed to load definition file" in title
        assert "source path 'tools/get_address' does not exist" in message


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_with_use_apm(mocker, create_mocked_files, mock_cli_response, mock_store_values, **kwargs):
    """Test that --use-apm sends apm_instrumentation=enabled to the backend."""
    requests_mock = kwargs.get("requests_mock")
    mock_cli_response(requests_mock)
    mock_store_values(mocker)

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()
        result = runner.invoke(project, ["push", "--use-apm", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        last_request = requests_mock.last_request
        assert last_request is not None
        request_body = last_request.body or b""
        assert b"apm_instrumentation" in request_body
        assert b"enabled" in request_body


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_with_remove_apm(mocker, create_mocked_files, mock_cli_response, mock_store_values, **kwargs):
    """Test that --remove-apm sends apm_instrumentation=disabled to the backend."""
    requests_mock = kwargs.get("requests_mock")
    mock_cli_response(requests_mock)
    mock_store_values(mocker)

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()
        result = runner.invoke(project, ["push", "--remove-apm", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        last_request = requests_mock.last_request
        assert last_request is not None
        request_body = last_request.body or b""
        assert b"apm_instrumentation" in request_body
        assert b"disabled" in request_body


def test_project_push_rejects_conflicting_apm_flags(mocker, create_mocked_files, mock_store_values):
    """Test that --use-apm and --remove-apm cannot be used together."""
    mock_store_values(mocker)

    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()
        result = runner.invoke(project, ["push", "--use-apm", "--remove-apm", "agents.json"], terminal_width=80)

        assert result.exit_code == 0
        assert "Cannot use --use-apm and --remove-apm together" in result.output


VALID_PASSIVE_DEFINITION = yaml.safe_load(SAMPLE_AGENT_DEFINITION_YAML)

VALID_ACTIVE_DEFINITION = {
    "agents": {
        "payment_agent": {
            "name": "Payment Agent",
            "description": "Recovers incomplete PIX orders",
            "language": "pt_BR",
            "rules": {
                "payment_recovery": {
                    "display_name": "Payment Recovery",
                    "template": "payment_recovery",
                    "start_condition": "Incomplete order without PIX",
                    "source": {
                        "path": "rules/payment_recovery",
                        "entrypoint": "main.PaymentRecovery",
                    },
                    "example": {"input": {}, "output": {}},
                }
            },
            "pre_processing": {
                "source": {
                    "path": "pre_processors/processor",
                    "entrypoint": "processing.PreProcessor",
                },
                "result_examples_file": "result_example.json",
            },
        }
    }
}


@pytest.fixture
def create_active_agent_files():
    """Create files required to push an active agent definition."""

    def _create():
        with open("agents.yaml", "w") as f:
            f.write(yaml.dump(VALID_ACTIVE_DEFINITION, sort_keys=False))

        os.makedirs("rules/payment_recovery", exist_ok=True)
        os.makedirs("pre_processors/processor", exist_ok=True)

        with open("rules/payment_recovery/main.py", "w") as f:
            f.write("class PaymentRecovery: pass\n")
        with open("pre_processors/processor/processing.py", "w") as f:
            f.write("class PreProcessor: pass\n")
        with open("pre_processors/processor/result_example.json", "w") as f:
            f.write("{}")

        return "agents.yaml"

    return _create


class TestProjectPushHandler:
    def test_load_param_required_raises(self):
        handler = ProjectPushHandler()

        with pytest.raises(Exception, match="Missing required parameter definition"):
            handler.load_param({}, "definition", required=True)

    def test_load_tools_folders_delegates(self, mocker):
        handler = ProjectPushHandler()
        expected = ({"agent:tool": "zip"}, None)
        mocker.patch(
            "weni_cli.commands.project_push._load_tools_folders",
            return_value=expected,
        )

        assert handler.load_tools_folders(VALID_PASSIVE_DEFINITION) == expected

    def test_load_rules_folders_delegates(self, mocker):
        handler = ProjectPushHandler()
        expected = ({"agent:rule": "zip"}, None)
        mocker.patch(
            "weni_cli.commands.project_push._load_rules_folders",
            return_value=expected,
        )

        assert handler.load_rules_folders(VALID_ACTIVE_DEFINITION) == expected

    def test_load_preprocessing_folder_delegates(self, mocker):
        handler = ProjectPushHandler()
        expected = ({"agent:preprocessor_folder": "zip"}, None)
        mocker.patch(
            "weni_cli.commands.project_push._load_preprocessing_folder",
            return_value=expected,
        )

        assert handler.load_preprocessing_folder(VALID_ACTIVE_DEFINITION) == expected

    def test_execute_routes_to_push_active_agent(self, mocker):
        handler = ProjectPushHandler()
        mock_active = mocker.patch.object(handler, "push_active_agent")
        mock_store = mocker.patch("weni_cli.commands.project_push.Store")
        mock_store.return_value.get.return_value = "project-uuid"
        mocker.patch(
            "weni_cli.commands.project_push.load_agent_definition",
            return_value=(VALID_ACTIVE_DEFINITION, None),
        )

        handler.execute(definition="agents.yaml")

        mock_active.assert_called_once_with(False, "project-uuid", VALID_ACTIVE_DEFINITION, None)

    def test_execute_passes_apm_instrumentation_to_passive_push(self, mocker):
        handler = ProjectPushHandler()
        mock_passive = mocker.patch.object(handler, "push_passive_agent")
        mock_store = mocker.patch("weni_cli.commands.project_push.Store")
        mock_store.return_value.get.return_value = "project-uuid"
        mocker.patch(
            "weni_cli.commands.project_push.load_agent_definition",
            return_value=(VALID_PASSIVE_DEFINITION, None),
        )

        handler.execute(definition="agents.yaml", use_apm=True)

        mock_passive.assert_called_once_with(False, "project-uuid", VALID_PASSIVE_DEFINITION, "enabled")

    def test_execute_passes_disabled_apm_to_passive_push(self, mocker):
        handler = ProjectPushHandler()
        mock_passive = mocker.patch.object(handler, "push_passive_agent")
        mock_store = mocker.patch("weni_cli.commands.project_push.Store")
        mock_store.return_value.get.return_value = "project-uuid"
        mocker.patch(
            "weni_cli.commands.project_push.load_agent_definition",
            return_value=(VALID_PASSIVE_DEFINITION, None),
        )

        handler.execute(definition="agents.yaml", remove_apm=True)

        mock_passive.assert_called_once_with(False, "project-uuid", VALID_PASSIVE_DEFINITION, "disabled")

    def test_execute_identify_agent_type_error(self, mocker):
        handler = ProjectPushHandler()
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value
        mocker.patch("weni_cli.commands.project_push.Store")
        mocker.patch(
            "weni_cli.commands.project_push.load_agent_definition",
            return_value=({"agents": {"broken_agent": "not-a-dict"}}, None),
        )

        handler.execute(definition="agents.yaml")

        formatter_instance.print_error_panel.assert_called_once()
        assert "Failed to identify agent type" in formatter_instance.print_error_panel.call_args.kwargs["title"]

    def test_push_passive_agent_schema_validation_error(self, mocker):
        handler = ProjectPushHandler()
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value
        mocker.patch(
            "weni_cli.commands.project_push.validate_agent_definition_schema",
            return_value="Invalid passive definition",
        )

        handler.push_passive_agent(False, "project-uuid", VALID_PASSIVE_DEFINITION)

        formatter_instance.print_error_panel.assert_called_once()
        assert "Failed to load definition file" in formatter_instance.print_error_panel.call_args.kwargs["title"]
        assert "Invalid passive definition" in formatter_instance.print_error_panel.call_args.args[0]

    def test_push_passive_agent_load_tools_error(self, mocker):
        handler = ProjectPushHandler()
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value
        mocker.patch("weni_cli.commands.project_push.validate_agent_definition_schema", return_value=None)
        mocker.patch.object(handler, "load_tools_folders", return_value=(None, "Tool folder missing"))

        handler.push_passive_agent(False, "project-uuid", VALID_PASSIVE_DEFINITION)

        formatter_instance.print_error_panel.assert_called_once_with("Tool folder missing")

    def test_push_passive_agent_success(self, mocker):
        handler = ProjectPushHandler()
        mock_push = mocker.patch.object(handler, "push_definition")
        tools_map = {"cep_agent:get_address": "zip"}
        mocker.patch("weni_cli.commands.project_push.validate_agent_definition_schema", return_value=None)
        mocker.patch.object(handler, "load_tools_folders", return_value=(tools_map, None))
        mocker.patch(
            "weni_cli.commands.project_push.format_definition",
            side_effect=lambda definition: definition,
        )

        handler.push_passive_agent(False, "project-uuid", VALID_PASSIVE_DEFINITION, "enabled")

        mock_push.assert_called_once_with(
            False, "passive", "project-uuid", VALID_PASSIVE_DEFINITION, tools_map, "enabled"
        )

    def test_push_active_agent_schema_validation_error(self, mocker):
        handler = ProjectPushHandler()
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value
        mocker.patch(
            "weni_cli.commands.project_push.validate_active_agent_definition_schema",
            return_value="Invalid active definition",
        )

        handler.push_active_agent(False, "project-uuid", VALID_ACTIVE_DEFINITION)

        formatter_instance.print_error_panel.assert_called_once()
        assert "Failed to load definition file" in formatter_instance.print_error_panel.call_args.kwargs["title"]
        assert "Invalid active definition" in formatter_instance.print_error_panel.call_args.args[0]

    def test_push_active_agent_load_rules_error(self, mocker):
        handler = ProjectPushHandler()
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value
        mocker.patch("weni_cli.commands.project_push.validate_active_agent_definition_schema", return_value=None)
        mocker.patch.object(handler, "load_rules_folders", return_value=(None, "Rule folder missing"))

        handler.push_active_agent(False, "project-uuid", VALID_ACTIVE_DEFINITION)

        formatter_instance.print_error_panel.assert_called_once_with("Rule folder missing")

    def test_push_active_agent_load_preprocessing_error(self, mocker):
        handler = ProjectPushHandler()
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value
        mocker.patch("weni_cli.commands.project_push.validate_active_agent_definition_schema", return_value=None)
        mocker.patch.object(handler, "load_rules_folders", return_value=({"agent:rule": "zip"}, None))
        mocker.patch.object(
            handler,
            "load_preprocessing_folder",
            return_value=(None, "Preprocessor folder missing"),
        )

        handler.push_active_agent(False, "project-uuid", VALID_ACTIVE_DEFINITION)

        formatter_instance.print_error_panel.assert_called_once_with("Preprocessor folder missing")

    def test_push_active_agent_success(self, mocker):
        handler = ProjectPushHandler()
        mock_push = mocker.patch.object(handler, "push_definition")
        rules_map = {"payment_agent:payment_recovery": "rule_zip"}
        preprocessing_map = {"payment_agent:preprocessor_folder": "pre_zip"}
        mocker.patch("weni_cli.commands.project_push.validate_active_agent_definition_schema", return_value=None)
        mocker.patch.object(handler, "load_rules_folders", return_value=(rules_map, None))
        mocker.patch.object(handler, "load_preprocessing_folder", return_value=(preprocessing_map, None))
        mocker.patch(
            "weni_cli.commands.project_push.format_definition",
            side_effect=lambda definition: definition,
        )

        handler.push_active_agent(False, "project-uuid", VALID_ACTIVE_DEFINITION, "enabled")

        expected_resources = {**rules_map, **preprocessing_map}
        mock_push.assert_called_once_with(
            False, "active", "project-uuid", VALID_ACTIVE_DEFINITION, expected_resources, None
        )

    def test_push_definition_success(self, mocker):
        handler = ProjectPushHandler()
        mock_client = mocker.patch("weni_cli.commands.project_push.CLIClient")
        mock_echo = mocker.patch("weni_cli.commands.project_push.click.echo")
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value

        handler.push_definition(False, "passive", "project-uuid", VALID_PASSIVE_DEFINITION, {}, "enabled")

        mock_client.return_value.push_agents.assert_called_once_with(
            "project-uuid",
            VALID_PASSIVE_DEFINITION,
            {},
            "passive",
            apm_instrumentation="enabled",
        )
        mock_echo.assert_called_once_with("Definition pushed successfully")
        formatter_instance.print_warning_panel.assert_called_once()

    def test_push_definition_success_without_apm_skips_warning(self, mocker):
        handler = ProjectPushHandler()
        mocker.patch("weni_cli.commands.project_push.CLIClient")
        mocker.patch("weni_cli.commands.project_push.click.echo")
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value

        handler.push_definition(False, "passive", "project-uuid", VALID_PASSIVE_DEFINITION, {}, None)

        formatter_instance.print_warning_panel.assert_not_called()

    def test_push_definition_api_error(self, mocker):
        handler = ProjectPushHandler()
        formatter_mock = mocker.patch("weni_cli.commands.project_push.Formatter")
        formatter_instance = formatter_mock.return_value
        mock_client = mocker.patch("weni_cli.commands.project_push.CLIClient")
        mock_client.return_value.push_agents.side_effect = Exception("API unavailable")

        handler.push_definition(False, "passive", "project-uuid", VALID_PASSIVE_DEFINITION, {})

        formatter_instance.print_error_panel.assert_called_once_with("Failed to push definition: API unavailable")


@requests_mock.Mocker(kw="requests_mock")
def test_project_push_active_agent(mocker, create_active_agent_files, mock_cli_response, mock_store_values, **kwargs):
    """Test that active agent definitions are pushed successfully."""
    requests_mock = kwargs.get("requests_mock")
    mock_cli_response(requests_mock)
    mock_store_values(mocker)

    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_active_agent_files()
        result = runner.invoke(project, ["push", agent_file], terminal_width=80)

        assert result.exit_code == 0
        assert "Definition pushed successfully" in result.output
        last_request = requests_mock.last_request
        assert last_request is not None
        request_body = last_request.body or b""
        assert b"active" in request_body
