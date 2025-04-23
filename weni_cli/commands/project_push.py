from typing import Optional
import rich_click as click

from weni_cli.formatter.formatter import Formatter
from weni_cli.clients.cli_client import CLIClient
from weni_cli.handler import Handler
from weni_cli.packager.packager import create_tool_folder_zip
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.definition import format_definition, load_agent_definition

CONTACT_FIELD_NAME_REGEX = r"^[a-z][a-z0-9_]*$"


class ProjectPushHandler(Handler):
    def execute(self, **kwargs):
        force_update = self.load_param(kwargs, "force_update", False)
        definition_path = self.load_param(kwargs, "definition", None, True)

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        formatter = Formatter()

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        definition_data, error = load_agent_definition(definition_path)
        if error:
            formatter.print_error_panel(f"Invalid agent definition YAML file format, error:\n{error}", title="Failed to load definition file")
            return

        tools_folders_map, error = self.load_tools_folders(definition_data)
        if error:
            formatter.print_error_panel(error)
            return

        definition = format_definition(definition_data)
        self.push_definition(force_update, project_uuid, definition, tools_folders_map)

    def load_param(self, params, key, default=None, required=False):
        value = params.get(key, default)
        if required and not value:
            raise Exception(f"Missing required parameter {key}")
        return value

    def load_tools_folders(self, definition) -> tuple[Optional[dict], Optional[str]]:
        tools_folder_map = {}

        agents = definition.get("agents", {})

        for agent_key, agent_data in agents.items():
            tools = agent_data.get("tools", {})
            for tool in tools:
                for tool_key, tool_data in tool.items():
                    tool_folder, error = create_tool_folder_zip(tool_key, tool_data.get("source").get("path"))
                    if error:
                        return None, f"Failed to create tool folder for tool {tool_data.get('name')} in agent {agent_data.get('name')}\n{error}"

                    tools_folder_map[f"{agent_key}:{tool_key}"] = tool_folder

        return tools_folder_map, None

    def push_definition(self, force_update, project_uuid, definition, tool_folders_map):
        client = CLIClient()

        client.push_agents(project_uuid, definition, tool_folders_map)

        click.echo("Definition pushed successfully")
