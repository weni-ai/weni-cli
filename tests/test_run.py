import os
import pytest
import io
from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.commands.run import RunHandler, DEFAULT_TEST_DEFINITION_FILE
from weni_cli.clients.cli_client import CLIClient


@pytest.fixture(autouse=True)
def reset_all_mocks(mocker):
    """Reset all mocks before each test."""
    mocker.resetall()


@pytest.fixture
def create_mocked_files():
    """Create the necessary files for testing run command."""

    def _create():
        # Write the agent definition file
        with open("agents.yaml", "w") as f:
            f.write(
                """
agents:
  get_address:
    name: Get Address
    description: An agent to get address information
    tools:
      - get_address:
          name: Get Address
          description: A tool to get address information
          source:
            path: tools/get_address
            path_test: test_definition.yaml
            entrypoint: main.Tool
          parameters:
            - address:
                type: string
                description: The address to get information
                required: true
            """
            )

        # Create tool directories
        try:
            os.makedirs("tools/get_address", exist_ok=True)
        except Exception:
            pass

        # Create test definition
        with open("tools/get_address/test_definition.yaml", "w") as f:
            f.write(
                """
test_cases:
  - name: Test Get Address
    input: "123 Main St"
    expected: "123 Main St, New York, NY"
            """
            )

        # Create tool file
        with open("tools/get_address/tool.py", "w") as f:
            f.write(
                """
def run(input, context):
    return f"{input}, New York, NY"
            """
            )

        # Create empty credentials and globals files
        with open("tools/get_address/.env", "w") as f:
            f.write("API_KEY=sample_key\n")

        with open("tools/get_address/.globals", "w") as f:
            f.write("REGION=us-east-1\n")

        return "agents.yaml"

    return _create


@pytest.fixture
def mock_cli_response():
    """Mock the CLI client response for run_test method."""

    def _mock_response(mocker, test_results=None):
        if test_results is None:
            test_results = [
                {
                    "test_name": "Test Get Address",
                    "test_status_code": 200,
                    "test_response": {
                        "response": {
                            "functionResponse": {"responseBody": {"TEXT": {"body": "123 Main St, New York, NY"}}}
                        }
                    },
                    "test_logs": "Running test...\nTest completed successfully.",
                }
            ]

        mock_client = mocker.patch.object(CLIClient, "run_test")
        mock_client.return_value = test_results
        return mock_client

    return _mock_response


@pytest.fixture
def mock_store_values():
    """Mock the store values.

    IMPORTANT: Always use this fixture instead of directly mocking Store.get
    to maintain consistency across test functions and improve maintainability.

    This fixture can be used in three ways:
    1. Default values: mock_store_values(mocker)
    2. Custom values: mock_store_values(mocker, project_uuid="custom", token="custom_token")
    3. Return None for project_uuid: mock_store_values(mocker, project_uuid=None)
    4. Custom side_effect: mock_store_values(mocker, side_effect=["value1", "value2"])
    """

    def _mock(mocker, project_uuid="123456", token="token", base_url="https://cli.cloud.weni.ai", side_effect=None):
        if side_effect is not None:
            # Use the provided side_effect directly
            mock = mocker.patch("weni_cli.store.Store.get", side_effect=side_effect)
            return mock

        # Use the lambda function approach for regular cases
        mock = mocker.patch(
            "weni_cli.store.Store.get",
            side_effect=lambda key, default=None: {
                "project_uuid": project_uuid,
                "token": token,
                "base_url": base_url,
            }.get(key, default),
        )
        return project_uuid

    return _mock


@pytest.fixture
def mock_tool_folder():
    """Mock the tool folder creation."""

    def _mock(mocker):
        mock_zip = mocker.patch("weni_cli.packager.packager.create_tool_folder_zip")
        mock_zip.return_value = io.BytesIO(b"mock zip content")
        return mock_zip

    return _mock


def test_run_command_success(mocker, create_mocked_files, mock_cli_response, mock_store_values, mock_tool_folder):
    """Test running a tool test successfully."""

    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_mocked_files()
        mock_store_values(mocker)
        mock_tool_folder(mocker)
        mock_cli_response(mocker)

        # Mock the methods directly
        mocker.patch(
            "weni_cli.commands.run.RunHandler.load_default_test_definition",
            return_value=f"tools/get_address/{DEFAULT_TEST_DEFINITION_FILE}",
        )
        mocker.patch(
            "weni_cli.commands.run.RunHandler.load_tool_folder", return_value=(io.BytesIO(b"mock zip content"), None)
        )
        mocker.patch("weni_cli.commands.run.RunHandler.get_tool_source_path", return_value="tools/get_address")
        mocker.patch("weni_cli.commands.run.RunHandler.load_tool_credentials", return_value={"API_KEY": "test_key"})
        mocker.patch("weni_cli.commands.run.RunHandler.load_tool_globals", return_value={"REGION": "us-east-1"})
        mocker.patch(
            "weni_cli.commands.run.RunHandler.get_tool_and_agent_name",
            return_value=("Get Address", "Get Address Tool"),
        )

        # Mock the CLIClient.run_test before the test
        mock_client_run = mocker.patch("weni_cli.clients.cli_client.CLIClient.run_test")
        mock_client_run.return_value = []

        # Create a mock response for the live display
        mocker.patch("rich.live.Live", autospec=True)

        # Run the command
        result = runner.invoke(cli, ["run", agent_file, "get_address", "get_address"])
        # Check results
        assert result.exit_code == 0
        assert mock_client_run.call_count == 1


