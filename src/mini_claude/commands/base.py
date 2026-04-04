"""
Enhanced Command base class with grouping and aliases.

This module provides an enhanced Command base class that extends the simple
core Command class with additional features like command aliases, grouping,
and hidden commands. It also includes a CommandGroup class for creating
nested command hierarchies.

Features:
    - Command aliases for alternative invocation names
    - Command grouping for organizing related commands
    - Hidden commands that don't appear in help listings
    - CommandGroup for creating subcommand hierarchies

Example:
    ```python
    from mini_claude.commands.base import Command, CommandGroup
    import typer

    class MyCommand(Command):
        name = "my-command"
        help = "My custom command"
        aliases = ["mc", "mycmd"]
        group = "utils"

        def register(self, app: typer.Typer) -> None:
            @app.command(name=self.name, help=self.help)
            def my_command():
                print("Hello from my command!")

    # Create a command group
    group = CommandGroup("tools", "Tool commands")
    group.add_command(MyCommand())
    ```
"""

from abc import ABC, abstractmethod
from typing import List, Optional

import typer


class Command(ABC):
    """
    Abstract base class for CLI commands with enhanced features.

    This class extends the simple core Command class with additional
    functionality for command aliases, grouping, and visibility control.

    Attributes:
        name: The primary name of the command
        help: Help text describing what the command does
        aliases: List of alternative names for the command
        group: Optional group name for organizing related commands
        hidden: Whether the command should be hidden from help listings
    """

    name: str
    """The primary name of the command as it appears in the CLI."""

    help: str
    """Help text describing what the command does."""

    aliases: List[str] = []
    """List of alternative names that can be used to invoke the command."""

    group: Optional[str] = None
    """Optional group name for categorizing related commands in help output."""

    hidden: bool = False
    """Whether the command should be hidden from help listings."""

    @abstractmethod
    def register(self, app: typer.Typer) -> None:
        """
        Register this command with the Typer app.

        This method should implement the logic to add the command to
        the provided Typer application using Typer's decorator or
        command registration API.

        Args:
            app: The Typer application instance to register with.
        """
        pass

    def __repr__(self) -> str:
        """
        Return a string representation of the command for debugging.

        Returns:
            String showing the command class, name, and group.
        """
        return f"{self.__class__.__name__}(name={self.name!r}, group={self.group!r})"


class CommandGroup(Command):
    """
    A command that contains subcommands.

    This class allows creating nested command hierarchies. A CommandGroup
    can contain multiple subcommands, which are registered as subcommands
    under the group's name.

    Example:
        ```python
        group = CommandGroup("config", "Configuration commands")
        group.add_command(ConfigSetCommand())
        group.add_command(ConfigGetCommand())
        group.register(app)
        ```
    """

    def __init__(self, name: str, help: str, aliases: List[str] = [], group: Optional[str] = None):
        """
        Initialize a CommandGroup.

        Args:
            name: The name of the command group
            help: Help text describing the group
            aliases: Optional list of alternative names for the group
            group: Optional parent group for this group
        """
        self.name = name
        self.help = help
        self.aliases = aliases
        self.group = group
        self.subcommands: List[Command] = []
        self._app: Optional[typer.Typer] = None

    def add_command(self, command: Command) -> None:
        """
        Add a subcommand to this group.

        Args:
            command: The Command instance to add as a subcommand.
        """
        self.subcommands.append(command)

    def register(self, app: typer.Typer) -> None:
        """
        Register this command group and all its subcommands.

        This method creates a new Typer app for the group, registers
        all subcommands with it, then adds the group as a subcommand
        to the parent app.

        Args:
            app: The parent Typer application to register with.
        """
        self._app = typer.Typer(
            name=self.name,
            help=self.help,
            rich_markup_mode="rich",
        )
        for cmd in self.subcommands:
            cmd.register(self._app)
        app.add_typer(self._app, name=self.name)
