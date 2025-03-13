import rich_click as click
import requests
import json
import importlib.metadata
from typing import Dict, List, Optional, Any, BinaryIO, Callable
from contextlib import contextmanager

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


def create_default_payload(project_uuid: str, definition: Dict) -> Dict[str, str]:
    """Create a default payload for API requests."""
    return {
        "project_uuid": project_uuid,
        "definition": json.dumps(definition),
        "toolkit_version": get_toolkit_version(),
    }


class CLIClient:
    """Client for interacting with the Weni CLI API."""

    def __init__(self):
        store = Store()
        self.headers = self._create_headers(store)
        self.base_url = store.get(STORE_CLI_BASE_URL, DEFAULT_BASE_URL)
        self.session = requests.Session()

    def _create_headers(self, store: Store) -> Dict[str, str]:
        """Create headers for API requests."""
        return {
            "Authorization": f"Bearer {store.get(STORE_TOKEN_KEY)}",
            "X-Project-Uuid": store.get(STORE_PROJECT_UUID_KEY),
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
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        timeout: tuple = (10, None),
    ) -> requests.Response:
        """Make a non-streaming request to the API with error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = self.session.request(
            method=method, url=url, headers=self.headers, data=data, files=files, stream=False, timeout=timeout
        )

        if response.status_code != 200:
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
        payload = {"project_uuid": project_uuid}

        try:
            self._make_request(method="POST", endpoint="api/v1/permissions/verify", data=json.dumps(payload))
        except RequestError as e:
            raise RequestError(f"Failed to check project permission: {e.message}")

    def push_agents(self, project_uuid: str, agents_definition: Dict, skill_folders: Dict[str, BinaryIO]) -> None:
        """Push agents to the API."""
        data = create_default_payload(project_uuid, agents_definition)

        with spinner():
            try:
                with self._streaming_request(
                    method="POST", endpoint="api/v1/agents", data=data, files=skill_folders
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

    def run_test(
        self,
        project_uuid: str,
        definition: Dict,
        skill_folder: BinaryIO,
        skill_name: str,
        agent_name: str,
        test_definition: Dict,
        credentials: Dict,
        skill_globals: Dict,
        result_callback: Callable[[str, Any, int, Optional[str], bool], None],
        verbose: bool = False,
    ) -> List[Dict]:
        """Run a test for a skill."""
        test_logs = []

        data = self._prepare_test_data(
            project_uuid, definition, test_definition, skill_name, agent_name, credentials, skill_globals
        )
        files = {"skill": skill_folder}

        try:
            with self._streaming_request(method="POST", endpoint="api/v1/runs", data=data, files=files) as response:
                test_logs = self._handle_test_response(response, result_callback, verbose)
        except RequestError as e:
            raise RequestError(f"Failed to run test: {e.message}")

        return test_logs

    def _prepare_test_data(
        self,
        project_uuid: str,
        definition: Dict,
        test_definition: Dict,
        skill_name: str,
        agent_name: str,
        credentials: Dict,
        skill_globals: Dict,
    ) -> Dict[str, str]:
        """Prepare data for the test run."""
        data = create_default_payload(project_uuid, definition)
        data.update(
            {
                "test_definition": json.dumps(test_definition),
                "skill_name": skill_name,
                "agent_name": agent_name,
                "skill_credentials": json.dumps(credentials),
                "skill_globals": json.dumps(skill_globals),
            }
        )
        return data

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
