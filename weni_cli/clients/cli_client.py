import click
import requests
import json

from weni_cli.spinner import spinner
from weni_cli.store import STORE_CLI_BASE_URL, STORE_TOKEN_KEY, Store
import importlib.metadata

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
        self.headers = {"Authorization": f"Bearer {store.get(STORE_TOKEN_KEY)}"}
        self.base_url = store.get(STORE_CLI_BASE_URL, DEFAULT_BASE_URL)

    def push_agents(self, project_uuid, agents_definition, skill_folders):

        def display_step(resp):
            if not resp:
                return

            if not resp.get("success") and not resp.get("message"):
                return "Unknown error while pushing agents"

            # Add a buffer at the end to avoid the stdout last character being cut off by the spinner
            return resp.get("message") + "."

        url = f"{self.base_url}/api/v1/agents"

        data = create_default_payload(project_uuid, agents_definition)

        s = requests.Session()

        with spinner():
            with s.post(
                url, headers=self.headers, data=data, files=skill_folders, stream=True, timeout=(10, None)
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"Failed to push agents: {response.text}")

                progress = 0
                with click.progressbar(
                    length=100, label="Pushing agents", item_show_func=display_step, show_eta=False, show_pos=False
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
        verbose=False,
    ):

        def display_test_progress(resp, verbose):
            if not resp:
                return

            if not resp.get("success") and not resp.get("message"):
                click.echo("Unknown error while running test")
                return

            if not resp.get("success"):
                click.echo(resp.get("message"))
                return

            if resp.get("code") == "TEST_CASE_RUNNING":
                click.echo(f"{resp.get('message')}...", nl=False)
                return

            if resp.get("code") == "TEST_CASE_COMPLETED":
                if resp.get("data", {}).get("test_status_code") == 200:
                    click.echo(click.style("PASS", fg="green"))
                else:
                    click.echo(click.style("FAILED", fg="red"))

                if verbose:
                    click.echo(click.style(f"{resp.get('data', {}).get('test_case')} Logs:", fg="yellow"))
                    click.echo(resp.get("data", {}).get("test_response", {}))
                    click.echo("\n")

                return

        url = f"{self.base_url}/api/v1/runs"

        data = create_default_payload(project_uuid, definition)
        data["test_definition"] = json.dumps(test_definition)
        data["skill_name"] = skill_name
        data["agent_name"] = agent_name
        data["skill_credentials"] = json.dumps(credentials)
        data["skill_globals"] = json.dumps(skill_globals)

        files = {"skill": skill_folder}

        s = requests.Session()

        with spinner() as spin:
            with s.post(
                url, headers=self.headers, data=data, files=files, timeout=(10, None), stream=True
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"Failed to run test: {response.text}")

                for line in response.iter_lines():
                    if line:
                        spin.stop()
                        display_test_progress(json.loads(line), verbose)
                        spin.start()
