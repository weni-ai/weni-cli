from rich import print
from rich.panel import Panel


class Formatter:
    def __init__(self):
        pass

    def print_error_panel(self, message):
        error_panel = Panel(f"[red]Error:[/red] {message}", style="bold red", expand=False)
        print(error_panel)

    def print_success_panel(self, message):
        success_panel = Panel(f"[green]Success:[/green] {message}", style="bold green", expand=False)
        print(success_panel)
