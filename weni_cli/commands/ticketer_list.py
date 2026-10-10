from rich.console import Console
from rich.table import Table

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class TicketerListHandler(Handler):
    def execute(self, **kwargs):
        formatter = Formatter()

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        client = CLIClient()
        results = client.list_ticketers(project_uuid).get("results") or []

        if not results:
            formatter.print_success_panel("No ticketers found")
            return

        table = Table(title="Ticketers")
        table.add_column("UUID")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Created on")

        for ticketer in results:
            table.add_row(
                str(ticketer.get("uuid") or ""),
                str(ticketer.get("name") or ""),
                str(ticketer.get("ticketer_type") or ticketer.get("type") or ""),
                str(ticketer.get("created_on") or ""),
            )

        Console().print(table)
