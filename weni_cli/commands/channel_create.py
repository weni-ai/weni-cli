from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.channel_definition import load_channel_definition


class ChannelCreateHandler(Handler):
    def execute(self, **kwargs):
        channel_definition_path = kwargs.get("channel_definition")

        formatter = Formatter()

        if not channel_definition_path:
            formatter.print_error_panel("Channel definition path is required")
            return

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        channel_data, error = load_channel_definition(channel_definition_path)
        if error:
            formatter.print_error_panel(error)
            return

        client = CLIClient()
        client.create_channel(project_uuid, channel_data)
