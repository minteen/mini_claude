"""Enhanced Command base class with grouping and aliases."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

import typer


class Command(ABC):
    """Abstract base class for CLI commands with enhanced features."""

    name: str
    help: str
    aliases: List[str] = []
    group: Optional[str] = None
    hidden: bool = False

    @abstractmethod
    def register(self, app: typer.Typer) -> None:
        """
        Register this command with the Typer app.

        Args:
            app: The Typer application to register with
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, group={self.group!r})"


class CommandGroup(Command):
    """A command that contains subcommands."""

    def __init__(self, name: str, help: str, aliases: List[str] = [], group: Optional[str] = None):
        self.name = name
        self.help = help
        self.aliases = aliases
        self.group = group
        self.subcommands: List[Command] = []
        self._app: Optional[typer.Typer] = None

    def add_command(self, command: Command) -> None:
        """Add a subcommand to this group."""
        self.subcommands.append(command)

    def register(self, app: typer.Typer) -> None:
        """Register this command group and all its subcommands."""
        self._app = typer.Typer(
            name=self.name,
            help=self.help,
            rich_markup_mode="rich",
        )
        for cmd in self.subcommands:
            cmd.register(self._app)
        app.add_typer(self._app, name=self.name)
