import io
import json

import pytest

from weni_cli.clients.cli_client import (
    CLIClient,
    DEFAULT_BASE_URL,
    create_default_payload,
    get_toolkit_version,
)
from weni_cli.clients.response_handlers import process_push_display_step, process_test_progress
from weni_cli.store import STORE_CLI_BASE_URL, STORE_PROJECT_UUID_KEY, STORE_TOKEN_KEY


@pytest.fixture
def mock_store(mocker):
    """Mock the Store class to return predefined values."""

    def _mock(token="test-token", base_url=DEFAULT_BASE_URL, project_uuid="test-project-uuid"):
        def side_effect(key, default=None):
            if key == STORE_TOKEN_KEY:
                return token
            elif key == STORE_CLI_BASE_URL:
                return base_url
            elif key == STORE_PROJECT_UUID_KEY:
                return project_uuid
            return default

        mocker.patch("weni_cli.clients.cli_client.Store.get", side_effect=side_effect)
        return token, base_url, project_uuid

    return _mock


@pytest.fixture
def client(mock_store):
    """Create a CLIClient instance with mocked store."""
    mock_store()
    return CLIClient()


@pytest.fixture
def mock_toolkit_version(mocker):
    """Mock the get_toolkit_version function."""

    def _mock(version="0.3.0"):
        mocker.patch("weni_cli.clients.cli_client.get_toolkit_version", return_value=version)
        return version

    return _mock


def test_init_with_default_values(mock_store):
    """Test initialization with default values."""
    token, base_url, project_uuid = mock_store()
    client = CLIClient()

    assert client.headers == {
        "Authorization": f"Bearer {token}",
        "X-Project-Uuid": project_uuid,
    }
    assert client.base_url == base_url


def test_init_with_custom_values(mock_store):
    """Test initialization with custom values."""
    token, base_url, project_uuid = mock_store(
        token="custom-token", base_url="https://custom.cli.example.com", project_uuid="custom-project-uuid"
    )
    client = CLIClient()

    assert client.headers == {
        "Authorization": f"Bearer {token}",
        "X-Project-Uuid": project_uuid,
    }
    assert client.base_url == base_url


def test_get_toolkit_version(mocker):
    """Test getting the toolkit version."""
    # Mock importlib.metadata.version to return a fixed version
    mocker.patch("importlib.metadata.version", return_value="0.3.0")
    mock_echo = mocker.patch("rich_click.echo")

    version = get_toolkit_version()

    assert version == "0.3.0"
    mock_echo.assert_called_once_with("Using toolkit version: 0.3.0")


def test_create_default_payload(mock_toolkit_version):
    """Test creating default payload."""
    version = mock_toolkit_version()
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}

    payload = create_default_payload(project_uuid, definition)

    assert payload["project_uuid"] == project_uuid
    assert payload["definition"] == json.dumps(definition)
    assert payload["toolkit_version"] == version


def test_process_push_display_step():
    """Test the process_push_display_step function with various inputs."""
    # Test with None
    result = process_push_display_step(None)
    assert result is None

    # Test with empty dict
    result = process_push_display_step({})
    assert result is None

    # Test with success=False but no message
    result = process_push_display_step({"success": False})
    assert result == "Unknown error while pushing agents"

    # Test with success=True and message
    result = process_push_display_step({"success": True, "message": "Test message"})
    assert result == "Test message."


def test_process_test_progress_none_response(mocker):
    """Test the process_test_progress function with None response."""
    mock_echo = mocker.patch("rich_click.echo")

    result = process_test_progress(None, True)
    assert result is None
    assert not mock_echo.called


def test_process_test_progress_empty_response(mocker):
    """Test the process_test_progress function with empty response."""
    mock_echo = mocker.patch("rich_click.echo")

    result = process_test_progress({}, True)
    assert result is None
    assert not mock_echo.called


def test_process_test_progress_success_false_no_message(mocker):
    """Test the process_test_progress function with success=False and no message."""
    mock_echo = mocker.patch("rich_click.echo")

    result = process_test_progress({"success": False}, True)
    assert result is None
    mock_echo.assert_called_once_with("Unknown error while running test")


def test_process_test_progress_success_false_with_message(mocker):
    """Test the process_test_progress function with success=False and message."""
    mock_echo = mocker.patch("rich_click.echo")

    result = process_test_progress({"success": False, "message": "Error message", "request_id": "12345"}, True)
    assert result is None
    mock_echo.assert_any_call("Error message")
    mock_echo.assert_any_call("Request ID: 12345")


