import json

import rich_click as click

from weni_cli.clients.cli_client import CLIClient, RequestError
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store


class AttachHandler(Handler):
    def execute(self, **kwargs):
        urn_id = kwargs.get("urn_id")
        anchor_type = kwargs.get("anchor_type")
        anchor_value = kwargs.get("anchor_value")
        verified = bool(kwargs.get("verified"))
        project_id = kwargs.get("project_id")

        formatter = Formatter()
        if not project_id:
            project_id = Store().get(STORE_PROJECT_UUID_KEY)
        if not project_id:
            formatter.print_error_panel("No project selected, please select a project first")
            return 1

        try:
            payload = CLIClient().attach_identity(project_id, urn_id, anchor_type, anchor_value, verified)
        except RequestError as exc:
            code = "identity_unavailable"
            if isinstance(exc.data, dict) and exc.data.get("error"):
                code = exc.data["error"]
            click.echo(json.dumps({"error": code}))
            return 1

        click.echo(json.dumps(payload))
        return 0
