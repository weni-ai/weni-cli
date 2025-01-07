import click

from weni_cli.clients.weni_client import WeniClient
from weni_cli.handler import Handler
from weni_cli.store import STORE_TOKEN_KEY, Store


class ProjectListHandler(Handler):
    def execute(self, **kwargs):
        store = Store()

        if not store.get(STORE_TOKEN_KEY):
            click.echo("Missing login authorization, please login first")
            return

        org_uuid = kwargs.get("org_uuid", None)

        client = WeniClient()
        org_projects_map = client.list_projects(org_uuid)

        if not org_projects_map:
            return self.exit("Failed to list projects")

        self.log_orgs(org_projects_map)

    def log_orgs(self, org_projects_map):
        # Finds the longest organization name to format the output
        max_len = 0
        for org in org_projects_map.keys():
            if len(org) > max_len:
                max_len = len(org)

        click.echo("")
        for org, projects in org_projects_map.items():
            click.echo(f"Org {org}")
            for project in projects:
                click.echo(click.style("- ", fg="red"), nl=False)
                click.echo(f" {project[0].ljust(max_len + 2)}{project[1].ljust(38)}")
            click.echo("")
