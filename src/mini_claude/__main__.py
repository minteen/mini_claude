"""MiniClaude CLI entry point."""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from mini_claude import __version__

# Initialize Typer app
app = typer.Typer(
    name="mini-claude",
    help="A lightweight Claude Code CLI implementation in Python",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"MiniClaude version: [bold cyan]{__version__}[/bold cyan]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """MiniClaude - A lightweight Claude Code CLI implementation."""
    pass


@app.command(name="hello")
def hello(name: Optional[str] = typer.Argument(None, help="Name to greet")) -> None:
    """Say hello!"""
    if name:
        message = f"Hello, [bold green]{name}[/bold green]!"
    else:
        message = "Hello from MiniClaude!"

    console.print(
        Panel(
            message,
            title="[bold cyan]MiniClaude[/bold cyan]",
            border_style="cyan",
        )
    )


@app.command(name="info")
def info() -> None:
    """Show MiniClaude information."""
    from mini_claude.config.settings import settings

    console.print(f"[bold]Version:[/bold] {__version__}")
    console.print(f"[bold]Config directory:[/bold] {settings.config_dir}")
    console.print(f"[bold]Data directory:[/bold] {settings.data_dir}")
    console.print(f"[bold]Default model:[/bold] {settings.model}")


def run() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    run()
