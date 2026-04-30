import os
from io import BufferedReader
from typing import Optional

import rich_click as click
from rich.console import Console, group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.packager.loader import load_active_agent_resources
from weni_cli.packager.packager import create_agent_resource_folder_zip
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.agent_definition import (
    format_definition,
    load_agent_definition,
    load_test_definition,
    validate_active_test_definition,
)

DEFAULT_TEST_DEFINITION_FILE = "test_definition.yaml"

PASSIVE_TYPE = "passive"
ACTIVE_TYPE = "active"

# Maps the ResponseStatus enum values returned by the active Lambda template
# to a status icon used in the live results table.
ACTIVE_STATUS_ICONS = {
    0: "✅",  # RULE_MATCHED
    1: "🟡",  # RULE_NOT_MATCHED
    2: "❌",  # PREPROCESSING_FAILED
    3: "❌",  # CUSTOM_RULE_FAILED
    4: "❌",  # OFFICIAL_RULE_FAILED
    5: "❌",  # GLOBAL_RULE_FAILED
    6: "🟡",  # GLOBAL_RULE_NOT_MATCHED
}

ACTIVE_STATUS_NAMES = {
    0: "RULE_MATCHED",
    1: "RULE_NOT_MATCHED",
    2: "PREPROCESSING_FAILED",
    3: "CUSTOM_RULE_FAILED",
    4: "OFFICIAL_RULE_FAILED",
    5: "GLOBAL_RULE_FAILED",
    6: "GLOBAL_RULE_NOT_MATCHED",
}


