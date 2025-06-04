import io
import json

import pytest
from contextlib import contextmanager

from weni_cli.clients.cli_client import (
    CLIClient,
    DEFAULT_BASE_URL,
    create_default_payload,
    get_cli_version,
    get_toolkit_version,
    RequestError,
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


# Mock for streaming request context manager
@pytest.fixture
def mock_streaming_request(mocker, client):
    """Mock the _streaming_request context manager."""

    @contextmanager
    def mock_cm(*args, **kwargs):
        mock_response = mocker.MagicMock()
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_cm)
    return client


def test_init_with_default_values(mock_store):
    """Test initialization with default values."""
    token, base_url, project_uuid = mock_store()
    client = CLIClient()

    assert client.headers == {
        "Authorization": f"Bearer {token}",
        "X-Project-Uuid": project_uuid,
        "X-CLI-Version": get_cli_version(),
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
        "X-CLI-Version": get_cli_version(),
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
    agent_type = "passive"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}

    payload = create_default_payload(project_uuid, definition, agent_type)

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

    # Mock the streaming_request context manager
    mock_response = mocker.MagicMock()
    mock_response.iter_lines.return_value = [
        json.dumps({"success": True, "message": "Processing agents", "progress": 0.5}).encode("utf-8"),
        json.dumps({"success": True, "message": "Agents pushed successfully", "progress": 1.0}).encode("utf-8"),
    ]

    # Create a mock for the context manager
    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    agents_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folders = {"test_tool": io.BytesIO(b"test tool content")}
    agent_type = "passive"

    # Call the method
    client.push_agents(project_uuid, agents_definition, tool_folders, agent_type)

    # Verify progressbar was updated
    assert progress_instance.update.call_count == 2


def test_push_agents_error_response(client, mocker):
    """Test pushing agents with error in response."""
    # Mock the progressbar and spinner
    mock_progressbar = mocker.patch("rich_click.progressbar")
    progress_instance = mocker.MagicMock()
    mock_progressbar.return_value.__enter__.return_value = progress_instance
    mocker.patch("weni_cli.clients.cli_client.spinner")

    # Mock the streaming_request context manager
    mock_response = mocker.MagicMock()
    mock_response.iter_lines.return_value = [
        json.dumps({"success": False, "message": "Error pushing agents", "request_id": "12345"}).encode("utf-8")
    ]

    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    agents_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folders = {"test_tool": io.BytesIO(b"test tool content")}
    agent_type = "passive"

    # Call the method and expect exception
    with pytest.raises(RequestError) as exc_info:
        client.push_agents(project_uuid, agents_definition, tool_folders, agent_type)

    # Verify the exception message
    assert "Error pushing agents" in str(exc_info.value)
    assert "Request ID: 12345" in str(exc_info.value)


def test_push_agents_error_no_message(client, mocker):
    """Test pushing agents with error but no message."""
    # Mock the progressbar and spinner
    mock_progressbar = mocker.patch("rich_click.progressbar")
    progress_instance = mocker.MagicMock()
    mock_progressbar.return_value.__enter__.return_value = progress_instance
    mocker.patch("weni_cli.clients.cli_client.spinner")

    # Mock the streaming_request context manager
    mock_response = mocker.MagicMock()
    mock_response.iter_lines.return_value = [json.dumps({"success": False}).encode("utf-8")]

    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    agents_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folders = {"test_tool": io.BytesIO(b"test tool content")}
    agent_type = "passive"
    # Call the method and expect exception
    with pytest.raises(RequestError) as exc_info:
        client.push_agents(project_uuid, agents_definition, tool_folders, agent_type)

    # Verify the exception message
    assert "Unknown error during agent push" in str(exc_info.value)


def test_push_agents_http_error(client, mocker):
    """Test pushing agents with HTTP error."""
    # Mock the spinner
    mocker.patch("weni_cli.clients.cli_client.spinner")

    # Mock the streaming_request to raise an exception
    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        raise RequestError("Request failed with status code 500: Internal Server Error", status_code=500)

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    agents_definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folders = {"test_tool": io.BytesIO(b"test tool content")}
    agent_type = "passive"
    # Call the method and expect exception
    with pytest.raises(RequestError) as exc_info:
        client.push_agents(project_uuid, agents_definition, tool_folders, agent_type)

    # Verify the exception
    assert "500" in str(exc_info.value)
    assert "Internal Server Error" in str(exc_info.value)


