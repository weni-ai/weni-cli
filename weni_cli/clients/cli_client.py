import rich_click as click
import requests
import json
import importlib.metadata

from weni_cli.spinner import spinner
from weni_cli.store import STORE_CLI_BASE_URL, STORE_PROJECT_UUID_KEY, STORE_TOKEN_KEY, Store
from weni_cli.clients.response_handlers import process_push_display_step, process_test_progress

DEFAULT_BASE_URL = "https://cli.cloud.weni.ai"


# Check installed version of weni-agents-toolkit in pyproject.toml file
def get_toolkit_version():
    version = importlib.metadata.version("weni-agents-toolkit")
    click.echo(f"Using toolkit version: {version}")
    return version


def create_default_payload(project_uuid, definition):
    return {
        "project_uuid": project_uuid,
        "definition": json.dumps(definition),
        "toolkit_version": get_toolkit_version(),
    }


class CLIClient:
    base_url = None
    headers = None

    def __init__(self):
        store = Store()
        self.headers = {
            "Authorization": f"Bearer {store.get(STORE_TOKEN_KEY)}",
            "X-Project-Uuid": store.get(STORE_PROJECT_UUID_KEY),
        }
        self.base_url = store.get(STORE_CLI_BASE_URL, DEFAULT_BASE_URL)

    def push_agents(self, project_uuid, agents_definition, skill_folders):
        url = f"{self.base_url}/api/v1/agents"

        data = create_default_payload(project_uuid, agents_definition)

        session = requests.Session()

        with spinner():
            with session.post(
                url, headers=self.headers, data=data, files=skill_folders, stream=True, timeout=(10, None)
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"Failed to push agents: {response.text}")

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
                                if not resp.get("message"):
                                    raise Exception(f"Failed to push agents: {response.text}")

                                raise Exception(
                                    f"{resp.get('message')} - Data: {resp.get('data', None)} - Request ID: {resp.get('request_id')}"
                                )

    def run_test(
        self,
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
    ) -> list[dict]:
        test_logs = []

        url = f"{self.base_url}/api/v1/runs"

        data = create_default_payload(project_uuid, definition)
        data["test_definition"] = json.dumps(test_definition)
        data["skill_name"] = skill_name
        data["agent_name"] = agent_name
        data["skill_credentials"] = json.dumps(credentials)
        data["skill_globals"] = json.dumps(skill_globals)

        files = {"skill": skill_folder}

        s = requests.Session()

        try:
            with s.post(
                url, headers=self.headers, data=data, files=files, timeout=(10, None), stream=True
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"Failed to run test: {response.text}")

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
        except Exception as e:
            raise e

        return test_logs
