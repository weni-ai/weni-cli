from datetime import datetime
from weni_cli.clients.cli_client import CLIClient
from rich.console import Console
from rich.panel import Panel
from rich import print

from weni_cli.formatter.formatter import Formatter


class GetLogsHandler:
    def get_logs(self, agent: str, tool: str, start_time: str, end_time: str):
        console = Console()
        client = CLIClient()

        with console.status("Fetching logs...", spinner="dots"):
            logs_response, error = client.get_tool_logs(agent, tool, start_time, end_time)

        formatter = Formatter()
        if error:
            formatter.print_error_panel(error)
            return

        if not logs_response:
            formatter.print_error_panel("No logs found")
            return

        formatted_logs_str = ""
        for log in logs_response.get("logs"):
            log_time = datetime.fromtimestamp(int(log.get("timestamp")) / 1000)
            formatted_logs_str += f"[{log_time.strftime('%Y-%m-%d %H:%M:%S')}] {log.get('message').strip()}\n"

        print(Panel(
            formatted_logs_str.strip(),
            title="[bold green]Logs[/bold green]",
            title_align="left",
            highlight=True,
        ))
