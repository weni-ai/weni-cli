from rich.console import Console
from rich.table import Table

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.spinner import spinner
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class ChannelListHandler(Handler):
    def execute(self, **kwargs):
        channel_type = kwargs.get("channel_type")
        exclude_wpp_demo = kwargs.get("exclude_wpp_demo", False)

        formatter = Formatter()

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        client = CLIClient()
        with spinner():
            channels = client.list_channels(channel_type=channel_type, exclude_wpp_demo=exclude_wpp_demo)

        if not channels:
            formatter.print_warning_panel("No channels found for this project")
            return

        Console().print(self._build_table(channels))

    def _build_table(self, channels):
        table = Table(title="Channels", expand=True)
        table.add_column("UUID", justify="left", no_wrap=True)
        table.add_column("Name", justify="left")
        table.add_column("Type", justify="center")
        table.add_column("Address", justify="left")
        table.add_column("Active", justify="center")

        for channel in channels:
            table.add_row(
                str(channel.get("uuid") or ""),
                str(channel.get("name") or ""),
                str(channel.get("channel_type") or ""),
                str(channel.get("address") or ""),
                "yes" if channel.get("is_active") else "no",
            )

        return table
