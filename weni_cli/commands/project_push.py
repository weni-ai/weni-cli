from typing import Optional
import rich_click as click

from weni_cli.formatter.formatter import Formatter
from weni_cli.clients.cli_client import CLIClient
from weni_cli.handler import Handler
from weni_cli.packager.packager import create_agent_resource_folder_zip
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.definition import (
    format_definition,
    load_agent_definition,
    validate_agent_definition_schema,
    validate_active_agent_definition_schema,
)

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
            formatter.print_error_panel(
                f"Invalid agent definition YAML file format, error:\n{error}", title="Failed to load definition file"
            )
            return

        agent_type = "passive"
        try:
            agents = definition_data.get("agents", {})
            if agents:
                agent = list(agents.values())[0]
                if agent.get("rules"):
                    agent_type = "active"
        except Exception as e:
            formatter.print_error_panel(
                f"Invalid agent definition data format, error:\n{e}", title="Failed to identify agent type"
            )
            return

        if agent_type == "passive":
            self.push_passive_agent(force_update, project_uuid, definition_data)
        elif agent_type == "active":
            self.push_active_agent(force_update, project_uuid, definition_data)

    def push_passive_agent(self, force_update, project_uuid, definition):
        formatter = Formatter()
        error = validate_agent_definition_schema(definition)
        if error:
            formatter.print_error_panel(
                f"Invalid agent definition YAML file format, error:\n{error}", title="Failed to load definition file"
            )
            return

        tools_folders_map, error = self.load_tools_folders(definition)
        if error:
            formatter.print_error_panel(error)
            return

        definition = format_definition(definition)
        self.push_definition(force_update, "passive", project_uuid, definition, tools_folders_map)

    def push_active_agent(self, force_update, project_uuid, definition):
        formatter = Formatter()
        error = validate_active_agent_definition_schema(definition)
        if error:
            formatter.print_error_panel(
                f"Invalid agent definition YAML file format, error:\n{error}", title="Failed to load definition file"
            )
            return
        rules_folders_map, error = self.load_rules_folders(definition)
        if error:
            formatter.print_error_panel(error)
            return

        preprocessing_folders_map, error = self.load_preprocessing_folder(definition)
        if error:
            formatter.print_error_panel(error)
            return

        # merge rules_folders_map and preprocessing_folders_map
        rules_folders_map.update(preprocessing_folders_map)
        resources_folders_map = rules_folders_map
        definition = format_definition(definition)
        self.push_definition(force_update, "active", project_uuid, definition, resources_folders_map)

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
                    tool_folder, error = create_agent_resource_folder_zip(
                        tool_key, tool_data.get("source").get("path")
                    )
                    if error:
                        return (
                            None,
                            f"Failed to create tool folder for tool {tool_data.get('name')} in agent {agent_data.get('name')}\n{error}",
                        )

                    tools_folder_map[f"{agent_key}:{tool_key}"] = tool_folder

        return tools_folder_map, None

    def load_rules_folders(self, definition) -> tuple[Optional[dict], Optional[str]]:
        rules_folder_map = {}

        agents = definition.get("agents", {})
        for agent_key, agent_data in agents.items():
            rules = agent_data.get("rules", {})
            for rule_key, rule_data in rules.items():
                rule_folder, error = create_agent_resource_folder_zip(
                    rule_key, rule_data.get("source").get("path")
                )
                if error:
                    return (
                        None,
                        f"Failed to create rule folder for rule {rule_data.get('name')} in agent {agent_data.get('name')}\n{error}",
                    )

                rules_folder_map[f"{agent_key}:{rule_key}"] = rule_folder

        return rules_folder_map, None

    def load_preprocessing_folder(self, definition) -> tuple[Optional[dict], Optional[str]]:
        preprocessing_folder_map = {}
        preprocessing_key = "preprocessor_folder"

        agents = definition.get("agents", {})
        for agent_key, agent_data in agents.items():
            preprocessing_data = agent_data.get("pre-processing", {})
            preprocessing_folder, error = create_agent_resource_folder_zip(
                "pre-processing", preprocessing_data.get("source").get("path")
            )
            if error:
                return (
                    None,
                    f"Failed to create preprocessing folder for preprocessing {preprocessing_data.get('name')} in agent {agent_data.get('name')}\n{error}",
                )

            preprocessing_folder_map[f"{agent_key}:{preprocessing_key}"] = preprocessing_folder

        return preprocessing_folder_map, None

    def push_definition(self, force_update, agent_type, project_uuid, definition, resources_folder_map):
        client = CLIClient()

        client.push_agents(project_uuid, definition, resources_folder_map, agent_type)

        click.echo("Definition pushed successfully")
