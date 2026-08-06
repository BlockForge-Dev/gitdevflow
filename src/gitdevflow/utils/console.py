"""Rich console singleton with custom theme for styled terminal output."""

from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "error": "bold red",
        "success": "bold green",
        "highlight": "bold yellow",
        "accent": "bold magenta",
        "dim": "dim white",
    }
)

console = Console(theme=custom_theme)
error_console = Console(stderr=True, theme=custom_theme)
