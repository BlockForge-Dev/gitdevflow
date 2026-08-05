"""Rich console singleton for styled terminal output."""

from rich.console import Console

console = Console()
error_console = Console(stderr=True, style="bold red")
