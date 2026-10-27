import rich_click as click

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.spinner import spinner
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class ChannelDeleteHandler(Handler):
    def execute(self, **kwargs):
        channel_uuid = kwargs.get("channel_uuid")
        skip_confirmation = kwargs.get("yes", False)

        formatter = Formatter()

        if not channel_uuid:
            formatter.print_error_panel("Channel UUID is required")
            return

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        if not skip_confirmation and not click.confirm(
            f"Deactivate channel {channel_uuid}? It will stop sending and receiving messages", default=False
        ):
            formatter.print_warning_panel("Channel deletion cancelled")
            return

        client = CLIClient()
        with spinner():
            client.delete_channel(str(channel_uuid))

        formatter.print_success_panel(f"Channel deactivated successfully\nUUID: {channel_uuid}")