def test_process_test_progress_message_only(mocker):
    """Test the process_test_progress function with a message but no test case code."""
    mock_echo = mocker.patch("rich_click.echo")

    resp = {"success": True, "message": "Status message", "code": "OTHER_CODE"}
    result = process_test_progress(resp, True)
    assert result is None
    mock_echo.assert_called_once_with("Status message")


def test_process_test_progress_test_case_verbose():
    """Test the process_test_progress function with test case and verbose mode."""
    test_response = {"response": {"text": "Test response"}}
    resp = {
        "success": True,
        "code": "TEST_CASE_RUNNING",
        "data": {"test_case": "Test 1", "test_status_code": 200, "test_response": test_response, "logs": "Test logs"},
    }

    result = process_test_progress(resp, True)

    assert result["test_name"] == "Test 1"
    assert result["test_status_code"] == 200
    assert result["test_response"] == test_response
    assert result["test_logs"] == "Test logs"


def test_process_test_progress_test_case_non_verbose():
    """Test the process_test_progress function with test case and non-verbose mode."""
    test_response = {"response": {"text": "Test response"}}
    resp = {
        "success": True,
        "code": "TEST_CASE_COMPLETED",
        "data": {"test_case": "Test 1", "test_status_code": 200, "test_response": test_response, "logs": "Test logs"},
    }

    result = process_test_progress(resp, False)

    assert result["test_name"] == "Test 1"
    assert result["test_status_code"] == 200
    assert result["test_response"] == test_response
    assert "test_logs" not in result


def test_push_agents_success(client, requests_mock, mocker):
    """Test successful pushing of agents."""
    # Mock the progressbar and spinner to avoid display issues in tests
    mock_progressbar = mocker.patch("rich_click.progressbar")
    progress_instance = mocker.MagicMock()
    mock_progressbar.return_value.__enter__.return_value = progress_instance
    mocker.patch("weni_cli.clients.cli_client.spinner")

    # Mock the response content with a success response and 100% progress
    response_content = [
        json.dumps({"success": True, "message": "Processing agents", "progress": 0.5}),
        json.dumps({"success": True, "message": "Agents pushed successfully", "progress": 1.0}),
    ]
    requests_mock.post(f"{client.base_url}/api/v1/agents", content="\n".join(response_content).encode("utf-8"))

    # Create test data
    project_uuid = "test-project-uuid"
    agents_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folders = {"test_skill": io.BytesIO(b"test skill content")}

    # Call the method
    client.push_agents(project_uuid, agents_definition, skill_folders)

    # Verify the request
    assert requests_mock.last_request is not None
    assert requests_mock.last_request.headers["Authorization"] == client.headers["Authorization"]
    assert requests_mock.last_request.headers["X-Project-Uuid"] == client.headers["X-Project-Uuid"]

    # Verify progressbar was updated
    assert progress_instance.update.call_count == 2


def test_push_agents_error_response(client, requests_mock, mocker):
    """Test pushing agents with error in response."""
    # Mock the progressbar and spinner
    mock_progressbar = mocker.patch("rich_click.progressbar")
    progress_instance = mocker.MagicMock()
    mock_progressbar.return_value.__enter__.return_value = progress_instance
    mocker.patch("weni_cli.clients.cli_client.spinner")

    # Mock the response content with an error message
    response_content = [json.dumps({"success": False, "message": "Error pushing agents", "request_id": "12345"})]
    requests_mock.post(f"{client.base_url}/api/v1/agents", content="\n".join(response_content).encode("utf-8"))

    # Create test data
    project_uuid = "test-project-uuid"
    agents_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folders = {"test_skill": io.BytesIO(b"test skill content")}

    # Call the method and expect exception
    with pytest.raises(Exception) as exc_info:
        client.push_agents(project_uuid, agents_definition, skill_folders)

    # Verify the exception message
    assert "Error pushing agents" in str(exc_info.value)
    assert "Request ID: 12345" in str(exc_info.value)


