import click

from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class ProjectCurrentHandler(Handler):
    def execute(self):
        store = Store()
        project = store.get(STORE_PROJECT_UUID_KEY)
        click.echo(f"Current project: {project}")
