import click

from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class ProjectUseHandler(Handler):
    def execute(self, **kwargs):
        project_uuid = kwargs.get("project_uuid")

        store = Store()
        store.set(STORE_PROJECT_UUID_KEY, project_uuid)

        click.echo(f"Project {project_uuid} set as default")
