import click

from slugify import slugify

from weni_cli.clients.cli_client import CLIClient
from weni_cli.handler import Handler
from weni_cli.packager.packager import create_skill_folder_zip
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.definition import format_definition, load_definition


DEFAULT_TEST_DEFINITION_FILE = "test_definition.yaml"


class RunHandler(Handler):
    def execute(self, **kwargs):
        definition_path = kwargs.get("definition")
        agent_name = kwargs.get("agent")
        skill_name = kwargs.get("skill")
        test_definition_path = kwargs.get("test_definition")
        verbose = kwargs.get("verbose", False)
        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            click.echo("No project selected, please select a project first")
            return

        definition_data = load_definition(definition_path)

        if not definition_data:
            return

        if not test_definition_path:
            test_definition_path = self.load_default_test_definition(definition_data, agent_name, skill_name)

            if not test_definition_path:
                click.echo(
                    f"Error: Failed to get default test definition file: {DEFAULT_TEST_DEFINITION_FILE} in skill folder."
                )
                click.echo("You can use the --file option to specify a different file.")
                return

        skill_folder = self.load_skill_folder(definition_data, agent_name, skill_name)

        if not skill_folder:
            click.echo("Error: Failed to load skill folder")
            return

        definition = format_definition(definition_data)

        if not definition:
            return

        test_definition = load_definition(test_definition_path)

        if not test_definition:
            return

        skill_source_path = self.get_skill_source_path(definition_data, agent_name, skill_name)

        credentials = self.load_skill_credentials(skill_source_path)

        skill_globals = self.load_skill_globals(skill_source_path)

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

    def get_skill_source_path(self, definition, agent_name, skill_name) -> str | None:
        for _, data in definition.get("agents", {}).items():
            if data.get("name") == agent_name:
                for skill in data.get("skills", []):
                    for _, skill_data in skill.items():
                        if skill_data.get("name") == skill_name:
                            return skill_data.get("source", {}).get("path")
        return None

    def load_skill_credentials(self, skill_source_path: str) -> dict | None:
        credentials = {}
        with open(f"{skill_source_path}/.env", "r") as file:
            for line in file:
                key, value = line.strip().split("=")
                credentials[key] = value
        return credentials

    def load_skill_globals(self, skill_source_path: str) -> dict | None:
        globals = {}
        with open(f"{skill_source_path}/.globals", "r") as file:
            for line in file:
                key, value = line.strip().split("=")
                globals[key] = value
        return globals

    def load_default_test_definition(self, definition, agent_name, skill_name) -> str | None:
        try:
            definition_path = None

            for _, data in definition.get("agents", {}).items():
                if data.get("name") == agent_name:
                    for skill in data.get("skills", []):
                        for _, skill_data in skill.items():
                            if skill_data.get("name") == skill_name:
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

    def load_skill_folder(self, definition, agent_name, skill_name) -> bytes:
        agent_data = None
        for _, data in definition.get("agents", {}).items():
            if data.get("name") == agent_name:
                agent_data = data
                break

        if not agent_data:
            click.echo(f"Error: Agent {agent_name} not found in definition")
            return None

        skills = agent_data.get("skills", [])

        skill_data = None
        for skill in skills:
            for _, data in skill.items():
                if data.get("name") == skill_name:
                    skill_data = data
                    break

        if not skill_data:
            click.echo(f"Error: Skill {skill_name} not found in agent {agent_name}")
            return None

        skill_slug = slugify(skill_data.get("name"))
        skill_folder = create_skill_folder_zip(skill_slug, skill_data.get("source").get("path"))

        if not skill_folder:
            click.echo(f"Error: Failed to create skill folder for skill {skill_name} in agent {agent_name}")
            return None

        return skill_folder

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
        client = CLIClient()

        client.run_test(
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

        click.echo(click.style("Test completed", fg="green"))
