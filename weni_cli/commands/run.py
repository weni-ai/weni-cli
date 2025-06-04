from io import BufferedReader
from typing import Optional
import rich_click as click

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.console import group

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.packager.packager import create_agent_resource_folder_zip
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.definition import format_definition, load_agent_definition, load_test_definition


DEFAULT_TEST_DEFINITION_FILE = "test_definition.yaml"


class RunHandler(Handler):
    def execute(self, **kwargs):
        definition_path = kwargs.get("definition")
        agent_key = kwargs.get("agent_key")
        tool_key = kwargs.get("tool_key")
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
            formatter.print_error_panel(
                f"Invalid agent definition YAML file format, error:\n{error}", title="Error loading agent definition"
            )
            return

        # Validate agent existence
        if agent_key not in definition_data.get("agents", {}):
            formatter.print_error_panel(
                f"Agent '{agent_key}' not found in the definition file.",
                title="Invalid Agent"
            )
            return

        # Validate tool existence
        agent_tools = []
        for tool in definition_data["agents"][agent_key].get("tools", []):
            if isinstance(tool, dict):
                agent_tools.extend(tool.keys())

        if tool_key not in agent_tools:
            formatter.print_error_panel(
                f"Tool '{tool_key}' not found in agent '{agent_key}'.\nAvailable tools: {', '.join(agent_tools)}",
                title="Invalid Tool"
            )
            return

        if not test_definition_path:
            test_definition_path = self.load_default_test_definition(definition_data, agent_key, tool_key)

            if not test_definition_path:
                click.echo(
                    f"Error: Failed to get default test definition file: {DEFAULT_TEST_DEFINITION_FILE} in tool folder."
                )
                click.echo("You can use the --file option to specify a different file.")
                return

        tool_folder, error = self.load_tool_folder(definition_data, agent_key, tool_key)
        if error:
            formatter.print_error_panel(error)
            return

        test_definition, error = load_test_definition(test_definition_path)
        if error:
            formatter.print_error_panel(error)
            return

        definition = format_definition(definition_data)

        tool_source_path = self.get_tool_source_path(definition, agent_key, tool_key)

        credentials = self.load_tool_credentials(tool_source_path)

        tool_globals = self.load_tool_globals(tool_source_path)

        self.run_test(
            project_uuid,
            definition,
            tool_folder,
            tool_key,
            agent_key,
            test_definition,
            credentials,
            tool_globals,
            verbose,
        )

    def parse_agent_tool(self, agent_tool) -> tuple[Optional[str], Optional[str]]:
        try:
            return agent_tool.split(".")[0], agent_tool.split(".")[1]
        except Exception:
            return None, None

    def get_tool_source_path(self, definition, agent_key, tool_key) -> Optional[str]:
        agent_data = definition.get("agents", {}).get(agent_key)

        if not agent_data:
            return None

        for tool in agent_data.get("tools", []):
            if tool.get("key") == tool_key:
                return tool.get("source", {}).get("path")
        return None

    def load_tool_credentials(self, tool_source_path: str) -> Optional[dict]:
        credentials = {}
        try:
            with open(f"{tool_source_path}/.env", "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    credentials[key] = value
        except Exception:
            return {}

        return credentials

    def load_tool_globals(self, tool_source_path: str) -> Optional[dict]:
        globals = {}
        try:
            with open(f"{tool_source_path}/.globals", "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    globals[key] = value
        except Exception:
            return {}

        return globals

    def load_default_test_definition(self, definition, agent_key, tool_key) -> Optional[str]:
        try:
            definition_path = None

            agent_data = definition.get("agents", {}).get(agent_key)

            if not agent_data:
                return None

            for tool in agent_data.get("tools", []):
                for key, tool_data in tool.items():
                    if key == tool_key:
                        path_test = tool_data.get("source", {}).get("path_test")
                        tool_path = tool_data.get("source", {}).get("path")
                        if tool_data.get("source", {}).get("path_test"):
                            definition_path = f"{tool_path}/{path_test}"
                        else:
                            definition_path = f"{tool_path}/{DEFAULT_TEST_DEFINITION_FILE}"

            if not definition_path:
                return None

            return definition_path
        except Exception as e:
            click.echo(f"Error: Failed to load default test definition file: {e}")
            return None

    def load_tool_folder(
        self, definition, agent_key, tool_key
    ) -> tuple[Optional[BufferedReader], Optional[Exception]]:
        agent_data = definition.get("agents", {}).get(agent_key)
        if not agent_data:
            return None, Exception(f"Agent {agent_key} not found in definition")

        tools = agent_data.get("tools", [])

        tool_data = None
        for tool in tools:
            for key, data in tool.items():
                if key == tool_key:
                    tool_data = data
                    break

        if not tool_data:
            return None, Exception(f"Tool {tool_key} not found in agent {agent_key}")

        tool_folder, error = create_agent_resource_folder_zip(tool_key, tool_data.get("source").get("path"))
        if error:
            return None, Exception(f"Failed to create tool folder for tool {tool_key} in agent {agent_key}\n{error}")

        return tool_folder, None

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

    def display_test_results(self, rows, tool_name, verbose=False):
        """
        Create a table to display test results.

        Args:
            rows (list): List of row dictionaries containing test results
            tool_name (str): Name of the tool being tested
            verbose (bool, optional): Whether to show verbose output. Defaults to False.

        Returns:
            Table: Rich table object with test results, or None if rows is empty
        """
        if not rows:
            return None

        table = Table(title=f"Test Results for {tool_name}", expand=True)
        table.add_column("Test Name", justify="left")
        table.add_column("Status", justify="center")
        table.add_column("Response", ratio=2, no_wrap=True)

        for row in rows:
            status = self.get_status_icon(row.get("status")) if row.get("code") == "TEST_CASE_COMPLETED" else "⏳"
            response_display = self.format_response_for_display(row.get("response"))
            table.add_row(row.get("name"), status, response_display)

        return table

    def update_live_display(
        self, test_rows, test_name, test_result, status_code, code, live_display, tool_name, verbose=False
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
            tool_name (str): Name of the tool being tested
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

        live_display.update(self.display_test_results(test_rows, tool_name, verbose), refresh=True)

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
        tool_folder,
        tool_key,
        agent_key,
        test_definition,
        credentials,
        tool_globals,
        verbose=False,
    ):
        test_rows = []
        # Use the class method instead of a nested function
        with Live(self.display_test_results([], tool_key, verbose), refresh_per_second=4) as live:
            # Create a callback function that will be passed to the CLIClient
            def update_live_callback(test_name, test_result, status_code, code, verbose):
                self.update_live_display(test_rows, test_name, test_result, status_code, code, live, tool_key, verbose)

            client = CLIClient()
            test_logs = client.run_test(
                project_uuid,
                definition,
                tool_folder,
                tool_key,
                agent_key,
                test_definition,
                credentials,
                tool_globals,
                "active",
                update_live_callback,
                verbose,
            )

        if verbose:
            self.render_reponse_and_logs(test_logs)
