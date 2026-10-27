from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.ticketer_definition import (
    load_ticketer_definition,
    validate_ticketer_definition_schema,
)


class TicketerCreateHandler(Handler):
    def execute(self, **kwargs):
        ticketer_definition_path = kwargs.get("ticketer_definition")

        formatter = Formatter()

        if not ticketer_definition_path:
            formatter.print_error_panel("Ticketer definition path is required")
            return

        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)

        if not project_uuid:
            formatter.print_error_panel("No project selected, please select a project first")
            return

        ticketer_data, error = load_ticketer_definition(ticketer_definition_path)
        if error:
            formatter.print_error_panel(error)
            return

        schema_error = validate_ticketer_definition_schema(ticketer_data)
        if schema_error:
            formatter.print_error_panel(schema_error)
            return

        self._ensure_project_uuid(ticketer_data, project_uuid)

        client = CLIClient()
        response = client.create_ticketer(project_uuid, ticketer_data)

        ticketer_name = response.get("name") if isinstance(response, dict) else None
        ticketer_uuid = response.get("uuid") if isinstance(response, dict) else None

        details = []
        if ticketer_name:
            details.append(f"Name: {ticketer_name}")
        if ticketer_uuid:
            details.append(f"UUID: {ticketer_uuid}")

        if details:
            formatter.print_success_panel("Ticketer created successfully\n" + "\n".join(details))
        else:
            formatter.print_success_panel("Ticketer created successfully")

    def _ensure_project_uuid(self, ticketer_data, project_uuid):
        if not ticketer_data.get("ticketers"):
            return

        config = ticketer_data["ticketers"][0].setdefault("config", {})
        if not config.get("project_uuid", "").strip():
            config["project_uuid"] = project_uuid
