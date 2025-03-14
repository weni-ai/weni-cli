import rich_click as click

from slugify import slugify

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.console import group

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.packager.packager import create_skill_folder_zip
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.definition import format_definition, load_agent_definition, load_test_definition


DEFAULT_TEST_DEFINITION_FILE = "test_definition.yaml"


class RunHandler(Handler):
    def execute(self, **kwargs):
        definition_path = kwargs.get("definition")
        agent_key = kwargs.get("agent_key")
        skill_key = kwargs.get("skill_key")
        test_definition_path = kwargs.get("test_definition")
        verbose = kwargs.get("verbose", False)
        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        formatter = Formatter()

        if not project_uuid:
            click.echo("No project selected, please select a project first")
            return

        definition_data, error = load_agent_definition(definition_path)

        if error:
            formatter.print_error_panel(error)
            return

        if not test_definition_path:
            test_definition_path = self.load_default_test_definition(definition_data, agent_key, skill_key)

            if not test_definition_path:
                click.echo(
                    f"Error: Failed to get default test definition file: {DEFAULT_TEST_DEFINITION_FILE} in skill folder."
                )
                click.echo("You can use the --file option to specify a different file.")
                return

        skill_folder = self.load_skill_folder(definition_data, agent_key, skill_key)

        if not skill_folder:
            click.echo("Error: Failed to load skill folder")
            return

        definition = format_definition(definition_data)

        if not definition:
            return

        test_definition, error = load_test_definition(test_definition_path)

        if error:
            formatter.print_error_panel(error)
            return

        skill_source_path = self.get_skill_source_path(definition, agent_key, skill_key)

        credentials = self.load_skill_credentials(skill_source_path)

        skill_globals = self.load_skill_globals(skill_source_path)

        agent_name, skill_name = self.get_skill_and_agent_name(definition, agent_key, skill_key)

        if not skill_name or not agent_name:
            click.echo("Error: Failed to get skill or agent name")
            return

        self.run_test(
            project_uuid,
            definition,
            skill_folder,
            skill_name,
            agent_name,
            test_definition,
            credentials,
            skill_globals,
            verbose,
        )

    def parse_agent_skill(self, agent_skill) -> tuple[str, str]:
        try:
            return agent_skill.split(".")[0], agent_skill.split(".")[1]
        except Exception:
            return None, None

    def get_skill_and_agent_name(self, definition, agent_key, skill_key) -> tuple[str, str]:
        agent_data = definition.get("agents", {}).get(agent_key)

        if not agent_data:
            return None, None

        skill_name = None
        for skill in agent_data.get("skills", []):
            if skill.get("key") == skill_key:
                skill_name = skill.get("name")

        return agent_data.get("name"), skill_name

    def get_skill_source_path(self, definition, agent_key, skill_key) -> str | None:
        agent_data = definition.get("agents", {}).get(agent_key)

        if not agent_data:
            return None

        for skill in agent_data.get("skills", []):
            if skill.get("key") == skill_key:
                return skill.get("source", {}).get("path")
        return None

    def load_skill_credentials(self, skill_source_path: str) -> dict | None:
        credentials = {}
        try:
            with open(f"{skill_source_path}/.env", "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    credentials[key] = value
        except Exception:
            return {}

        return credentials

    def load_skill_globals(self, skill_source_path: str) -> dict | None:
        globals = {}
        try:
            with open(f"{skill_source_path}/.globals", "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    globals[key] = value
        except Exception:
            return {}

        return globals

    def load_default_test_definition(self, definition, agent_key, skill_key) -> str | None:
        try:
            definition_path = None

            agent_data = definition.get("agents", {}).get(agent_key)

            if not agent_data:
                return None

            for skill in agent_data.get("skills", []):
                for key, skill_data in skill.items():
                    if key == skill_key:
                        path_test = skill_data.get("source", {}).get("path_test")
                        skill_path = skill_data.get("source", {}).get("path")
                        if skill_data.get("source", {}).get("path_test"):
                            definition_path = f"{skill_path}/{path_test}"
                        else:
                            definition_path = f"{skill_path}/{DEFAULT_TEST_DEFINITION_FILE}"

            if not definition_path:
                return None

            return definition_path
        except Exception as e:
            click.echo(f"Error: Failed to load default test definition file: {e}")
            return None

    def load_skill_folder(self, definition, agent_key, skill_key) -> bytes:
        agent_data = definition.get("agents", {}).get(agent_key)

        if not agent_data:
            click.echo(f"Error: Agent {agent_key} not found in definition")
            return None

        skills = agent_data.get("skills", [])

        skill_data = None
        for skill in skills:
            for key, data in skill.items():
                if key == skill_key:
                    skill_data = data
                    break

        if not skill_data:
            click.echo(f"Error: Skill {skill_key} not found in agent {agent_key}")
            return None

        skill_slug = slugify(skill_data.get("name"))
        skill_folder = create_skill_folder_zip(skill_slug, skill_data.get("source").get("path"))

        if not skill_folder:
            click.echo(f"Error: Failed to create skill folder for skill {skill_key} in agent {agent_key}")
            return None

        return skill_folder

    def format_response_for_display(self, test_result):
        """Format response for better display"""

        if not test_result:
            return "waiting..."

        if isinstance(test_result, dict) and "response" in test_result:
            response = test_result.get("response")

            function_response = response.get("functionResponse")

            if not function_response:
                return str(response)

            response_body = function_response.get("responseBody")

            if not response_body:
                return str(function_response)

            response_body_text = response_body.get("TEXT")

            if not response_body_text:
                return str(response_body)

            return response_body_text.get("body", "")
        else:
            return str(test_result)

    def get_status_icon(self, status_code):
        if status_code == 200:
            return "✅"

        return "❌"

    def display_test_results(self, rows, skill_name, verbose=False):
        """
        Create a table to display test results.

        Args:
            rows (list): List of row dictionaries containing test results
            skill_name (str): Name of the skill being tested
            verbose (bool, optional): Whether to show verbose output. Defaults to False.

        Returns:
            Table: Rich table object with test results, or None if rows is empty
        """
        if not rows:
            return None

        table = Table(title=f"Test Results for {skill_name}", expand=True)
        table.add_column("Test Name", justify="left")
        table.add_column("Status", justify="center")
        table.add_column("Response", ratio=2, no_wrap=True)

        for row in rows:
            status = self.get_status_icon(row.get("status")) if row.get("code") == "TEST_CASE_COMPLETED" else "⏳"
            response_display = self.format_response_for_display(row.get("response"))
            table.add_row(row.get("name"), status, response_display)

        return table

    def update_live_display(
        self, test_rows, test_name, test_result, status_code, code, live_display, skill_name, verbose=False
    ):
        """
        Update the live display with test results.

        Args:
            test_rows (list): List of test result rows to update
            test_name (str): Name of the test
            test_result (dict): Test result data
            status_code (int): HTTP status code of the test result
            code (str): Test case status code (e.g., TEST_CASE_COMPLETED)
            live_display (Live): Rich Live object for updating the display
            skill_name (str): Name of the skill being tested
            verbose (bool, optional): Whether to show verbose output. Defaults to False.
        """
        # Check if test_name is already in test_rows, if not, add it
        row_index = next((i for i, row in enumerate(test_rows) if row.get("name") == test_name), None)
        if row_index is None:
            test_rows.append({"name": test_name, "status": status_code, "response": test_result, "code": code})
        else:
            test_rows[row_index]["status"] = status_code
            test_rows[row_index]["response"] = test_result
            test_rows[row_index]["code"] = code

        live_display.update(self.display_test_results(test_rows, skill_name, verbose), refresh=True)

    def render_reponse_and_logs(self, logs):
        console = Console()

        @group()
        def get_panels():
            if log.get("test_response"):
                yield Panel(
                    self.format_response_for_display(log.get("test_response")),
                    title="[bold yellow]Response[/bold yellow]",
                    title_align="left",
                )

            if log.get("test_logs"):
                yield Panel(
                    log.get("test_logs").strip("\n"),
                    title="[bold blue]Logs[/bold blue]",
                    title_align="left",
                )

        console.print("\n")
        for log in logs:
            if log.get("test_response") or log.get("test_logs"):
                console.print(
                    Panel(
                        get_panels(),
                        title=f"[bold green]Test Results for {log.get('test_name')}[/bold green]",
                        title_align="left",
                    )
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
        test_rows = []
        # Use the class method instead of a nested function
        with Live(self.display_test_results([], skill_name, verbose), refresh_per_second=4) as live:
            # Create a callback function that will be passed to the CLIClient
            def update_live_callback(test_name, test_result, status_code, code, verbose):
                self.update_live_display(
                    test_rows, test_name, test_result, status_code, code, live, skill_name, verbose
                )

            client = CLIClient()
            test_logs = client.run_test(
                project_uuid,
                definition,
                skill_folder,
                skill_name,
                agent_name,
                test_definition,
                credentials,
                skill_globals,
                update_live_callback,
                verbose,
            )

        if verbose:
            self.render_reponse_and_logs(test_logs)