def test_run_test_success(client, mocker):
    """Test successful test run."""
    # Mock the callback function
    result_callback = mocker.Mock()

    # Define the expected test responses
    test_response_1 = {"response": {"text": "Test response"}}
    test_response_2 = {"response": {"text": "Final response"}}

    # Mock the streaming_request context manager
    mock_response = mocker.MagicMock()
    mock_response.iter_lines.return_value = [
        json.dumps(
            {
                "success": True,
                "code": "TEST_CASE_RUNNING",
                "data": {
                    "test_case": "Test 1",
                    "test_status_code": 200,
                    "test_response": test_response_1,
                    "logs": "Test logs",
                },
            }
        ).encode("utf-8"),
        json.dumps(
            {
                "success": True,
                "code": "TEST_CASE_COMPLETED",
                "data": {
                    "test_case": "Test 1",
                    "test_status_code": 200,
                    "test_response": test_response_2,
                    "logs": "Final logs",
                },
            }
        ).encode("utf-8"),
    ]

    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folder = io.BytesIO(b"test tool content")
    tool_name = "Test Tool"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    tool_globals = {"REGION": "us-east-1"}
    agent_type = "passive"

    # Call the method
    test_logs = client.run_test(
        project_uuid,
        definition,
        tool_folder,
        tool_name,
        agent_name,
        test_definition,
        credentials,
        tool_globals,
        agent_type,
        result_callback,
        verbose=True,
    )

    # Verify the test logs were collected (verbose=True)
    assert len(test_logs) == 2
    assert test_logs[0]["test_name"] == "Test 1"
    assert test_logs[0]["test_status_code"] == 200
    assert test_logs[0]["test_response"] == test_response_1
    assert test_logs[1]["test_logs"] == "Final logs"

    # Verify the callback was called
    assert result_callback.call_count == 2
    result_callback.assert_any_call("Test 1", test_response_1, 200, "TEST_CASE_RUNNING", True)