def test_run_command_no_project(mocker, create_mocked_files, mock_store_values):
    """Test running a command without a selected project."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()
        # Use the fixture to mock the Store.get to return None for project_uuid
        mock_store_values(mocker, project_uuid=None)

        result = runner.invoke(cli, ["run", "agents.yaml", "get_address", "get_address"])

        assert result.exit_code == 0
        assert "No project selected" in result.output


def test_run_handler_execute_no_project(mocker, mock_store_values):
    """Test running the handler execute method without a selected project."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Use the fixture to mock the Store.get to return None for project_uuid
        mock_store_values(mocker, project_uuid=None)

        handler = RunHandler()
        result = handler.execute(
            definition="agents.yaml",
            agent_key="get_address",
            tool_key="get_address",
        )

        assert result is None


def test_run_command_with_external_test_file(
    mocker, create_mocked_files, mock_cli_response, mock_store_values, mock_tool_folder
):
    """Test running a tool test with an external test definition file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_mocked_files()
        _ = mock_store_values(mocker)  # Project UUID is saved in the mock
        mock_tool_folder(mocker)
        mock_cli_response(mocker)

        # Create an external test file
        with open("external_test.yaml", "w") as f:
            f.write(
                """
test_cases:
  - name: External Test
    input: "456 Main St"
    expected: "456 Main St, New York, NY"
            """
            )

        result = runner.invoke(cli, ["run", agent_file, "get_address", "get_address", "--file", "external_test.yaml"])

        assert result.exit_code == 0


def test_run_command_invalid_definition(mocker, mock_store_values):
    """Test running a command with an invalid definition file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _ = mock_store_values(mocker)  # Project UUID is saved in the mock

        # Create an invalid YAML file
        with open("invalid.yaml", "w") as f:
            f.write("invalid: yaml: content")

        # Mock the load_yaml_file function to return a proper YAML parse error
        yaml_error = "mapping values are not allowed here"
        mocker.patch("weni_cli.validators.definition.load_yaml_file", return_value=(None, yaml_error))

        result = runner.invoke(cli, ["run", "invalid.yaml", "get_address", "get_address"])

        assert result.exit_code == 0
        # Check for the actual error that's now being displayed
        assert yaml_error in result.output


def test_run_command_missing_definition(mocker, mock_store_values):
    """Test running a command with a missing definition file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _ = mock_store_values(mocker)  # Project UUID is saved in the mock

        result = runner.invoke(cli, ["run", "nonexistent.yaml", "get_address", "get_address"])

        assert result.exit_code != 0  # Expect an error
        assert "does not exist" in result.output


def test_run_command_missing_test_definition(mocker, create_mocked_files, mock_store_values, mock_tool_folder):
    """Test running a command with a missing test definition file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_mocked_files()
        _ = mock_store_values(mocker)  # Project UUID is saved in the mock
        mock_tool_folder(mocker)

        # Remove the test definition file
        os.remove("tools/get_address/test_definition.yaml")

        # Mock load_agent_definition to return valid data
        mocker.patch(
            "weni_cli.commands.run.load_agent_definition",
            return_value=({"agents": {"get_address": {"description": "Test", "tools": []}}}, None),
        )

        # Patch the load_default_test_definition to return None
        mocker.patch("weni_cli.commands.run.RunHandler.load_default_test_definition", return_value=None)

        result = runner.invoke(cli, ["run", agent_file, "get_address", "get_address"])

        assert result.exit_code == 0

        # Check the output directly for the error message
        assert "Failed to get default test definition file" in result.output


