import os
import shutil
import subprocess
import click
import yaml
import sys

from slugify import slugify
from zipfile import ZipFile

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

        if not definition_data:
            return

        skills_files_map = self.load_skills(definition_data)

        if not skills_files_map:
            return

        self.push_definition(force_update, project_uuid, definition_data, skills_files_map)

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
                    skill_file = self.generate_skill_file(skill_slug, skill_data.get("source").get("path"))
                    if not skill_file:
                        return None

                    skills_map[f"{agent_name_slug}:{skill_slug}"] = skill_file

        return skills_map

    def generate_skill_file(self, skill_name, skill_path):
        # install the requirements in the package folder
        self.install_requirements(skill_path)

        # create the zip file with packages and the skill file to be sent as a lambda zip function
        return self.create_skill_zip_file(skill_name, skill_path)

    def install_requirements(self, skill_path):
        requirements_file = f"{skill_path}{os.sep}requirements.txt"

        # check if the requirements file exists
        if not os.path.exists(requirements_file):
            return

        # generate the package folder
        self.create_package_folder(skill_path)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--target",
                    f"{skill_path}{os.sep}package",
                    "-r",
                    requirements_file,
                ]
            )
        except Exception as error:
            click.echo(f"Failed to install requirements for skill path {skill_path}: {error}")

    def create_package_folder(self, skill_path):
        try:
            os.makedirs(f"{skill_path}{os.sep}package")
        except Exception as error:
            click.echo(f"Failed to create package folder for skill path {skill_path}: {error}")
            return None

    def create_skill_zip_file(self, skill_name, skill_path):
        zip_file_name = f"{skill_name}.zip"
        zip_file_path = f"{skill_path}{os.sep}{zip_file_name}"
        package_folder_path = f"{skill_path}{os.sep}package"

        # delete the existing zip file if it exists
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        try:
            with ZipFile(zip_file_path, "w") as z:
                for root, _, files in os.walk(skill_path):
                    # skip the package folder since we need to add its content directly to the root of the zip file
                    if "package" in root:
                        continue

                    # skip the newly created zip file to avoid adding it to itself
                    if zip_file_name in files:
                        files.remove(zip_file_name)

                    # skip the requirements.txt file to avoid adding it to the zip file
                    if "requirements.txt" in files:
                        files.remove("requirements.txt")

                    # skip __pycache__ folders, as recommended by AWS
                    if "__pycache__" in root:
                        continue

                    # add the remaining files to the zip file
                    for file in files:
                        z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), skill_path))

                # add the package folder content to the zip file root if it exists
                if os.path.exists(package_folder_path):
                    for root, _, files in os.walk(package_folder_path):
                        # skip __pycache__ folders, as recommended by AWS
                        if "__pycache__" in root:
                            continue

                        # skip dist-info folders
                        if ".dist-info" in root:
                            continue

                        for file in files:
                            z.write(
                                os.path.join(root, file),
                                os.path.relpath(os.path.join(root, file), package_folder_path),
                            )

                    # clear all the temporary package folder
                    shutil.rmtree(package_folder_path)

            return open(zip_file_path, "rb")
        except Exception as error:
            click.echo(f"Failed to create skill zip file for skill path {skill_path}: {error}")
            return None

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
                            "slug": skill_slug,
                            "name": skill_data.get("name"),
                            "source": skill_data.get("source"),
                            "description": skill_data.get("description"),
                            "parameters": skill_data.get("parameters"),
                        }
                    )

            agents[agent]["skills"] = agent_skills

        return definition

    def push_definition(self, force_update, project_uuid, definition, skill_files_map):
        formatted_definition = self.format_definition(definition)

        client = NexusClient()

        response = client.push_agents(project_uuid, formatted_definition, skill_files_map)

        if response.status_code != 200:
            click.echo(f"Failed to push definition, error: {response.text}")
            return

        click.echo("Definition pushed successfully")