def detect_agent_type(definition_data: dict) -> str:
    """Detect whether the loaded definition describes a passive (Tool) or active agent."""
    agents = definition_data.get("agents", {}) or {}
    if not agents:
        return PASSIVE_TYPE

    agent = next(iter(agents.values()))
    if isinstance(agent, dict) and agent.get("rules"):
        return ACTIVE_TYPE
    return PASSIVE_TYPE


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
                f"Invalid agent definition YAML file format, error:\n{error}",
                title="Error loading agent definition",
            )
            return

        if agent_key not in definition_data.get("agents", {}):
            formatter.print_error_panel(
                f"Agent '{agent_key}' not found in the definition file.",
                title="Invalid Agent",
            )
            return

        agent_type = detect_agent_type(definition_data)

        if agent_type == ACTIVE_TYPE:
            self._execute_active(
                definition_data=definition_data,
                definition_path=definition_path,
                agent_key=agent_key,
                test_definition_path=test_definition_path,
                project_uuid=project_uuid,
                verbose=verbose,
                formatter=formatter,
            )
        else:
            self._execute_passive(
                definition_data=definition_data,
                agent_key=agent_key,
                tool_key=tool_key,
                test_definition_path=test_definition_path,
                project_uuid=project_uuid,
                verbose=verbose,
                formatter=formatter,
            )

    def _execute_passive(  # noqa: PLR0913
        self,
        definition_data,
        agent_key,
        tool_key,
        test_definition_path,
        project_uuid,
        verbose,
        formatter,
    ):
        if not tool_key:
            formatter.print_error_panel(
                "TOOL_KEY is required for passive agents.",
                title="Missing Tool",
            )
            return

        agent_tools = []
        for tool in definition_data["agents"][agent_key].get("tools", []):
            if isinstance(tool, dict):
                agent_tools.extend(tool.keys())

        if tool_key not in agent_tools:
            formatter.print_error_panel(
                f"Tool '{tool_key}' not found in agent '{agent_key}'.\nAvailable tools: {', '.join(agent_tools)}",
                title="Invalid Tool",
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
            project_uuid=project_uuid,
            definition=definition,
            tool_folder=tool_folder,
            tool_key=tool_key,
            agent_key=agent_key,
            test_definition=test_definition,
            credentials=credentials,
            tool_globals=tool_globals,
            verbose=verbose,
            agent_type=PASSIVE_TYPE,
            display_label=tool_key,
        )

    def _execute_active(  # noqa: PLR0913
        self,
        definition_data,
        definition_path,
        agent_key,
        test_definition_path,
        project_uuid,
        verbose,
        formatter,
    ):
        if not test_definition_path:
            test_definition_path = self._load_default_active_test_definition(definition_path)

            if not test_definition_path:
                click.echo(
                    f"Error: Failed to get default test definition file: {DEFAULT_TEST_DEFINITION_FILE} "
                    f"next to the agent definition."
                )
                click.echo("You can use the --file option to specify a different file.")
                return

        test_definition, error = load_test_definition(test_definition_path)
        if error:
            formatter.print_error_panel(error)
            return

        validation_error = validate_active_test_definition(test_definition)
        if validation_error:
            formatter.print_error_panel(
                f"Invalid test definition for active agent:\n{validation_error}",
                title="Invalid test definition",
            )
            return

        resources_folder, error = load_active_agent_resources(definition_data, agent_key)
        if error or not resources_folder:
            formatter.print_error_panel(
                error or f"No resources found for active agent '{agent_key}'",
                title="Failed to load active agent resources",
            )
            return

        definition = format_definition(definition_data)

        self.run_test(
            project_uuid=project_uuid,
            definition=definition,
            tool_folder=None,
            tool_key=None,
            agent_key=agent_key,
            test_definition=test_definition,
            credentials={},
            tool_globals={},
            verbose=verbose,
            agent_type=ACTIVE_TYPE,
            display_label=agent_key,
            resources_folder=resources_folder,
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

    def _load_default_active_test_definition(self, definition_path: str) -> Optional[str]:
        """Look for ``test_definition.yaml`` next to the agent definition file."""
        try:
            base_dir = os.path.dirname(os.path.abspath(definition_path))
            candidate = os.path.join(base_dir, DEFAULT_TEST_DEFINITION_FILE)
            return candidate if os.path.exists(candidate) else None
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

    def format_response_for_display(self, test_result, agent_type: str = PASSIVE_TYPE):
        """Format the test response for the live table display."""
        if not test_result:
            return "waiting..."

        if agent_type == ACTIVE_TYPE:
            return self._format_active_response_for_display(test_result)

        return self._format_passive_response_for_display(test_result)

    def _format_passive_response_for_display(self, test_result):
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

        return str(test_result)

    def _format_active_response_for_display(self, test_result):
        if not isinstance(test_result, dict):
            return str(test_result)

        status_value = test_result.get("status")
        status_name = ACTIVE_STATUS_NAMES.get(status_value, "UNKNOWN")
        template = test_result.get("template")
        contact_urn = test_result.get("contact_urn")
        error = test_result.get("error")

        parts = [status_name]
        if template:
            parts.append(f"template={template}")
        if contact_urn:
            parts.append(f"urn={contact_urn}")
        if error:
            parts.append(f"error={error}")
        return " | ".join(parts)

    def get_status_icon(self, status_code, agent_type: str = PASSIVE_TYPE, response=None):
        """Resolve the status icon for either a passive or active agent run."""
        if agent_type == ACTIVE_TYPE and isinstance(response, dict):
            response_status = response.get("status")
            if response_status in ACTIVE_STATUS_ICONS:
                return ACTIVE_STATUS_ICONS[response_status]

        if status_code == 200:
            return "✅"

        return "❌"

    def display_test_results(self, rows, display_label, agent_type: str = PASSIVE_TYPE, verbose: bool = False):
        """Build the Rich table used by the live display."""
        if not rows:
            return None

        title = (
            f"Test Results for {display_label} (active agent)"
            if agent_type == ACTIVE_TYPE
            else f"Test Results for {display_label}"
        )
        table = Table(title=title, expand=True)
        table.add_column("Test Name", justify="left")
        table.add_column("Status", justify="center")
        if agent_type == ACTIVE_TYPE:
            table.add_column("Result", ratio=2, no_wrap=True)
        else:
            table.add_column("Response", ratio=2, no_wrap=True)

        for row in rows:
            if row.get("code") == "TEST_CASE_COMPLETED":
                status = self.get_status_icon(
                    row.get("status"), agent_type=agent_type, response=row.get("response")
                )
            else:
                status = "⏳"
            response_display = self.format_response_for_display(row.get("response"), agent_type=agent_type)
            table.add_row(row.get("name"), status, response_display)

        return table

    def update_live_display(  # noqa: PLR0913
        self,
        test_rows,
        test_name,
        test_result,
        status_code,
        code,
        live_display,
        display_label,
        agent_type: str = PASSIVE_TYPE,
        verbose: bool = False,
    ):
        row_index = next((i for i, row in enumerate(test_rows) if row.get("name") == test_name), None)
        if row_index is None:
            test_rows.append({"name": test_name, "status": status_code, "response": test_result, "code": code})
        else:
            test_rows[row_index]["status"] = status_code
            test_rows[row_index]["response"] = test_result
            test_rows[row_index]["code"] = code

        live_display.update(
            self.display_test_results(test_rows, display_label, agent_type=agent_type, verbose=verbose),
            refresh=True,
        )

    def render_reponse_and_logs(self, logs, agent_type: str = PASSIVE_TYPE):
        console = Console()

        @group()
        def get_panels():
            if log.get("test_response"):
                yield Panel(
                    self.format_response_for_display(log.get("test_response"), agent_type=agent_type),
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

    def run_test(  # noqa: PLR0913
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
        agent_type: str = PASSIVE_TYPE,
        display_label: Optional[str] = None,
        resources_folder: Optional[dict] = None,
    ):
        test_rows: list[dict] = []
        display_label = display_label or tool_key or agent_key

        with Live(
            self.display_test_results([], display_label, agent_type=agent_type, verbose=verbose),
            refresh_per_second=4,
        ) as live:
            def update_live_callback(test_name, test_result, status_code, code, verbose):
                self.update_live_display(
                    test_rows,
                    test_name,
                    test_result,
                    status_code,
                    code,
                    live,
                    display_label,
                    agent_type=agent_type,
                    verbose=verbose,
                )

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
                agent_type,
                update_live_callback,
                verbose,
                resources_folder=resources_folder,
            )

        if verbose:
            self.render_reponse_and_logs(test_logs, agent_type=agent_type)