def test_run_command_tool_folder_failure(mocker, create_mocked_files, mock_store_values):
    """Test running a command when tool folder creation fails."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_mocked_files()
        _ = mock_store_values(mocker)  # Project UUID is saved in the mock

        # Mock load_agent_definition to return valid data
        mocker.patch(
            "weni_cli.commands.run.load_agent_definition",
            return_value=({"agents": {"get_address": {"description": "Test", "tools": []}}}, None),
        )

        # Patch the load_default_test_definition to return a valid file
        mocker.patch(
            "weni_cli.commands.run.RunHandler.load_default_test_definition",
            return_value="tools/get_address/test_definition.yaml",
        )

        # Patch the load_tool_folder to return None
        mocker.patch("weni_cli.commands.run.RunHandler.load_tool_folder", return_value=(None, "Failed to load tool folder"))

        result = runner.invoke(cli, ["run", agent_file, "get_address", "get_address"])

        assert result.exit_code == 0
        # Check the output directly for the error message
        assert "Failed to load tool folder" in result.output


def test_run_command_tool_name_error(mocker, create_mocked_files, mock_store_values, mock_tool_folder):
    """Test running a command when get_tool_and_agent_name returns None."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_mocked_files()
        _ = mock_store_values(mocker)  # Project UUID is saved in the mock
        mock_tool_folder(mocker)

        # Mock load_agent_definition to return valid data
        mocker.patch(
            "weni_cli.commands.run.load_agent_definition",
            return_value=({"agents": {"get_address": {"description": "Test", "tools": []}}}, None),
        )

        # Mock load_test_definition to return valid data
        mocker.patch("weni_cli.commands.run.load_test_definition", return_value=({"test_cases": []}, None))

        # Patch the load_default_test_definition to return a valid file
        mocker.patch(
            "weni_cli.commands.run.RunHandler.load_default_test_definition",
            return_value="tools/get_address/test_definition.yaml",
        )

        # Patch the load_tool_folder to return a mock folder
        mocker.patch("weni_cli.commands.run.RunHandler.load_tool_folder", return_value=(b"mock_tool_folder", None))

        # Make sure format_definition returns a valid definition
        mocker.patch(
            "weni_cli.commands.run.format_definition", return_value={"agents": {"get_address": {"tools": []}}}
        )

        # Patch the get_tool_and_agent_name to return None
        mocker.patch("weni_cli.commands.run.RunHandler.get_tool_and_agent_name", return_value=(None, None))

        result = runner.invoke(cli, ["run", agent_file, "get_address", "get_address"])

        assert result.exit_code == 0
        # Check the output directly for the error message
        assert "Failed to get tool or agent name" in result.output


def test_run_command_invalid_test_definition(mocker, create_mocked_files, mock_store_values, mock_tool_folder):
    """Test running a command when test definition file is invalid."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_mocked_files()
        _ = mock_store_values(mocker)  # Project UUID is saved in the mock
        mock_tool_folder(mocker)

        # Mock load_agent_definition to return valid data
        mocker.patch(
            "weni_cli.commands.run.load_agent_definition",
            return_value=({"agents": {"get_address": {"description": "Test", "tools": []}}}, None),
        )

        # Mock load_test_definition to return an error
        error_message = "Error loading test definition"
        mocker.patch("weni_cli.commands.run.load_test_definition", return_value=(None, error_message))

        # Patch the load_default_test_definition to return a valid file
        mocker.patch(
            "weni_cli.commands.run.RunHandler.load_default_test_definition",
            return_value="tools/get_address/test_definition.yaml",
        )

        # Patch the load_tool_folder to return a mock folder
        mocker.patch("weni_cli.commands.run.RunHandler.load_tool_folder", return_value=(b"mock_tool_folder", None))

        # Patch the format_definition to return a valid definition
        mocker.patch(
            "weni_cli.commands.run.format_definition", return_value=({"agents": {"get_address": {"tools": []}}}, None)
        )

        result = runner.invoke(cli, ["run", agent_file, "get_address", "get_address"])

        assert result.exit_code == 0

        # The error message should be displayed in the output
        assert error_message in result.output


def test_parse_agent_tool_success():
    """Test parse_agent_tool with valid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        agent_key, tool_key = handler.parse_agent_tool("get_address.get_address")
        assert agent_key == "get_address"
        assert tool_key == "get_address"


def test_parse_agent_tool_failure():
    """Test parse_agent_tool with invalid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        agent_key, tool_key = handler.parse_agent_tool("invalid_format")
        assert agent_key is None
        assert tool_key is None


def test_get_tool_and_agent_name_success():
    """Test get_tool_and_agent_name with valid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock the definition to match our expected structure
        formatted_definition = {
            "agents": {
                "get_address": {
                    "name": "Get Address",
                    "tools": [
                        {
                            "name": "Get Address Tool",
                            "key": "get_address"
                        }
                    ]
                }
            }
        }

        agent_name, tool_name = handler.get_tool_and_agent_name(formatted_definition, "get_address", "get_address")
        assert agent_name == "Get Address"
        assert tool_name == "Get Address Tool"


