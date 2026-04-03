"""Config command group for MiniClaude."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from mini_claude.commands.base import Command, CommandGroup
from mini_claude.config.settings import settings

console = Console()


class ConfigCommandGroup(CommandGroup):
    """Configuration management command group."""

    name = "config"
    help = "Manage MiniClaude configuration"
    aliases = ["cfg"]
    group = "config"

    def __init__(self):
        super().__init__(
            name=self.name,
            help=self.help,
            aliases=self.aliases,
            group=self.group,
        )
        self.add_command(ConfigListCommand())
        self.add_command(ConfigGetCommand())
        self.add_command(ConfigSetCommand())
        self.add_command(ConfigUnsetCommand())
        self.add_command(ConfigEditCommand())


class ConfigListCommand(Command):
    """List all configuration values."""

    name = "list"
    help = "List all configuration values"
    group = "config"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def list_config(
            show_all: bool = typer.Option(False, "--all", "-a", help="Show all settings including empty ones"),
            show_source: bool = typer.Option(False, "--source", "-s", help="Show where each setting is defined"),
        ) -> None:
            self._run(show_all, show_source)

    def _run(self, show_all: bool, show_source: bool) -> None:
        settings_dict = settings.model_dump()

        table = Table(show_header=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        if show_source:
            table.add_column("Source", style="dim")

        for key, value in sorted(settings_dict.items()):
            if not show_all and (value is None or value == ""):
                continue

            # Mask sensitive values
            if key in ["api_key", "anthropic_api_key"] and value:
                value = "****" + str(value)[-4:] if len(str(value)) > 4 else "****"

            if show_source:
                table.add_row(key, str(value) if value is not None else "", "TODO")
            else:
                table.add_row(key, str(value) if value is not None else "")

        console.print()
        console.print("[bold]Configuration:[/bold]")
        console.print(table)
        console.print()
        config_file = Path(settings.config_dir) / "config.env"
        console.print(f"[dim]Config file: {config_file if config_file.exists() else 'Not found (will be created on first set)'}[/dim]")
        console.print()


class ConfigGetCommand(Command):
    """Get a configuration value."""

    name = "get"
    help = "Get a configuration value"
    group = "config"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def get_config(
            key: str = typer.Argument(..., help="Configuration key to get"),
        ) -> None:
            self._run(key)

    def _run(self, key: str) -> None:
        settings_dict = settings.model_dump()

        if key not in settings_dict:
            console.print(f"[red]Unknown config key:[/red] {key}")
            console.print()
            console.print("Available keys:")
            for k in sorted(settings_dict.keys()):
                console.print(f"  - [cyan]{k}[/cyan]")
            console.print()
            raise typer.Exit(1)

        value = settings_dict[key]

        # Mask sensitive values
        if key in ["api_key", "anthropic_api_key"] and value:
            value = "****" + str(value)[-4:] if len(str(value)) > 4 else "****"

        console.print()
        console.print(f"[cyan]{key}[/cyan] = [green]{value if value is not None else '(not set)'}[/green]")
        console.print()


class ConfigSetCommand(Command):
    """Set a configuration value."""

    name = "set"
    help = "Set a configuration value"
    group = "config"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def set_config(
            key: str = typer.Argument(..., help="Configuration key to set"),
            value: str = typer.Argument(..., help="Value to set"),
        ) -> None:
            self._run(key, value)

    def _run(self, key: str, value: str) -> None:
        settings_dict = settings.model_dump()

        if key not in settings_dict:
            console.print(f"[red]Unknown config key:[/red] {key}")
            console.print()
            console.print("Available keys:")
            for k in sorted(settings_dict.keys()):
                console.print(f"  - [cyan]{k}[/cyan]")
            console.print()
            raise typer.Exit(1)

        # Ensure config directory exists
        config_dir = Path(settings.config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = Path(settings.config_dir) / "config.env"

        # Read existing config
        lines = []
        if config_file.exists():
            lines = config_file.read_text(encoding="utf-8").splitlines()

        # Find and replace or append
        key_upper = key.upper()
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key_upper}=") or line.startswith(f"#{key_upper}="):
                lines[i] = f"{key_upper}={value}"
                found = True
                break

        if not found:
            lines.append(f"{key_upper}={value}")

        # Write back
        config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        console.print()
        console.print(f"[green]✓[/green] Set [cyan]{key}[/cyan] = [green]{'****' if key in ['api_key', 'anthropic_api_key'] else value}[/green]")
        console.print()


class ConfigUnsetCommand(Command):
    """Unset a configuration value."""

    name = "unset"
    help = "Unset a configuration value"
    group = "config"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def unset_config(
            key: str = typer.Argument(..., help="Configuration key to unset"),
        ) -> None:
            self._run(key)

    def _run(self, key: str) -> None:
        settings_dict = settings.model_dump()

        if key not in settings_dict:
            console.print(f"[red]Unknown config key:[/red] {key}")
            console.print()
            raise typer.Exit(1)

        config_dir = Path(settings.config_dir)
        config_file = Path(settings.config_dir) / "config.env"

        if not config_file.exists():
            console.print()
            console.print("[yellow]Config file does not exist, nothing to unset[/yellow]")
            console.print()
            return

        # Read existing config
        lines = config_file.read_text(encoding="utf-8").splitlines()

        # Remove the key
        key_upper = key.upper()
        new_lines = []
        removed = False
        for line in lines:
            if line.startswith(f"{key_upper}="):
                removed = True
            elif line.startswith(f"#{key_upper}="):
                removed = True
            else:
                new_lines.append(line)

        # Write back
        config_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        if removed:
            console.print()
            console.print(f"[green]✓[/green] Unset [cyan]{key}[/cyan]")
            console.print()
        else:
            console.print()
            console.print(f"[yellow]Key [cyan]{key}[/cyan] not found in config file[/yellow]")
            console.print()


class ConfigEditCommand(Command):
    """Open configuration file in editor."""

    name = "edit"
    help = "Open configuration file in editor"
    group = "config"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def edit_config() -> None:
            self._run()

    def _run(self) -> None:
        config_dir = Path(settings.config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = Path(settings.config_dir) / "config.env"

        # Create empty file if it doesn't exist
        if not config_file.exists():
            config_file.write_text("# MiniClaude Configuration\n", encoding="utf-8")

        # Get editor from environment or default
        editor = os.environ.get("EDITOR")
        if not editor:
            if sys.platform == "win32":
                editor = "notepad.exe"
            else:
                editor = "nano"

        console.print()
        console.print(f"Opening [cyan]{config_file}[/cyan] in [green]{editor}[/green]...")
        console.print()

        try:
            subprocess.run([editor, str(config_file)], check=True)
        except Exception as e:
            console.print(f"[red]Failed to open editor:[/red] {e}")
            console.print()
            console.print(f"You can edit the file manually: {config_file}")
            console.print()
            raise typer.Exit(1)
