import json

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.spinner import spinner
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store

SECRET_KEY_MARKERS = ("token", "secret", "password", "key")
MASKED_VALUE = "****"


def mask_secrets(value):
    if isinstance(value, dict):
        return {
            key: MASKED_VALUE
            if any(marker in str(key).lower() for marker in SECRET_KEY_MARKERS)
            else mask_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [mask_secrets(item) for item in value]
    return value


class ChannelGetHandler(Handler):
    def execute(self, **kwargs):
        channel_uuid = kwargs.get("channel_uuid")
        show_secrets = kwargs.get("show_secrets", False)

        formatter = Formatter()

        if not channel_uuid:
            formatter.print_error_panel("Channel UUID is required")
            return

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        client = CLIClient()
        with spinner():
            channel = client.get_channel(str(channel_uuid))

        config = channel.get("config") or {}
        if not show_secrets:
            config = mask_secrets(config)

        details = [
            f"UUID: {channel.get('uuid', '')}",
            f"Name: {channel.get('name', '')}",
            f"Type: {channel.get('channel_type', '')}",
            f"Address: {channel.get('address') or ''}",
            f"Active: {'yes' if channel.get('is_active') else 'no'}",
            f"Project: {channel.get('org') or ''}",
            "Config:",
            json.dumps(config, indent=2, ensure_ascii=False),
        ]

        formatter.print_success_panel("\n".join(details))