def test_get_tool_and_agent_name_failure():
    """Test get_tool_and_agent_name with invalid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {"agents": {}}
        agent_name, tool_name = handler.get_tool_and_agent_name(definition, "nonexistent", "nonexistent")
        assert agent_name is None
        assert tool_name is None


def test_get_tool_source_path_success():
    """Test get_tool_source_path with valid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {
            "agents": {"get_address": {"tools": [{"key": "get_address", "source": {"path": "tools/get_address"}}]}}
        }
        path = handler.get_tool_source_path(definition, "get_address", "get_address")
        assert path == "tools/get_address"


def test_get_tool_source_path_failure():
    """Test get_tool_source_path with invalid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {"agents": {}}
        path = handler.get_tool_source_path(definition, "nonexistent", "nonexistent")
        assert path is None


def test_get_tool_source_path_agent_exists_but_tool_not_found():
    """Test get_tool_source_path when agent exists but tool is not found."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {
            "agents": {
                "get_address": {"tools": [{"key": "different_tool", "source": {"path": "tools/different_tool"}}]}
            }
        }
        result = handler.get_tool_source_path(definition, "get_address", "get_address")
        assert result is None


def test_load_tool_credentials_success(mocker):
    """Test load_tool_credentials with valid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock the open function to return a file with credentials
        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="API_KEY=test_key\nSECRET=test_secret\n"))

        credentials = handler.load_tool_credentials("path/to/tool")
        assert credentials == {"API_KEY": "test_key", "SECRET": "test_secret"}
        mock_open.assert_called_once_with("path/to/tool/.env", "r")


def test_load_tool_credentials_failure(mocker):
    """Test load_tool_credentials when file doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock the open function to raise an exception
        mock_open = mocker.patch("builtins.open", side_effect=FileNotFoundError)

        credentials = handler.load_tool_credentials("path/to/tool")
        assert credentials == {}
        mock_open.assert_called_once_with("path/to/tool/.env", "r")


def test_load_tool_globals_success(mocker):
    """Test load_tool_globals with valid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock the open function to return a file with globals
        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="REGION=us-east-1\nLANGUAGE=en\n"))

        globals_dict = handler.load_tool_globals("path/to/tool")
        assert globals_dict == {"REGION": "us-east-1", "LANGUAGE": "en"}
        mock_open.assert_called_once_with("path/to/tool/.globals", "r")


def test_load_tool_globals_failure(mocker):
    """Test load_tool_globals when file doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock the open function to raise an exception
        mock_open = mocker.patch("builtins.open", side_effect=FileNotFoundError)

        globals_dict = handler.load_tool_globals("path/to/tool")
        assert globals_dict == {}
        mock_open.assert_called_once_with("path/to/tool/.globals", "r")


def test_load_default_test_definition_success():
    """Test load_default_test_definition with valid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {
            "agents": {
                "get_address": {
                    "tools": [
                        {"get_address": {"source": {"path": "tools/get_address", "path_test": "custom_test.yaml"}}}
                    ]
                }
            }
        }
        path = handler.load_default_test_definition(definition, "get_address", "get_address")
        assert path == "tools/get_address/custom_test.yaml"


def test_load_default_test_definition_no_path_test():
    """Test load_default_test_definition when path_test is not specified."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {
            "agents": {"get_address": {"tools": [{"get_address": {"source": {"path": "tools/get_address"}}}]}}
        }
        path = handler.load_default_test_definition(definition, "get_address", "get_address")
        assert path == f"tools/get_address/{DEFAULT_TEST_DEFINITION_FILE}"


def test_load_default_test_definition_failure():
    """Test load_default_test_definition with invalid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {"agents": {}}
        path = handler.load_default_test_definition(definition, "nonexistent", "nonexistent")
        assert path is None


def test_load_tool_folder_success(mocker, create_mocked_files):
    """Test load_tool_folder with valid input."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_mocked_files()
        handler = RunHandler()

        # Mock create_tool_folder_zip to return a bytesIO object
        mock_zip = mocker.patch("weni_cli.commands.run.create_tool_folder_zip")
        mock_zip.return_value = (io.BytesIO(b"mock zip content"), None)

        definition = {
            "agents": {
                "get_address": {
                    "tools": [{"get_address": {"name": "Get Address", "source": {"path": "tools/get_address"}}}]
                }
            }
        }

        result, error = handler.load_tool_folder(definition, "get_address", "get_address")
        assert result is not None
        assert error is None
        mock_zip.assert_called_once_with("get-address", "tools/get_address")


