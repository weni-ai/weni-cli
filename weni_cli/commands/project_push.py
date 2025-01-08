import click
import yaml

from slugify import slugify

from weni_cli.clients.nexus_client import NexusClient
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class ProjectPushHandler(Handler):
    def execute(self, **kwargs):
        force_update = self.load_param(kwargs, "force_update", False)
        definition_path = self.load_param(kwargs, "definition", None, True)

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            click.echo("No project selected, please select a project first")
            return

        definition_data = self.load_definition(definition_path)

        skills_files_map = self.load_skills(definition_data)

        self.push_definition(
            force_update, project_uuid, definition_data, skills_files_map
        )

    def load_param(self, params, key, default=None, required=False):
        value = params.get(key, default)
        if required and not value:
            raise Exception(f"Missing required parameter {key}")
        return value

    def load_definition(self, path):
        with open(path, "r") as file:
            data = yaml.safe_load(file)

            if not data:
                click.echo("Failed to load definition file")
                return

            return data

    def load_skills(self, definition):
        skills_map = {}

        agents = definition.get("agents", {})

        for _, agent_data in agents.items():
            skills = agent_data.get("skills", {})
            for skill in skills:
                for _, skill_data in skill.items():
                    agent_name_slug = slugify(agent_data.get("name"))
                    skill_slug = slugify(skill_data.get("name"))
                    skill_file = open(skill_data.get("path"), "rb")

                    skills_map[f"{agent_name_slug}:{skill_slug}"] = skill_file

        return skills_map

    # Updates the skills in the definition to be an array of objects containing name, path and slug
    def format_definition(self, definition):
        agents = definition.get("agents", {})

        for agent in agents:
            skills = agents[agent].get("skills", {})
            agent_skills = []
            for skill in skills:
                for _, skill_data in skill.items():
                    skill_slug = slugify(skill_data.get("name"))
                    agent_skills.append(
                        {
                            "name": skill_data.get("name"),
                            "path": skill_data.get("path"),
                            "slug": skill_slug,
                        }
                    )

            agents[agent]["skills"] = agent_skills

        return definition

    def push_definition(self, force_update, project_uuid, definition, skill_files_map):
        formatted_definition = self.format_definition(definition)

        client = NexusClient()

        client.push_agents(project_uuid, formatted_definition, skill_files_map)

        click.echo("Definition pushed successfully")