def test_run_test_non_verbose(client, mocker):
    """Test running a test without verbose mode."""
    # Mock the callback function
    result_callback = mocker.Mock()

    # Mock the streaming_request context manager
    mock_response = mocker.MagicMock()
    mock_response.iter_lines.return_value = [
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
        ).encode("utf-8")
    ]

    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folder = io.BytesIO(b"test tool content")
    tool_name = "Test Tool"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    tool_globals = {"REGION": "us-east-1"}
    agent_type = "passive"
    # Call the method with verbose=False
    test_logs = client.run_test(
        project_uuid,
        definition,
        tool_folder,
        tool_name,
        agent_name,
        test_definition,
        credentials,
        tool_globals,
        agent_type,
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


def test_run_test_error_message(client, mocker):
    """Test running a test with error message in response."""
    # Mock echo and callback
    mock_echo = mocker.patch("rich_click.echo")
    result_callback = mocker.Mock()

    # Mock the streaming_request context manager
    mock_response = mocker.MagicMock()
    mock_response.iter_lines.return_value = [
        json.dumps({"success": False, "message": "Error running test", "request_id": "12345"}).encode("utf-8")
    ]

    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folder = io.BytesIO(b"test tool content")
    tool_name = "Test Tool"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    tool_globals = {"REGION": "us-east-1"}
    agent_type = "passive"

    # Call the method
    test_logs = client.run_test(
        project_uuid,
        definition,
        tool_folder,
        tool_name,
        agent_name,
        test_definition,
        credentials,
        tool_globals,
        agent_type,
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


def test_run_test_http_error(client, mocker):
    """Test running a test with HTTP error."""
    # Mock the callback
    result_callback = mocker.Mock()

    # Mock the streaming_request to raise an exception
    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        raise RequestError("Request failed with status code 500: Internal Server Error", status_code=500)

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folder = io.BytesIO(b"test tool content")
    tool_name = "Test Tool"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    tool_globals = {"REGION": "us-east-1"}
    agent_type = "passive"
    # Call the method and expect exception
    with pytest.raises(RequestError) as exc_info:
        client.run_test(
            project_uuid,
            definition,
            tool_folder,
            tool_name,
            agent_name,
            test_definition,
            credentials,
            tool_globals,
            agent_type,
            result_callback,
            verbose=True,
        )

    # Verify the exception message
    assert "Failed to run test" in str(exc_info.value)
    assert "500" in str(exc_info.value)


def test_run_test_unknown_error(client, mocker):
    """Test running a test with unknown error in response."""
    # Mock echo and callback
    mock_echo = mocker.patch("rich_click.echo")
    result_callback = mocker.Mock()

    # Mock the streaming_request context manager
    mock_response = mocker.MagicMock()
    mock_response.iter_lines.return_value = [json.dumps({"success": False}).encode("utf-8")]

    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folder = io.BytesIO(b"test tool content")
    tool_name = "Test Tool"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    tool_globals = {"REGION": "us-east-1"}
    agent_type = "passive"
    # Call the method
    test_logs = client.run_test(
        project_uuid,
        definition,
        tool_folder,
        tool_name,
        agent_name,
        test_definition,
        credentials,
        tool_globals,
        agent_type,
        result_callback,
        verbose=True,
    )

    # Verify echo was called with unknown error message
    mock_echo.assert_any_call("Unknown error while running test")

    # Verify test logs are empty
    assert test_logs == []


def test_run_test_success_false_no_message(client, mocker):
    """Test running a test with success=False but no message."""
    # Mock echo
    mock_echo = mocker.patch("rich_click.echo")
    result_callback = mocker.Mock()

    # Mock the streaming_request context manager
    mock_response = mocker.MagicMock()
    mock_response.iter_lines.return_value = [json.dumps({"success": False}).encode("utf-8")]

    @contextmanager
    def mock_streaming_request(*args, **kwargs):
        yield mock_response

    mocker.patch.object(client, "_streaming_request", mock_streaming_request)

    # Create test data
    project_uuid = "test-project-uuid"
    definition = {"agents": {"test_agent": {"name": "Test Agent"}}}
    tool_folder = io.BytesIO(b"test tool content")
    tool_name = "Test Tool"
    agent_name = "Test Agent"
    test_definition = {"test_cases": [{"name": "Test 1", "input": "Test input"}]}
    credentials = {"API_KEY": "test-key"}
    tool_globals = {"REGION": "us-east-1"}
    agent_type = "passive"
    # Call the method
    test_logs = client.run_test(
        project_uuid,
        definition,
        tool_folder,
        tool_name,
        agent_name,
        test_definition,
        credentials,
        tool_globals,
        agent_type,
        result_callback,
        verbose=True,
    )

    # Verify echo was called with unknown error message
    mock_echo.assert_any_call("Unknown error while running test")

    # Verify test logs are empty
    assert test_logs == []


def test_check_project_permission_success(client, mocker):
    """Test successful project permission check."""
    # Mock the make_request method
    mocker.patch.object(client, "_make_request", return_value=mocker.MagicMock(status_code=200))

    # Call the method - should not raise an exception
    project_uuid = "test-project-uuid"
    client.check_project_permission(project_uuid)

    # Verify the method was called with correct parameters
    client._make_request.assert_called_once_with(
        method="POST", endpoint="api/v1/permissions/verify", json_data={"project_uuid": project_uuid}
    )


def test_check_project_permission_failure(client, mocker):
    """Test failed project permission check."""
    # Mock the make_request method to raise RequestError
    error_message = "User does not have permission to access this project"
    mocker.patch.object(client, "_make_request", side_effect=RequestError(message=error_message, status_code=403))

    # Call the method and expect an exception
    project_uuid = "test-project-uuid"
    with pytest.raises(RequestError) as exc_info:
        client.check_project_permission(project_uuid)

    # Verify the exception message
    assert "Failed to check project permission" in str(exc_info.value)
    assert error_message in str(exc_info.value)


def test_check_project_permission_no_message(client, mocker):
    """Test project permission check with no message in response."""
    # Mock the make_request method to raise RequestError without a specific message
    mocker.patch.object(
        client,
        "_make_request",
        side_effect=RequestError(message="Request failed with status code 500", status_code=500),
    )

    # Call the method and expect an exception
    project_uuid = "test-project-uuid"
    with pytest.raises(RequestError) as exc_info:
        client.check_project_permission(project_uuid)

    # Verify the exception message
    assert "Failed to check project permission" in str(exc_info.value)
    assert "500" in str(exc_info.value)


def test_check_project_permission_network_error(client, mocker):
    """Test project permission check with network error."""
    # Mock the _make_request method to raise a ConnectionError that gets wrapped in RequestError
    mocker.patch.object(client, "_make_request", side_effect=RequestError("Connection refused"))

    # Call the method and expect an exception
    project_uuid = "test-project-uuid"
    with pytest.raises(RequestError) as exc_info:
        client.check_project_permission(project_uuid)

    # Verify the exception message
    assert "Failed to check project permission" in str(exc_info.value)
    assert "Connection refused" in str(exc_info.value)


def test_request_error_format_message():
    """Test the RequestError _format_message method with various parameters."""
    # Test with just a message
    error = RequestError("Test error")
    assert error._format_message() == "Test error"

    # Test with message and data
    error = RequestError("Test error", data={"key": "value"})
    assert error._format_message() == "Test error - Data: {'key': 'value'}"

    # Test with message and request_id
    error = RequestError("Test error", request_id="12345")
    assert error._format_message() == "Test error - Request ID: 12345"

    # Test with all parameters
    error = RequestError("Test error", data={"key": "value"}, request_id="12345")
    assert error._format_message() == "Test error - Data: {'key': 'value'} - Request ID: 12345"


def test_streaming_request_json_decode_error(client, requests_mock, mocker):
    """Test _streaming_request method with a JSON decode error."""
    # Mock the session.request method
    mock_response = mocker.MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Not a JSON response"
    # Ensure json.loads raises JSONDecodeError
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)

    client.session.request = mocker.MagicMock(return_value=mock_response)

    # Test with the context manager
    with pytest.raises(RequestError) as excinfo:
        with client._streaming_request("GET", "test/endpoint"):
            pass

    # Verify the error message format
    assert "Request failed with status code 500: Not a JSON response" in str(excinfo.value)


def test_request_method_error_handling(client, mocker):
    """Test _make_request method with various error responses."""
    # 1. Test with JSON error response
    json_error_resp = mocker.MagicMock()
    json_error_resp.status_code = 400
    json_error_resp.json.return_value = {
        "message": "Bad request",
        "data": {"field": "error"},
        "request_id": "req-12345",
    }

    client.session.request = mocker.MagicMock(return_value=json_error_resp)

    with pytest.raises(RequestError) as excinfo:
        client._make_request("GET", "test/endpoint")

    error = excinfo.value
    assert error.message == "Bad request"
    assert error.status_code == 400
    assert error.data == {"field": "error"}
    assert error.request_id == "req-12345"

    # 2. Test with non-JSON error response
    text_error_resp = mocker.MagicMock()
    text_error_resp.status_code = 500
    text_error_resp.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    text_error_resp.text = "Internal server error"

    client.session.request = mocker.MagicMock(return_value=text_error_resp)

    with pytest.raises(RequestError) as excinfo:
        client._make_request("GET", "test/endpoint")

    assert "Request failed with status code 500: Internal server error" in str(excinfo.value)

    # 3. Test with successful response
    success_resp = mocker.MagicMock()
    success_resp.status_code = 200
    success_resp.json.return_value = {"data": "success"}

    client.session.request = mocker.MagicMock(return_value=success_resp)

    response = client._make_request("GET", "test/endpoint")
    assert response == success_resp


def test_streaming_request_json_error_response(client, mocker):
    """Test _streaming_request method with a JSON error response."""
    # Mock the session.request method to return a JSON error
    mock_response = mocker.MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "message": "Bad request from streaming",
        "data": {"field": "stream_error"},
        "request_id": "stream-12345",
    }

    client.session.request = mocker.MagicMock(return_value=mock_response)

    # Test with the context manager
    with pytest.raises(RequestError) as excinfo:
        with client._streaming_request("GET", "test/endpoint"):
            pass

    # Verify the error properties
    error = excinfo.value
    assert error.message == "Bad request from streaming"
    assert error.status_code == 400
    assert error.data == {"field": "stream_error"}
    assert error.request_id == "stream-12345"

    # Ensure the session.request was called properly
    client.session.request.assert_called_once()
    call_args = client.session.request.call_args
    assert call_args[1]["stream"] is True