def test_load_tool_folder_agent_not_found():
    """Test load_tool_folder when agent is not found."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {"agents": {}}
        result, error = handler.load_tool_folder(definition, "nonexistent", "get_address")
        assert result is None
        assert "Agent nonexistent not found in definition" in str(error)


def test_load_tool_folder_tool_not_found():
    """Test load_tool_folder when tool is not found."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        definition = {"agents": {"get_address": {"tools": []}}}
        result, error = handler.load_tool_folder(definition, "get_address", "nonexistent")
        assert result is None
        assert "Tool nonexistent not found in agent get_address" in str(error)


def test_format_response_for_display_none():
    """Test format_response_for_display with None input."""
    handler = RunHandler()
    result = handler.format_response_for_display(None)
    assert result == "waiting..."


def test_format_response_for_display_no_response():
    """Test format_response_for_display with input missing response key."""
    handler = RunHandler()
    result = handler.format_response_for_display({"not_response": "data"})
    assert result == "{'not_response': 'data'}"


def test_format_response_for_display_no_function_response():
    """Test format_response_for_display with input missing functionResponse key."""
    handler = RunHandler()
    result = handler.format_response_for_display({"response": {"not_function_response": "data"}})
    assert result == "{'not_function_response': 'data'}"


def test_format_response_for_display_no_response_body():
    """Test format_response_for_display with input missing responseBody key."""
    handler = RunHandler()
    result = handler.format_response_for_display({"response": {"functionResponse": {"not_response_body": "data"}}})
    assert result == "{'not_response_body': 'data'}"


def test_format_response_for_display_no_text():
    """Test format_response_for_display with input missing TEXT key."""
    handler = RunHandler()
    result = handler.format_response_for_display(
        {"response": {"functionResponse": {"responseBody": {"not_text": "data"}}}}
    )
    assert result == "{'not_text': 'data'}"


def test_format_response_for_display_success():
    """Test format_response_for_display with valid input."""
    handler = RunHandler()
    result = handler.format_response_for_display(
        {"response": {"functionResponse": {"responseBody": {"TEXT": {"body": "This is the response"}}}}}
    )
    assert result == "This is the response"


def test_get_status_icon_success():
    """Test get_status_icon with success code."""
    handler = RunHandler()
    icon = handler.get_status_icon(200)
    assert icon == "✅"


def test_get_status_icon_failure():
    """Test get_status_icon with error code."""
    handler = RunHandler()
    icon = handler.get_status_icon(400)
    assert icon == "❌"


def test_load_tool_credentials_with_malformed_data(mocker):
    """Test load_tool_credentials when the file contains malformed data."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock the open function to return a file with malformed data (missing =)
        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="API_KEY:test_key\nSECRET=test_secret\n"))

        # Should throw an exception that gets caught, returning empty dict
        credentials = handler.load_tool_credentials("path/to/tool")
        assert credentials == {}
        mock_open.assert_called_once_with("path/to/tool/.env", "r")


def test_load_default_test_definition_exception_handling(mocker):
    """Test load_default_test_definition with an exception during processing."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Create a definition that should trigger an exception
        definition = {
            "agents": {
                "get_address": {
                    "tools": [{"get_address": {"source": None}}]  # This will cause an attribute error when accessed
                }
            }
        }

        # Call the method directly and check the result
        result = handler.load_default_test_definition(definition, "get_address", "get_address")

        # Verify the function returns None on exception
        assert result is None


def test_load_tool_folder_zip_creation_failure(mocker):
    """Test load_tool_folder when create_tool_folder_zip returns None."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Create definition with valid data
        definition = {
            "agents": {
                "get_address": {
                    "tools": [{"get_address": {"name": "Get Address", "source": {"path": "tools/get_address"}}}]
                }
            }
        }

        # Mock create_tool_folder_zip to return None, simulating a failure
        mocker.patch("weni_cli.commands.run.create_tool_folder_zip", return_value=(None, "Failed to create tool folder for tool get_address in agent get_address"))

        # Call the method directly and check the result
        result, error = handler.load_tool_folder(definition, "get_address", "get_address")

        # Verify the function returns None on failure
        assert result is None
        assert "Failed to create tool folder for tool get_address in agent get_address" in str(error)


def test_render_response_and_logs(capsys):
    """Test render_reponse_and_logs method."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Create test logs
        logs = [
            {
                "test_name": "Test 1",
                "test_response": {
                    "response": {"functionResponse": {"responseBody": {"TEXT": {"body": "Response 1"}}}}
                },
                "test_logs": "Log data 1\nMore log data",
            }
        ]

        # Call the method
        handler.render_reponse_and_logs(logs)

        # Capture stdout and check that our content appears
        captured = capsys.readouterr()
        assert "Response 1" in captured.out
        assert "Log data 1" in captured.out
        assert "More log data" in captured.out


