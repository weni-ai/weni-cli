from typing import Optional
import rich_click as click

from slugify import slugify

from weni_cli.formatter.formatter import Formatter
from weni_cli.clients.cli_client import CLIClient
from weni_cli.handler import Handler
from weni_cli.packager.packager import create_skill_folder_zip
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
            formatter.print_error_panel(error, title="Failed to load definition file")
            return

        skills_folders_map, error = self.load_skills_folders(definition_data)
        if error:
            formatter.print_error_panel(error)
            return

        definition = format_definition(definition_data)
        self.push_definition(force_update, project_uuid, definition, skills_folders_map)

    def load_param(self, params, key, default=None, required=False):
        value = params.get(key, default)
        if required and not value:
            raise Exception(f"Missing required parameter {key}")
        return value

    def load_skills_folders(self, definition) -> tuple[Optional[dict], Optional[str]]:
        skills_folder_map = {}

        agents = definition.get("agents", {})

        for _, agent_data in agents.items():
            skills = agent_data.get("skills", {})
            for skill in skills:
                for _, skill_data in skill.items():
                    agent_name_slug = slugify(agent_data.get("name"))
                    skill_slug = slugify(skill_data.get("name"))
                    skill_folder, error = create_skill_folder_zip(skill_slug, skill_data.get("source").get("path"))
                    if error:
                        return None, f"Failed to create skill folder for skill {skill_data.get('name')} in agent {agent_data.get('name')}\n{error}"

                    skills_folder_map[f"{agent_name_slug}:{skill_slug}"] = skill_folder

        return skills_folder_map, None

    def push_definition(self, force_update, project_uuid, definition, skill_folders_map):
        client = CLIClient()

        client.push_agents(project_uuid, definition, skill_folders_map)

        click.echo("Definition pushed successfully")