def test_push_agents_error_no_message(client, mocker):
    """Test pushing agents with error but no message."""
    # Mock the Session class and post method
    mock_session = mocker.MagicMock()
    mock_post = mocker.MagicMock()
    mock_session.post.return_value = mock_post

    # Mock response from post method
    mock_post.status_code = 200
    mock_post.__enter__.return_value = mock_post
    mock_post.iter_lines.return_value = [json.dumps({"success": False}).encode("utf-8")]

    # Mock Session class to return our mock session
    mocker.patch("requests.Session", return_value=mock_session)

    # Mock progressbar and spinner
    mock_progressbar = mocker.patch("rich_click.progressbar")
    mock_progress_context = mocker.MagicMock()
    mock_progressbar.return_value.__enter__.return_value = mock_progress_context
    mocker.patch("weni_cli.clients.cli_client.spinner")

    # Create test data
    project_uuid = "test-project-uuid"
    agents_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folders = {"test_skill": io.BytesIO(b"test skill content")}

    # Call the method and expect exception
    with pytest.raises(Exception) as exc_info:
        client.push_agents(project_uuid, agents_definition, skill_folders)

    # Verify the session.post call
    mock_session.post.assert_called_once()
    assert "Failed to push agents" in str(exc_info.value)


def test_push_agents_http_error(client, requests_mock, mocker):
    """Test pushing agents with HTTP error."""
    # Mock the spinner
    mocker.patch("weni_cli.clients.cli_client.spinner")

    # Mock the response with an error status code
    requests_mock.post(f"{client.base_url}/api/v1/agents", status_code=500, text="Internal Server Error")

    # Create test data
    project_uuid = "test-project-uuid"
    agents_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folders = {"test_skill": io.BytesIO(b"test skill content")}

    # Call the method and expect exception
    with pytest.raises(Exception) as exc_info:
        client.push_agents(project_uuid, agents_definition, skill_folders)

    # Verify the exception message
    assert "Failed to push agents" in str(exc_info.value)
    assert "Internal Server Error" in str(exc_info.value)


def test_run_test_success(client, requests_mock, mocker):
    """Test successful test run."""
    # Mock the callback function
    result_callback = mocker.Mock()

    # Mock the response content with test case responses
    response_content = [
        json.dumps(
            {
                "success": True,
                "code": "TEST_CASE_RUNNING",
                "data": {
                    "test_case": "Test 1",
                    "test_status_code": 200,
                    "test_response": {"response": {"text": "Test response"}},
                    "logs": "Test logs",
                },
            }
        ),
        json.dumps(
            {
                "success": True,
                "code": "TEST_CASE_COMPLETED",
                "data": {
                    "test_case": "Test 1",
                    "test_status_code": 200,
                    "test_response": {"response": {"text": "Final response"}},
                    "logs": "Final logs",
                },
            }
        ),
    ]
    requests_mock.post(f"{client.base_url}/api/v1/runs", content="\n".join(response_content).encode("utf-8"))

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folder = io.BytesIO(b"test skill content")
    skill_name = "Test Skill"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    skill_globals = {"REGION": "us-east-1"}

    # Call the method
    test_logs = client.run_test(
        project_uuid,
        definition,
        skill_folder,
        skill_name,
        agent_name,
        test_definition,
        credentials,
        skill_globals,
        result_callback,
        verbose=True,
    )

    # Verify the request
    assert requests_mock.last_request is not None
    assert requests_mock.last_request.headers["Authorization"] == client.headers["Authorization"]
    assert requests_mock.last_request.headers["X-Project-Uuid"] == client.headers["X-Project-Uuid"]

    # Verify the test logs were collected (verbose=True)
    assert len(test_logs) == 2
    assert test_logs[0]["test_name"] == "Test 1"
    assert test_logs[0]["test_status_code"] == 200
    assert test_logs[0]["test_logs"] == "Test logs"
    assert test_logs[1]["test_logs"] == "Final logs"

    # Verify the callback was called
    assert result_callback.call_count == 2
    result_callback.assert_any_call("Test 1", {"response": {"text": "Test response"}}, 200, "TEST_CASE_RUNNING", True)


def test_run_test_non_verbose(client, requests_mock, mocker):
    """Test running a test without verbose mode."""
    # Mock the callback function
    result_callback = mocker.Mock()

    # Mock the response content with a test case response
    response_content = [
        json.dumps(
            {
                "success": True,
                "code": "TEST_CASE_COMPLETED",
                "data": {
                    "test_case": "Test 1",
                    "test_status_code": 200,
                    "test_response": {"response": {"text": "Test response"}},
                    "logs": "Test logs",
                },
            }
        )
    ]
    requests_mock.post(f"{client.base_url}/api/v1/runs", content="\n".join(response_content).encode("utf-8"))

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folder = io.BytesIO(b"test skill content")
    skill_name = "Test Skill"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    skill_globals = {"REGION": "us-east-1"}

    # Call the method with verbose=False
    test_logs = client.run_test(
        project_uuid,
        definition,
        skill_folder,
        skill_name,
        agent_name,
        test_definition,
        credentials,
        skill_globals,
        result_callback,
        verbose=False,
    )

    # Verify the test logs are empty (verbose=False)
    assert test_logs == []

    # Verify the callback was called
    assert result_callback.call_count == 1
    result_callback.assert_called_once_with(
        "Test 1", {"response": {"text": "Test response"}}, 200, "TEST_CASE_COMPLETED", False
    )