def test_parse_agent_tool_with_empty_string():
    """Test parse_agent_tool method with an empty string."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        agent_key, tool_key = handler.parse_agent_tool("")
        assert agent_key is None
        assert tool_key is None


def test_parse_agent_tool_without_delimiter():
    """Test parse_agent_tool method with a string that doesn't contain a delimiter."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        agent_key, tool_key = handler.parse_agent_tool("agenttool")
        assert agent_key is None
        assert tool_key is None


def test_run_test_uses_new_methods(mocker):
    """Test that run_test uses our newly extracted methods."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a separate handler instance for this test
        handler = RunHandler()

        # We'll directly verify that update_live_display gets called
        # by patching it and tracking if it was called
        update_mock = mocker.patch.object(handler, "update_live_display")

        # Skip the indirect approach and directly mock the client creation
        # This ensures we're testing only our handler.run_test method
        # Create a CLIClient mock with a prepared run_test method
        client_mock = mocker.MagicMock()

        # Have the client.run_test method call the callback directly
        def fake_run_test(*args, **kwargs):
            # Directly call the callback function with test data
            # The callback is the 9th positional argument (index 8)
            callback = args[8]
            # Call the callback with some test data
            callback(
                "Test Name",
                {"response": {"text": "Test result"}},
                200,
                "TEST_CASE_COMPLETED",
                kwargs.get("verbose", False),
            )
            return []

        client_mock.run_test.side_effect = fake_run_test

        # This will replace the CLIClient constructor with our mock
        # Save the patch reference for later verification
        mocker.patch("weni_cli.commands.run.CLIClient", return_value=client_mock)

        # Mock the Live context manager
        live_context = mocker.MagicMock()
        live_mock = mocker.MagicMock()
        live_context.__enter__.return_value = live_mock
        mocker.patch("rich.live.Live", return_value=live_context)

        # Mock display_test_results for verification - no need to save the reference
        mocker.patch.object(handler, "display_test_results", return_value="Test Table")

        # Call the handler method to be tested
        handler.run_test(
            "project_uuid",
            {"test": "definition"},
            b"tool_folder",
            "Tool Name",
            "Agent Name",
            {"test": "test_definition"},
            {"API_KEY": "key"},
            {"REGION": "region"},
            False,
        )

        # Verify that client.run_test was called
        assert client_mock.run_test.called, "client.run_test was not called"

        # Now verify that update_live_display was called
        assert update_mock.call_count > 0, "update_live_display was not called"


def test_run_test_verbose_triggers_render_logs(mocker):
    """Test that run_test with verbose=True triggers the render_reponse_and_logs method."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a separate handler instance for this test
        handler = RunHandler()

        # Set up test logs to be returned by our mock
        test_logs = [
            {
                "test_name": "Test Name",
                "test_response": {"response": {"text": "Test response"}},
                "test_logs": "Test logs",
            }
        ]

        # Create a CLIClient mock with a prepared run_test method
        client_mock = mocker.MagicMock()

        # Have the client.run_test method call the callback directly
        def fake_run_test(*args, **kwargs):
            # Directly call the callback function with test data
            # The callback is the 9th positional argument (index 8)
            if len(args) > 8:
                callback = args[8]
                # Call the callback with some test data
                callback(
                    "Test Name",
                    {"response": {"text": "Test response"}},
                    200,
                    "TEST_CASE_COMPLETED",
                    True,  # verbose=True
                )
            return test_logs

        client_mock.run_test.side_effect = fake_run_test

        # This will replace the CLIClient constructor with our mock
        # Save the patch reference for later verification
        client_patch = mocker.patch("weni_cli.commands.run.CLIClient", return_value=client_mock)

        # Mock the Live context manager
        live_context = mocker.MagicMock()
        live_mock = mocker.MagicMock()
        live_context.__enter__.return_value = live_mock
        mocker.patch("rich.live.Live", return_value=live_context)

        # Mock render_reponse_and_logs for verification
        render_mock = mocker.patch.object(handler, "render_reponse_and_logs")

        # Call the handler method to be tested with verbose=True
        handler.run_test(
            "project_uuid",
            {"test": "definition"},
            b"tool_folder",
            "Tool Name",
            "Agent Name",
            {"test": "test_definition"},
            {"API_KEY": "key"},
            {"REGION": "region"},
            True,  # verbose=True
        )

        # Verify client constructor was called
        assert client_patch.called, "CLIClient constructor not called"

        # Verify render_reponse_and_logs was called with the test logs
        render_mock.assert_called_once_with(test_logs)


