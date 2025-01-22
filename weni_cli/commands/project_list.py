import click
import click_spinner

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

        click.echo("Fetching projects... Please wait")

        client = WeniClient()
        next_orgs_page_url = None

        while True:
            org_projects_map = {}
            with click_spinner.spinner():
                next_orgs_page_url, org_projects_map = client.list_projects(org_uuid, next_orgs_page_url)

            if not org_projects_map:
                return self.exit("Failed to list projects")

            self.log_orgs(org_projects_map)

            if not next_orgs_page_url:
                break

            value = click.prompt('Press "q" to quit or press "p" to load more projects', type=str, default="p")

            if value == "q":
                break

    def log_orgs(self, org_projects_map):
        # Finds the longest project name to format the output
        max_len = 0
        for org, projects in org_projects_map.items():
            for project in projects:
                if len(project[0]) > max_len:
                    max_len = len(project[0])

        click.echo("\n", nl=False)
        for org, projects in org_projects_map.items():
            click.echo(f"Org {org}")
            for project in projects:
                click.echo(click.style("- ", fg="red"), nl=False)
                click.echo(f"{project[0].ljust(max_len + 2)}{project[1].ljust(len(project[1]) + 2)}")
            click.echo("")
