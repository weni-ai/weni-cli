import rich_click as click

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class TicketerDeleteHandler(Handler):
    def execute(self, **kwargs):
        formatter = Formatter()
        ticketer_uuid = kwargs.get("ticketer_uuid")

        if not ticketer_uuid:
            formatter.print_error_panel("Ticketer UUID is required")
            return

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        if not kwargs.get("yes"):
            if not click.confirm(
                "This will deactivate the ticketer and close all open tickets. Continue?",
                default=False,
            ):
                formatter.print_warning_panel("Delete cancelled")
                return

        client = CLIClient()
        client.delete_ticketer(project_uuid, ticketer_uuid)
        formatter.print_success_panel(f"Ticketer deleted successfully\nUUID: {ticketer_uuid}")