def test_parse_agent_tool_with_out_of_bounds_index():
    """Test parse_agent_tool method with an index error."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()
        # This generates an index error when trying to access [1]
        agent_key, tool_key = handler.parse_agent_tool("agent")
        assert agent_key is None
        assert tool_key is None


def test_display_test_results_comprehensive(mocker):
    """Comprehensive test for the display_test_results method after extraction."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock Table and its instance methods
        table_mock = mocker.MagicMock()
        mocker.patch("weni_cli.commands.run.Table", return_value=table_mock)

        # Test with empty rows
        result = handler.display_test_results([], "Test Tool")
        assert result is None

        # Test with various rows
        rows = [
            {"name": "Test 1", "status": 200, "response": "Response 1", "code": "TEST_CASE_COMPLETED"},
            {"name": "Test 2", "status": 400, "response": "Response 2", "code": "TEST_CASE_COMPLETED"},
            {"name": "Test 3", "status": 0, "response": None, "code": "TEST_CASE_RUNNING"},
        ]

        # Mock the format_response_for_display method to return a known value
        mocker.patch.object(
            handler, "format_response_for_display", side_effect=lambda response: f"Formatted: {response}"
        )

        # Call the method
        result = handler.display_test_results(rows, "Test Tool")

        # Verify table creation
        assert result == table_mock
        assert table_mock.add_column.call_count == 3
        assert table_mock.add_row.call_count == 3

        # Check column titles
        column_calls = table_mock.add_column.call_args_list
        assert column_calls[0][0][0] == "Test Name"
        assert column_calls[1][0][0] == "Status"
        assert column_calls[2][0][0] == "Response"

        # Verify table row content
        row_calls = table_mock.add_row.call_args_list
        assert row_calls[0][0][0] == "Test 1"  # Test name
        assert row_calls[0][0][1] == "✅"  # Status icon for success
        assert row_calls[0][0][2] == "Formatted: Response 1"  # Formatted response

        assert row_calls[1][0][0] == "Test 2"  # Test name
        assert row_calls[1][0][1] == "❌"  # Status icon for error

        assert row_calls[2][0][0] == "Test 3"  # Test name
        assert row_calls[2][0][1] == "⏳"  # Running icon for in-progress


def test_update_live_display_add_new_row(mocker):
    """Test update_live_display method when adding a new row."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock the live display
        live_mock = mocker.MagicMock()

        # Mock the display_test_results method
        display_mock = mocker.patch.object(handler, "display_test_results", return_value="Test Table")

        # Initial empty test rows
        test_rows = []

        # Call the method to add a new row
        handler.update_live_display(
            test_rows=test_rows,
            test_name="Test 1",
            test_result="Response 1",
            status_code=200,
            code="TEST_CASE_COMPLETED",
            live_display=live_mock,
            tool_name="Test Tool",
        )

        # Verify the row was added to test_rows
        assert len(test_rows) == 1
        assert test_rows[0]["name"] == "Test 1"
        assert test_rows[0]["status"] == 200
        assert test_rows[0]["response"] == "Response 1"
        assert test_rows[0]["code"] == "TEST_CASE_COMPLETED"

        # Verify that the display method was called correctly
        display_mock.assert_called_once_with(test_rows, "Test Tool", False)

        # Verify that the live display was updated
        live_mock.update.assert_called_once_with("Test Table", refresh=True)


def test_update_live_display_update_existing_row(mocker):
    """Test update_live_display method when updating an existing row."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Mock the live display
        live_mock = mocker.MagicMock()

        # Mock the display_test_results method
        display_mock = mocker.patch.object(handler, "display_test_results", return_value="Test Table")

        # Initial test rows with an existing row
        test_rows = [{"name": "Test 1", "status": 200, "response": "Initial Response", "code": "TEST_CASE_RUNNING"}]

        # Call the method to update the existing row
        handler.update_live_display(
            test_rows=test_rows,
            test_name="Test 1",  # Same name as existing row
            test_result="Updated Response",
            status_code=400,
            code="TEST_CASE_COMPLETED",
            live_display=live_mock,
            tool_name="Test Tool",
        )

        # Verify the row was updated in test_rows
        assert len(test_rows) == 1  # Still just one row
        assert test_rows[0]["name"] == "Test 1"
        assert test_rows[0]["status"] == 400  # Updated status
        assert test_rows[0]["response"] == "Updated Response"  # Updated response
        assert test_rows[0]["code"] == "TEST_CASE_COMPLETED"  # Updated code

        # Verify that the display method was called correctly
        display_mock.assert_called_once_with(test_rows, "Test Tool", False)

        # Verify that the live display was updated
        live_mock.update.assert_called_once_with("Test Table", refresh=True)