def test_streaming_request_successful_response(client, mocker):
    """Test _streaming_request method with a successful response."""
    # Mock the session.request method to return a successful response
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200

    client.session.request = mocker.MagicMock(return_value=mock_response)

    # Test with the context manager and ensure the response is yielded
    with client._streaming_request("GET", "test/endpoint") as response:
        assert response == mock_response

    # Ensure the session.request was called properly
    client.session.request.assert_called_once()
    call_args = client.session.request.call_args
    assert call_args[1]["stream"] is True


def test_run_test_verbose_with_callback(client, mocker):
    """Test run_test method with verbose=True and a callback."""
    # This test is a placeholder and can be implemented if needed
    pass


def test_get_tool_logs_success(client, mocker):
    """Test successful tool logs retrieval."""
    # Mock response data
    mock_logs_data = {
        "logs": [
            {"timestamp": "2023-01-01T12:00:00", "level": "INFO", "message": "Tool executed successfully"},
            {"timestamp": "2023-01-01T12:01:00", "level": "DEBUG", "message": "Processing data"}
        ]
    }
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = mock_logs_data

    # Mock the _make_request method
    mocker.patch.object(client, "_make_request", return_value=mock_response)

    # Call the method
    agent = "test-agent"
    tool = "test-tool"
    start_time = "2023-01-01T00:00:00"
    end_time = "2023-01-02T00:00:00"
    pattern = "success"

    logs, error = client.get_tool_logs(agent, tool, start_time, end_time, pattern)

    # Verify the results
    assert logs == mock_logs_data
    assert error is None

    # Verify the method was called with correct parameters
    client._make_request.assert_called_once_with(
        method="GET", endpoint="api/v1/tool-logs/",
        params={
            "agent_key": agent,
            "tool_key": tool,
            "start_time": start_time,
            "end_time": end_time,
            "pattern": pattern,
            "next_token": None,
        }
    )


