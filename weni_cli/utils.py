"""Utility functions for the Weni CLI."""

import importlib.metadata
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S%Z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S.%f%Z"
]


def print_version(ctx, param, value):
    """Print the CLI version in a formatted panel.

    Used as a callback for the --version flag.
    """
    if not value or ctx.resilient_parsing:
        return

    console = Console()
    version = importlib.metadata.version("weni-cli")

    version_text = Text(f"Weni CLI v{version}", style="bold green")
    panel = Panel(version_text, title="Version", border_style="blue", expand=False, title_align="left", padding=(1, 2))

    console.print(panel)
    ctx.exit(0)