def test_execute_with_none_test_definition(mocker, mock_store_values):
    """Test the execute method when test_definition fails to load"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        handler = RunHandler()

        # Use the fixture to mock Store.get to return a project UUID
        mock_store_values(mocker, project_uuid="mock-project-uuid")

        # Create a realistic definition with the expected agent and tool structure
        definition_data = {
            "agents": {"test_agent": {"tools": [{"test_tool": {"source": {"path": "tools/test_tool"}}}]}}
        }

        # Mock load_agent_definition to return our definition data the first time (for the agent definition)
        # and None for the test definition
        mock_load_agent_definition = mocker.patch("weni_cli.commands.run.load_agent_definition")
        mock_load_agent_definition.return_value = (definition_data, None)

        # Mock load_test_definition to return None with an error
        mock_load_test_definition = mocker.patch("weni_cli.commands.run.load_test_definition")
        mock_load_test_definition.return_value = (None, "Error loading test definition")

        # Mock format_definition to return a formatted definition with the same structure
        formatted_definition = {
            "agents": {"test_agent": {"tools": [{"key": "test_tool", "source": {"path": "tools/test_tool"}}]}}
        }
        mocker.patch("weni_cli.commands.run.format_definition", return_value=(formatted_definition, None))

        # Mock load_tool_folder to return a mock tool folder
        load_tool_folder_mock = mocker.patch.object(handler, "load_tool_folder")
        load_tool_folder_mock.return_value = (b"mock_tool_folder_content", None)

        # Spy on methods that should not be called if we exit early
        get_tool_source_path_spy = mocker.spy(handler, "get_tool_source_path")

        # Call execute with arguments that will lead to loading test_definition
        result = handler.execute(
            definition="path/to/definition.json",
            agent_key="test_agent",
            tool_key="test_tool",
            test_definition="path/to/test_definition.json",
            verbose=False,
        )
        # Assert that the method returned None (early exit)
        assert result is None

        # Verify load_agent_definition was called once for definition_path
        assert mock_load_agent_definition.call_count == 1

        # Verify load_test_definition was called once for the test definition path
        assert mock_load_test_definition.call_count == 1
        assert mock_load_test_definition.call_args[0][0] == "path/to/test_definition.json"

        # Verify that load_tool_folder was called
        assert load_tool_folder_mock.called

        # Verify that get_tool_source_path was NOT called since we should exit early
        assert not get_tool_source_path_spy.called


def test_run_command_unhandled_exception(mocker, create_mocked_files, mock_store_values):
    """Test running a command with an unhandled exception."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_mocked_files()
        mock_store_values(mocker)

        # Mock RunHandler.execute to raise an exception
        mock_execute = mocker.patch("weni_cli.commands.run.RunHandler.execute")
        mock_execute.side_effect = Exception("Unhandled test exception")

        # Run the command and expect the exception to be caught and printed
        result = runner.invoke(cli, ["run", agent_file, "get_address", "get_address"])

        # Verify the command output
        assert result.exit_code == 0  # CLI commands return 0 when error is handled
        assert "Error: Unhandled test exception" in result.output

        # Verify the execute method was called with the correct arguments
        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        assert kwargs["definition"] == agent_file
        assert kwargs["agent_key"] == "get_address"
        assert kwargs["tool_key"] == "get_address"
        assert kwargs["test_definition"] is None
        assert kwargs["verbose"] is False


def test_project_push_command_unhandled_exception(mocker):
    """Test project push command with an unhandled exception."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a dummy definition file
        with open("agents.yaml", "w") as f:
            f.write("agents: {}")

        # Mock ProjectPushHandler.execute to raise an exception
        mock_execute = mocker.patch("weni_cli.commands.project_push.ProjectPushHandler.execute")
        mock_execute.side_effect = Exception("Unhandled project push exception")

        # Run the command and expect the exception to be caught and printed
        result = runner.invoke(cli, ["project", "push", "agents.yaml"])

        # Verify the command output
        assert result.exit_code == 0  # CLI commands return 0 when error is handled
        assert "Error: Unhandled project push exception" in result.output

        # Verify the execute method was called with the correct arguments
        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        assert kwargs["definition"] == "agents.yaml"
        assert kwargs["force_update"] is False


def test_run_command_invalid_format_definition(mocker, create_mocked_files, mock_store_values, mock_tool_folder):
    """Test running a command when format_definition returns None."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        agent_file = create_mocked_files()
        _ = mock_store_values(mocker)  # Project UUID is saved in the mock
        mock_tool_folder(mocker)

        # Mock load_agent_definition to return valid data
        mocker.patch(
            "weni_cli.validators.definition.load_agent_definition",
            return_value=({"agents": {"get_address": {"description": "Test", "tools": []}}}, None),
        )

        # Patch the load_default_test_definition to return a valid file
        mocker.patch.object(
            RunHandler, "load_default_test_definition", return_value="tools/get_address/test_definition.yaml"
        )

        # Patch the format_definition to return None
        mocker.patch("weni_cli.commands.run.format_definition", return_value=None)

        result = runner.invoke(cli, ["run", agent_file, "get_address", "get_address"])

        assert result.exit_code == 0
