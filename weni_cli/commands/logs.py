from datetime import datetime
from weni_cli.clients.cli_client import CLIClient
from rich.console import Console
from rich.prompt import Confirm
from rich import print

from weni_cli.formatter.formatter import Formatter


class GetLogsHandler:
    def get_logs(self, agent: str, tool: str, start_time: str, end_time: str, pattern: str):
        console = Console()
        client = CLIClient()
        formatter = Formatter()

        current_token = None
        page = 1
        while True:
            if pattern and pattern.startswith("%") and pattern.endswith("%"):
                formatter.print_error_panel("Regex patterns are not supported")
                return

            with console.status("Fetching logs...", spinner="dots"):
                logs_response, error = client.get_tool_logs(agent, tool, start_time, end_time, pattern, current_token)

            if error:
                formatter.print_error_panel(error)
                return

            if not logs_response or not logs_response.get("logs"):
                if current_token is None:  # Only show "No logs found" on the first request
                    formatter.print_error_panel("No logs found")
                else:
                    print("[bold yellow]No more logs found.[/bold yellow]")
                return

            formatted_logs_str = ""
            for log in logs_response.get("logs"):
                log_time = datetime.fromtimestamp(int(log.get("timestamp")) / 1000)
                formatted_logs_str += f"[{log_time.strftime('%Y-%m-%d %H:%M:%S')}] {log.get('message').strip()}\n"

            with console.pager(links=True):
                console.print(formatted_logs_str.strip())

            current_token = logs_response.get("next_token")

            if current_token:
                if not Confirm.ask("Fetch more logs?", default=True):
                    break
            else:
                # No next token, so we are done
                break

            page += 1
