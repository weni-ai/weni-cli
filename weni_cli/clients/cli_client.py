import rich_click as click
import requests
import json
import importlib.metadata
from typing import Dict, List, Optional, Any, BinaryIO, Callable
from contextlib import contextmanager

from weni_cli.clients.common import ErrorMessage
from weni_cli.spinner import spinner
from weni_cli.store import STORE_CLI_BASE_URL, STORE_PROJECT_UUID_KEY, STORE_TOKEN_KEY, Store
from weni_cli.clients.response_handlers import process_push_display_step, process_test_progress

DEFAULT_BASE_URL = "https://cli.cloud.weni.ai"


class RequestError(Exception):
    """Custom exception for request-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        data: Optional[Dict] = None,
        request_id: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.data = data
        self.request_id = request_id
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        msg = self.message
        if self.data:
            msg += f" - Data: {self.data}"
        if self.request_id:
            msg += f" - Request ID: {self.request_id}"
        return msg


def get_toolkit_version() -> str:
    """Get the version of weni-agents-toolkit from metadata."""
    version = importlib.metadata.version("weni-agents-toolkit")
    click.echo(f"Using toolkit version: {version}")
    return version


def get_cli_version() -> str:
    """Get the version of weni-cli from metadata."""
    return importlib.metadata.version("weni-cli")


def create_default_payload(project_uuid: str, definition: Dict, agent_type: str) -> Dict[str, str]:
    """Create a default payload for API requests."""
    return {
        "project_uuid": project_uuid,
        "definition": json.dumps(definition),
        "toolkit_version": get_toolkit_version(),
        "type": agent_type,
    }


class CLIClient:
    """Client for interacting with the Weni CLI API."""

    def __init__(self):
        store = Store()
        self.headers = self._create_headers(store)
        # self.base_url = store.get(STORE_CLI_BASE_URL, DEFAULT_BASE_URL)
        self.base_url = "http://localhost:8000"
        self.session = requests.Session()

    def _create_headers(self, store: Store) -> Dict[str, str]:
        """Create headers for API requests."""
        return {
            "Authorization": f"Bearer {store.get(STORE_TOKEN_KEY)}",
            "X-Project-Uuid": store.get(STORE_PROJECT_UUID_KEY),
            "X-CLI-Version": get_cli_version(),
        }

    @contextmanager
    def _streaming_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        timeout: tuple = (10, None),
    ):
        """Make a streaming request to the API using a context manager for proper resource handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = None
        try:
            response = self.session.request(
                method=method, url=url, headers=self.headers, data=data, files=files, stream=True, timeout=timeout
            )

            if response.status_code != 200:
                if response.status_code == 401:
                    raise RequestError("Invalid authentication token. Please login again using 'weni login'")
                try:
                    error_data = response.json()
                    message = error_data.get("message", f"Request failed with status code {response.status_code}")
                    raise RequestError(
                        message=message,
                        status_code=response.status_code,
                        data=error_data.get("data"),
                        request_id=error_data.get("request_id"),
                    )
                except json.JSONDecodeError:
                    raise RequestError(f"Request failed with status code {response.status_code}: {response.text}")

            yield response

        finally:
            if response:
                response.close()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Any] = None,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: tuple = (10, None),
    ) -> requests.Response:
        """Make a non-streaming request to the API with error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = self.session.request(
            method=method,
            url=url,
            headers=self.headers,
            data=data,
            json=json_data,
            files=files,
            stream=False,
            timeout=timeout,
            params=params,
        )

        if response.status_code != 200:
            if response.status_code == 401:
                raise RequestError("Invalid authentication token. Please login again using 'weni login'")
            try:
                error_data = response.json()
                message = error_data.get("message", f"Request failed with status code {response.status_code}")
                raise RequestError(
                    message=message,
                    status_code=response.status_code,
                    data=error_data.get("data"),
                    request_id=error_data.get("request_id"),
                )
            except json.JSONDecodeError:
                raise RequestError(f"Request failed with status code {response.status_code}: {response.text}")

        return response

    def check_project_permission(self, project_uuid: str) -> None:
        """Check if the user has permission for the given project."""
        payload: dict = {"project_uuid": project_uuid}

        try:
            self._make_request(method="POST", endpoint="api/v1/permissions/verify", json_data=payload)
        except RequestError as e:
            raise RequestError(f"Failed to check project permission: {e.message}")

    def push_agents(
        self, project_uuid: str, agents_definition: Dict, resources_folder: Dict[str, BinaryIO], agent_type: str
    ) -> None:
        """Push agents to the API."""
        data = create_default_payload(project_uuid, agents_definition, agent_type)

        with spinner():
            try:
                with self._streaming_request(
                    method="POST", endpoint="api/v1/agents", data=data, files=resources_folder
                ) as response:
                    self._handle_push_response(response)
            except RequestError as e:
                raise e

    def _handle_push_response(self, response: requests.Response) -> None:
        """Handle the streaming response from push_agents."""
        progress = 0
        with click.progressbar(
            length=100,
            label="Pushing agents",
            item_show_func=process_push_display_step,
            show_eta=False,
            show_pos=False,
        ) as bar:
            for line in response.iter_lines():
                if line:
                    resp = json.loads(line)
                    if resp.get("success"):
                        current_progress = resp.get("progress")
                        if current_progress:
                            bar.update((current_progress - progress) * 100, resp)
                            progress = current_progress
                    else:
                        message = resp.get("message", "Unknown error during agent push")
                        raise RequestError(message=message, data=resp.get("data"), request_id=resp.get("request_id"))

    def run_tool_test(
        self,
        project_uuid: str,
        definition: Dict,
        tool_folder: BinaryIO,
        tool_key: str,
        agent_key: str,
        test_definition: Dict,
        credentials: Dict,
        tool_globals: Dict,
        agent_type: str,
        result_callback: Callable[[str, Any, int, Optional[str], bool], None],
        verbose: bool = False,
    ) -> List[Dict]:
        """Run a test for a tool."""
        test_logs = []

        data = self._prepare_test_data(
            project_uuid, definition, test_definition, tool_key, agent_key, credentials, tool_globals, agent_type
        )
        files = {"tool": tool_folder}

        try:
            with self._streaming_request(method="POST", endpoint="api/v1/passive_runs", data=data, files=files) as response:
                test_logs = self._handle_test_response(response, result_callback, verbose)
        except RequestError as e:
            raise RequestError(f"Failed to run test: {e.message}")

        return test_logs
    
    def run_rule_test(
        self,
        project_uuid: str,
        definition: Dict,
        rule_folder: BinaryIO,
        rule_key: str,
        agent_key: str,
        test_definition: Dict,
        credentials: Dict,
        rule_globals: Dict,
        agent_type: str,
        result_callback: Callable[[str, Any, int, Optional[str], bool], None],
        verbose: bool = False,
    ) -> List[Dict]:
        """Run a test for a rule."""
        test_logs = []

        data = self._prepare_test_data(
            project_uuid, definition, test_definition, rule_key, agent_key, credentials, rule_globals, agent_type
        )
        files = {"rule": rule_folder}
        
        try:
            with self._streaming_request(method="POST", endpoint="api/v1/active_runs", data=data, files=files) as response:
                test_logs = self._handle_test_response(response, result_callback, verbose)
        except RequestError as e:
            raise RequestError(f"Failed to run test: {e.message}")
        
        return test_logs

    def run_optimized_active_agent_test(
        self,
        project_uuid: str,
        definition: Dict,
        preprocessing_folder: Optional[BinaryIO],
        rules_folders_map: Dict[str, BinaryIO],
        agent_key: str,
        test_definition: Dict,
        credentials: Dict,
        agent_globals: Dict,
        result_callback: Callable[[str, Any, int, Optional[str], bool], None],
        verbose: bool = False,
    ) -> List[Dict]:
        """Run optimized test for active agent: preprocessor once → test all rules."""
        test_logs = []

        # Prepare data for optimized active agent test
        data = self._prepare_optimized_active_agent_test_data(
            project_uuid, definition, test_definition, agent_key, credentials, agent_globals
        )
        
        # Prepare files: preprocessor + all rules + payload files
        files = {}
        if preprocessing_folder:
            files["preprocessor"] = preprocessing_folder
        
        # Add all rule folders
        for rule_key, rule_folder in rules_folders_map.items():
            files[f"rule_{rule_key}"] = rule_folder
        
        # Add payload files for comparison
        try:
            for test_name, test_config in test_definition.get("tests", {}).items():
                payload_path = test_config.get("payload_path", "")
                if payload_path:
                    try:
                        # Open payload file
                        with open(payload_path, "rb") as payload_file:
                            payload_content = payload_file.read()
                            # Create a new BinaryIO object for the files dict
                            import io
                            payload_buffer = io.BytesIO(payload_content)
                            files[f"payload_{test_name}"] = payload_buffer
                    except Exception as e:
                        print(f"⚠️ Warning: Could not load payload file {payload_path}: {e}")
        except Exception as e:
            print(f"⚠️ Warning: Error processing payload files: {e}")
        
        try:
            with self._streaming_request(method="POST", endpoint="api/v1/active_runs_optimized", data=data, files=files) as response:
                test_logs = self._handle_test_response(response, result_callback, verbose)
        except RequestError as e:
            # If endpoint doesn't exist (404), signal to use fallback
            if e.status_code == 404:
                print(f"⚠️ Optimized endpoint returned 404 - falling back to individual testing")
                raise RequestError("ENDPOINT_NOT_AVAILABLE", status_code=404)
            else:
                print(f"❌ Optimized endpoint error: {e.message}")
                raise RequestError(f"Failed to run optimized active agent test: {e.message}")
        
        return test_logs

    def _prepare_test_data(
        self,
        project_uuid: str,
        definition: Dict,
        test_definition: Dict,
        resource_key: str,
        agent_key: str,
        credentials: Dict,
        resource_globals: Dict,
        agent_type: str,
    ) -> Dict[str, str]:
        """Prepare data for the test run."""
        data = create_default_payload(project_uuid, definition, agent_type)
        
        # Ensure None values are replaced with empty dicts
        test_definition = test_definition or {}
        credentials = credentials or {}
        resource_globals = resource_globals or {}
        
        # Load webhook data for active agents
        if agent_type == "active":
            test_definition_with_webhook_data = self._load_webhook_data_for_tests(test_definition)
            
            # Get payload_path and webhook_data from test that matches current rule
            payload_path = None
            webhook_data = {}
            
            if test_definition_with_webhook_data.get("tests"):
                # Find test with payload_path that matches current rule folder
                for test_name, test_config in test_definition_with_webhook_data["tests"].items():
                    test_payload_path = test_config.get("payload_path", "")
                    test_webhook_data = test_config.get("webhook_data", {})
                    
                    # Match rule by checking if payload_path contains rule folder
                    if resource_key in test_payload_path:
                        payload_path = test_payload_path
                        webhook_data = test_webhook_data
                        print(f"📍 Using test '{test_name}' for rule '{resource_key}' - payload: {test_payload_path}")
                        break
                
                # Fallback: if no match by path, try by status
                if not webhook_data:
                    for test_name, test_config in test_definition_with_webhook_data["tests"].items():
                        test_webhook_data = test_config.get("webhook_data", {})
                        test_status = test_webhook_data.get("status", "")
                        
                        # Match rule to appropriate test based on status
                        if (resource_key == "status_aprovado" and test_status == "payment-approved") or \
                           (resource_key == "status_invoiced" and test_status == "invoiced"):
                            payload_path = test_config.get("payload_path", "")
                            webhook_data = test_webhook_data
                            print(f"📍 Using test '{test_name}' for rule '{resource_key}' by status: {test_status}")
                            break
                
                # Final fallback to first test if no match
                if not webhook_data:
                    first_test = next(iter(test_definition_with_webhook_data["tests"].values()))
                    payload_path = first_test.get("payload_path", "")
                    webhook_data = first_test.get("webhook_data", {})
                    print(f"📍 Using fallback (first test) for rule '{resource_key}'")
            
            # For active agents (rules)
            data.update(
                {
                    "test_definition": json.dumps(test_definition_with_webhook_data),
                    "rule_key": resource_key,
                    "agent_key": agent_key,
                    "rule_credentials": json.dumps(credentials),
                    "rule_globals": json.dumps(resource_globals),
                    "payload_path": payload_path or "",  # Backend expects this field
                    "webhook_data": json.dumps(webhook_data),  # Send webhook_data directly
                }
            )
        else:
            # For passive agents (tools)
            data.update(
                {
                    "test_definition": json.dumps(test_definition),
                    "tool_key": resource_key,
                    "agent_key": agent_key,
                    "tool_credentials": json.dumps(credentials),
                    "tool_globals": json.dumps(resource_globals),
                }
            )
        return data

    def _load_webhook_data_for_tests(self, test_definition: Dict) -> Dict:
        """Load webhook data from payload_path for each test in active agents."""
        import os
        
        # Create a copy of test_definition to avoid modifying the original
        test_definition_copy = test_definition.copy()
        
        # Process each test to load webhook data
        if "tests" in test_definition_copy:
            for test_name, test_config in test_definition_copy["tests"].items():
                payload_path = test_config.get("payload_path", "")
                if payload_path and os.path.exists(payload_path):
                    try:
                        # Load webhook JSON data
                        with open(payload_path, "r") as file:
                            webhook_data = json.load(file)
                        
                        # Add webhook_data to test config
                        test_config["webhook_data"] = webhook_data
                        
                    except Exception as e:
                        print(f"⚠️ Warning: Could not load webhook data for test '{test_name}': {e}")
                        # Set empty webhook_data if load fails
                        test_config["webhook_data"] = {}
                else:
                    print(f"⚠️ Warning: payload_path not found for test '{test_name}': {payload_path}")
                    test_config["webhook_data"] = {}
        
        return test_definition_copy

    def _handle_test_response(
        self,
        response: requests.Response,
        result_callback: Callable[[str, Any, int, Optional[str], bool], None],
        verbose: bool,
    ) -> List[Dict]:
        """Handle the streaming response from run_test."""
        test_logs = []

        for line in response.iter_lines():
            if line:
                resp = json.loads(line)
                
                test_data = process_test_progress(resp, verbose)
                if test_data:
                    if verbose and "test_logs" in test_data:
                        test_logs.append(test_data)
                    # Call the callback with the test results
                    result_callback(
                        test_data["test_name"],
                        test_data["test_response"],
                        test_data["test_status_code"],
                        resp.get("code"),
                        verbose,
                    )

        return test_logs

    def _prepare_optimized_active_agent_test_data(
        self,
        project_uuid: str,
        definition: Dict,
        test_definition: Dict,
        agent_key: str,
        credentials: Dict,
        agent_globals: Dict,
    ) -> Dict[str, str]:
        """Prepare data for optimized active agent test."""
        data = create_default_payload(project_uuid, definition, "active")
        
        # Ensure None values are replaced with empty dicts
        test_definition = test_definition or {}
        credentials = credentials or {}
        agent_globals = agent_globals or {}
        
        # Extract rule keys from definition
        agent_data = definition.get("agents", {}).get(agent_key, {})
        rules = agent_data.get("rules", {})
        rule_keys = list(rules.keys())
        
        # Prepare test cases with payload paths for comparison
        test_cases = []
        for test_name, test_config in test_definition.get("tests", {}).items():
            test_case = {
                "test_name": test_name,
                "payload_path": test_config.get("payload_path", ""),
                "expected_triggered_rules": test_config.get("expected_triggered_rules", []),
                "expected_not_triggered_rules": test_config.get("expected_not_triggered_rules", []),
                "params": test_config.get("params", {}),
                "credentials": test_config.get("credentials", {})
            }
            test_cases.append(test_case)
        
        data.update({
            "test_definition": json.dumps(test_definition),
            "agent_key": agent_key,
            "rule_keys": json.dumps(rule_keys),  # Send all rule keys
            "test_cases": json.dumps(test_cases),  # Send structured test cases
            "credentials": json.dumps(credentials),
            "agent_globals": json.dumps(agent_globals),
        })
        
        return data

    def get_tool_logs(
        self, agent: str, tool: str, start_time: str, end_time: str, pattern: str, next_token: str | None = None
    ) -> tuple[Any, ErrorMessage]:
        """Get logs for a tool."""

        data = {
            "agent_key": agent,
            "tool_key": tool,
            "start_time": str(start_time) if start_time else None,
            "end_time": str(end_time) if end_time else None,
            "next_token": next_token,
            "pattern": pattern,
        }

        try:
            response = self._make_request(method="GET", endpoint="api/v1/tool-logs/", params=data)
        except RequestError as e:
            return {}, f"Error fetching logs: {e.message} - Request ID: {e.request_id}"

        return response.json(), None

    def test_preprocessor_directly(
        self,
        project_uuid: str,
        definition: Dict,
        preprocessing_folder: BinaryIO,
        webhook_data: Dict,
        agent_key: str,
        verbose: bool = False,
    ) -> Dict:
        """Test the preprocessor directly to see what it returns."""
        
        # Prepare data for preprocessor test
        data = {
            "project_uuid": project_uuid,
            "definition": json.dumps(definition),
            "toolkit_version": get_toolkit_version(),
            "type": "active",
            "agent_key": agent_key,
            "test_type": "preprocessor_only",
            "webhook_data": json.dumps(webhook_data)
        }
        
        files = {"preprocessor": preprocessing_folder}
        
        print(f"🚀 Testing preprocessor directly...")
        print(f"📊 Data keys: {list(data.keys())}")
        print(f"📊 Files: {list(files.keys())}")
        print(f"📊 Webhook data: {webhook_data}")
        
        try:
            # Try to use a simple endpoint that just runs the preprocessor
            response = self._make_request(
                method="POST", 
                endpoint="api/v1/test_preprocessor", 
                data=data, 
                files=files
            )
            
            result = response.json()
            print(f"✅ Preprocessor test successful!")
            print(f"📊 Response: {result}")
            return result
            
        except RequestError as e:
            if e.status_code == 404:
                print(f"⚠️ Preprocessor test endpoint not available")
                print(f"📊 Backend needs to implement /api/v1/test_preprocessor endpoint")
                return {"error": "endpoint_not_available", "message": str(e)}
            else:
                print(f"❌ Error testing preprocessor: {e}")
                return {"error": "test_failed", "message": str(e)}
