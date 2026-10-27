from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.spinner import spinner
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.channel_definition import load_yaml_file


class ChannelUpdateHandler(Handler):
    def execute(self, **kwargs):
        channel_uuid = kwargs.get("channel_uuid")
        name = kwargs.get("name")
        address = kwargs.get("address")
        config_file = kwargs.get("config_file")

        formatter = Formatter()

        if not channel_uuid:
            formatter.print_error_panel("Channel UUID is required")
            return

        if name is None and address is None and not config_file:
            formatter.print_error_panel("Provide at least one of --name, --address or --config-file")
            return

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        config = None
        if config_file:
            config, error = load_yaml_file(config_file)
            if error:
                formatter.print_error_panel(f"Could not read config file: {error}")
                return
            if not isinstance(config, dict) or not config:
                formatter.print_error_panel("Config file must contain a non-empty key/value mapping")
                return

        client = CLIClient()
        with spinner():
            response = client.update_channel(str(channel_uuid), name=name, address=address, config=config)

        details = []
        if isinstance(response, dict):
            if response.get("name"):
                details.append(f"Name: {response['name']}")
            if response.get("uuid"):
                details.append(f"UUID: {response['uuid']}")

        if details:
            formatter.print_success_panel("Channel updated successfully\n" + "\n".join(details))
        else:
            formatter.print_success_panel("Channel updated successfully")