def test_run_test_error_message(client, requests_mock, mocker):
    """Test running a test with error message in response."""
    # Mock echo and callback
    mock_echo = mocker.patch("rich_click.echo")
    result_callback = mocker.Mock()

    # Mock the response content with an error message
    response_content = [json.dumps({"success": False, "message": "Error running test", "request_id": "12345"})]
    requests_mock.post(f"{client.base_url}/api/v1/runs", content="\n".join(response_content).encode("utf-8"))

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folder = io.BytesIO(b"test skill content")
    skill_name = "Test Skill"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    skill_globals = {"REGION": "us-east-1"}

    # Call the method
    test_logs = client.run_test(
        project_uuid,
        definition,
        skill_folder,
        skill_name,
        agent_name,
        test_definition,
        credentials,
        skill_globals,
        result_callback,
        verbose=True,
    )

    # Verify echo was called with error message
    mock_echo.assert_any_call("Error running test")
    mock_echo.assert_any_call("Request ID: 12345")

    # Verify test logs are empty
    assert test_logs == []

    # Verify the callback was not called with test results
    result_callback.assert_not_called()


def test_run_test_http_error(client, requests_mock, mocker):
    """Test running a test with HTTP error."""
    # Mock the callback
    result_callback = mocker.Mock()

    # Mock the response with an error status code
    requests_mock.post(f"{client.base_url}/api/v1/runs", status_code=500, text="Internal Server Error")

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folder = io.BytesIO(b"test skill content")
    skill_name = "Test Skill"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    skill_globals = {"REGION": "us-east-1"}

    # Call the method and expect exception
    with pytest.raises(Exception) as exc_info:
        client.run_test(
            project_uuid,
            definition,
            skill_folder,
            skill_name,
            agent_name,
            test_definition,
            credentials,
            skill_globals,
            result_callback,
            verbose=True,
        )

    # Verify the exception message
    assert "Failed to run test" in str(exc_info.value)
    assert "Internal Server Error" in str(exc_info.value)


def test_run_test_unknown_error(client, requests_mock, mocker):
    """Test running a test with unknown error in response."""
    # Mock echo and callback
    mock_echo = mocker.patch("rich_click.echo")
    result_callback = mocker.Mock()

    # Mock the response content with a success=False but no message
    response_content = [
        json.dumps(
            {
                "success": False
                # No message or other data
            }
        )
    ]
    requests_mock.post(f"{client.base_url}/api/v1/runs", content="\n".join(response_content).encode("utf-8"))

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folder = io.BytesIO(b"test skill content")
    skill_name = "Test Skill"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    skill_globals = {"REGION": "us-east-1"}

    # Call the method
    test_logs = client.run_test(
        project_uuid,
        definition,
        skill_folder,
        skill_name,
        agent_name,
        test_definition,
        credentials,
        skill_globals,
        result_callback,
        verbose=True,
    )

    # Verify echo was called with unknown error message
    mock_echo.assert_any_call("Unknown error while running test")

    # Verify test logs are empty
    assert test_logs == []


def test_run_test_success_false_no_message(client, requests_mock, mocker):
    """Test running a test with success=False but no message."""
    # Mock echo
    mock_echo = mocker.patch("rich_click.echo")
    result_callback = mocker.Mock()

    # Mock the response content with success=False but no message
    response_content = [
        json.dumps(
            {
                "success": False
                # No message
            }
        )
    ]
    requests_mock.post(f"{client.base_url}/api/v1/runs", content="\n".join(response_content).encode("utf-8"))

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    skill_folder = io.BytesIO(b"test skill content")
    skill_name = "Test Skill"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    skill_globals = {"REGION": "us-east-1"}

    # Call the method
    test_logs = client.run_test(
        project_uuid,
        definition,
        skill_folder,
        skill_name,
        agent_name,
        test_definition,
        credentials,
        skill_globals,
        result_callback,
        verbose=True,
    )

    # Verify echo was called with unknown error message
    mock_echo.assert_any_call("Unknown error while running test")

    # Verify test logs are empty
    assert test_logs == []