def test_get_tool_logs_error(client, mocker):
    """Test tool logs retrieval with error."""
    # Mock the _make_request method to raise RequestError
    error_message = "Failed to fetch tool logs"
    request_id = "req-12345"
    mocker.patch.object(
        client,
        "_make_request",
        side_effect=RequestError(message=error_message, request_id=request_id)
    )

    # Call the method
    agent = "test-agent"
    tool = "test-tool"
    start_time = "2023-01-01T00:00:00"
    end_time = "2023-01-02T00:00:00"
    pattern = "error"

    logs, error = client.get_tool_logs(agent, tool, start_time, end_time, pattern)

    # Verify the results
    assert logs == {}
    assert error == f"Error fetching logs: {error_message} - Request ID: {request_id}"


def test_get_tool_logs_with_empty_times(client, mocker):
    """Test tool logs retrieval with empty start/end times."""
    # Mock response data
    mock_logs_data = {"logs": []}
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = mock_logs_data

    # Mock the _make_request method
    mocker.patch.object(client, "_make_request", return_value=mock_response)

    # Call the method with empty times
    agent = "test-agent"
    tool = "test-tool"
    start_time = ""
    end_time = None
    pattern = None

    logs, error = client.get_tool_logs(agent, tool, start_time, end_time, pattern)

    # Verify the results
    assert logs == mock_logs_data
    assert error is None

    # Verify the method was called with correct parameters (None values for times)
    client._make_request.assert_called_once_with(
        method="GET", endpoint="api/v1/tool-logs/",
        params={
            "agent_key": agent,
            "tool_key": tool,
            "start_time": None,
            "end_time": None,
            "pattern": pattern,
            "next_token": None,
        }
    )
