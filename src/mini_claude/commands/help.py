"""Help command for MiniClaude."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mini_claude.commands.base import Command
from mini_claude.commands.registry import get_registry

console = Console()


class HelpCommand(Command):
    """Show help information about MiniClaude commands."""

    name = "help"
    help = "Show help information about MiniClaude commands"
    aliases = ["h"]
    group = "info"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def help_command(
            command_name: Optional[str] = typer.Argument(None, help="Command to show help for"),
        ) -> None:
            self._run(command_name)

    def _run(self, command_name: Optional[str] = None) -> None:
        registry = get_registry()

        if command_name:
            self._show_command_help(command_name, registry)
        else:
            self._show_all_commands(registry)

    def _show_all_commands(self, registry) -> None:
        from mini_claude import __version__

        console.print()
        console.print(Panel(
            f"[bold cyan]MiniClaude[/bold cyan] - A lightweight Claude Code CLI\n"
            f"Version: [bold green]{__version__}[/bold green]",
            border_style="cyan",
        ))
        console.print()

        # Show commands by group
        groups = registry.list_groups()

        if "info" in groups:
            self._show_group("Information Commands", registry.list_by_group("info"))

        if "config" in groups:
            self._show_group("Configuration Commands", registry.list_by_group("config"))

        if "tools" in groups:
            self._show_group("Tool Commands", registry.list_by_group("tools"))

        # Show other commands
        other_commands = [
            cmd for cmd in registry.list_commands()
            if cmd.group is None
        ]
        if other_commands:
            self._show_group("Other Commands", other_commands)

        console.print()
        console.print("[dim]Use 'mini-claude help <command>' for more information about a command.[/dim]")
        console.print()

    def _show_group(self, title: str, commands) -> None:
        if not commands:
            return

        console.print(f"[bold]{title}[/bold]")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        for cmd in sorted(commands, key=lambda c: c.name):
            cmd_name = cmd.name
            if cmd.aliases:
                cmd_name += f" [dim]({', '.join(cmd.aliases)})[/dim]"
            table.add_row(cmd_name, cmd.help)

        console.print(table)
        console.print()

    def _show_command_help(self, command_name: str, registry) -> None:
        command = registry.get(command_name)

        if command is None:
            console.print(f"[red]Unknown command:[/red] {command_name}")
            console.print()
            console.print("Available commands:")
            for cmd in registry.list_commands():
                console.print(f"  - [cyan]{cmd.name}[/cyan]")
            console.print()
            raise typer.Exit(1)

        console.print()
        console.print(Panel(
            f"[bold cyan]{command.name}[/bold cyan]\n\n{command.help}",
            border_style="cyan",
        ))
        console.print()

        if command.aliases:
            console.print(f"[bold]Aliases:[/bold] {', '.join(command.aliases)}")
            console.print()

        if command.group:
            console.print(f"[bold]Group:[/bold] {command.group}")
            console.print()

        console.print("[dim]Usage: mini-claude [OPTIONS] COMMAND [ARGS]...[/dim]")
        console.print()
