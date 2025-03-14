from rich import print
from rich.panel import Panel


class Formatter:
    def __init__(self):
        pass

    def print_error_panel(self, message):
        error_panel = Panel(
            f"{message}",
            title="[bold red]Error[/bold red]",
            title_align="left",
            style="bold red",
            expand=False,
            padding=(1, 1),
        )
        print(error_panel)

    def print_success_panel(self, message):
        success_panel = Panel(
            f"{message}",
            title="[bold green]Success[/bold green]",
            title_align="left",
            style="bold green",
            expand=False,
        )
        print(success_panel)
