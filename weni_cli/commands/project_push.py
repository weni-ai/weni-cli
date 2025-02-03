import click
import regex
import yaml

from slugify import slugify

from weni_cli.clients.nexus_client import NexusClient
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store

CONTACT_FIELD_NAME_REGEX = r"^[a-z][a-z0-9_]*$"


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

        if not definition_data:
            return

        skills_files_map = self.load_skills(definition_data)

        if not skills_files_map:
            return

        definition = self.format_definition(definition_data)

        if not definition:
            return

        self.push_definition(force_update, project_uuid, definition, skills_files_map)

    def load_param(self, params, key, default=None, required=False):
        value = params.get(key, default)
        if required and not value:
            raise Exception(f"Missing required parameter {key}")
        return value

    def load_definition(self, path):
        with open(path, "r") as file:
            try:
                data = yaml.safe_load(file)
            except Exception as error:
                click.echo(f"Failed to parse definition file: {error}")
                return None

            if not data:
                click.echo("Error: Empty definition file")
                return None

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
                    skill_file = self.open_skill_file(skill_data.get("path"))
                    if not skill_file:
                        return None

                    skills_map[f"{agent_name_slug}:{skill_slug}"] = skill_file

        return skills_map

    def open_skill_file(self, path):
        try:
            skill_file = open(path, "rb")
            return skill_file
        except FileNotFoundError:
            click.echo(f"Failed to load skill file: File {path} not found")
            return None

    # Updates the skills in the definition to be an array of objects containing name, path and slug
    def format_definition(self, definition):
        agents = definition.get("agents", {})

        for agent in agents:
            skills = agents[agent].get("skills", {})
            agent_skills = []
            for skill in skills:
                for skill_name, skill_data in skill.items():

                    parameters, err = self.validate_parameters(skill_data.get("parameters"))

                    if err:
                        click.echo(f"Error in skill {skill_name}: {err}")
                        return None

                    skill_slug = slugify(skill_data.get("name"))
                    agent_skills.append(
                        {
                            "slug": skill_slug,
                            "name": skill_data.get("name"),
                            "path": skill_data.get("path"),
                            "description": skill_data.get("description"),
                            "parameters": parameters,
                        }
                    )

            agents[agent]["skills"] = agent_skills

        return definition

    def validate_parameters(self, parameters: dict) -> tuple[any, str]:
        if not parameters:
            return None, None

        def error(name, message):
            return f"parameter {name}: {message}"

        for parameter in parameters:
            for parameter_name, parameter_data in parameter.items():
                if not isinstance(parameter_data, dict):
                    return None, error(parameter_name, "must be an object")

                if not parameter_data.get("description"):
                    return None, error(parameter_name, "description is required")

                if type(parameter_data.get("description")) != str:
                    return None, error(parameter_name, "description must be a string")

                if not parameter_data.get("type"):
                    return None, error(parameter_name, "type is required")

                if parameter_data.get("type") not in ["string", "number", "integer", "boolean", "array"]:
                    return (
                        None,
                        error(parameter_name, "type must be one of: string, number, integer, boolean, array"),
                    )

                if type(parameter_data.get("required", None)) != bool:
                    return None, error(parameter_name, "'required' field must be a boolean")

                if parameter_data.get("contact_field", None) and type(parameter_data.get("contact_field")) != bool:
                    return None, error(parameter_name, "contact_field must be a boolean")

                if parameter_data.get("contact_field", None) and not self.is_valid_contact_field_name(parameter_name):
                    return (
                        None,
                        error(
                            parameter_name,
                            f"parameter name must match the regex of a valid contact field: {CONTACT_FIELD_NAME_REGEX}",
                        ),
                    )

        return parameters, None

    def is_valid_contact_field_name(self, parameter_name):
        if not regex.match(CONTACT_FIELD_NAME_REGEX, parameter_name, regex.V0):
            return False
        return True

    def push_definition(self, force_update, project_uuid, definition, skill_files_map):
        client = NexusClient()

        response = client.push_agents(project_uuid, definition, skill_files_map)

        if response.status_code != 200:
            click.echo(f"Failed to push definition, error: {response.text}")
            return

        click.echo("Definition pushed successfully")
