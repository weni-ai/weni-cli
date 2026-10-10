import json

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class TicketerGetHandler(Handler):
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

        client = CLIClient()
        response = client.get_ticketer(project_uuid, ticketer_uuid)

        name = response.get("name") if isinstance(response, dict) else None
        uuid = response.get("uuid") if isinstance(response, dict) else ticketer_uuid
        ticketer_type = ""
        created_on = ""
        modified_on = ""
        config = {}
        if isinstance(response, dict):
            ticketer_type = response.get("ticketer_type") or response.get("type") or ""
            created_on = response.get("created_on") or ""
            modified_on = response.get("modified_on") or ""
            config = response.get("config") if response.get("config") is not None else {}

        config_text = json.dumps(config, indent=2)
        details = [
            f"Name: {name or ''}",
            f"UUID: {uuid or ticketer_uuid}",
            f"Type: {ticketer_type}",
            f"Created on: {created_on}",
            f"Modified on: {modified_on}",
            f"Config:\n{config_text}",
        ]
        formatter.print_success_panel("\n".join(details))
