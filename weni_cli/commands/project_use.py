from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.store import STORE_PROJECT_UUID_KEY, STORE_TOKEN_KEY, Store


class ProjectUseHandler(Handler):
    def execute(self, **kwargs):
        project_uuid = kwargs.get("project_uuid")

        store = Store()
        formatter = Formatter()

        if not store.get(STORE_TOKEN_KEY):
            formatter.print_error_panel("You are not logged in. Please login to continue.")
            return

        cli_client = CLIClient()
        try:
            cli_client.check_project_permission(project_uuid)
        except Exception as e:
            formatter.print_error_panel(e)
            return

        store.set(STORE_PROJECT_UUID_KEY, project_uuid)

        formatter.print_success_panel(f"Project [underline]{project_uuid}[/underline] set as default")
