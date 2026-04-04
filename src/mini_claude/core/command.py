"""
Command base class for CLI commands.

This module defines the abstract base class for CLI commands in MiniClaude.
All commands should inherit from this base class and implement the `register`
method to integrate with the Typer application framework.

Note:
    This is the original simple Command base class. For enhanced features
    like aliases, grouping, and hidden commands, use
    `mini_claude.commands.base.Command` instead.

Example:
    ```python
    from mini_claude.core.command import Command
    import typer

    class MyCommand(Command):
        name = "my-command"
        help = "My custom command"

        def register(self, app: typer.Typer) -> None:
            @app.command(name=self.name, help=self.help)
            def my_command():
                print("Hello from my command!")
    ```
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import typer


class Command(ABC):
    """
    Abstract base class for CLI commands.

    This class defines the interface that all CLI commands must implement.
    Each command has a name and help text, and must provide a `register`
    method to add itself to a Typer application.

    Attributes:
        name: The name of the command as it appears in the CLI
        help: Help text describing what the command does
    """

    name: str
    """The name of the command as it appears in the CLI."""

    help: str
    """Help text describing what the command does."""

    @abstractmethod
    def register(self, app: typer.Typer) -> None:
        """
        Register this command with the Typer app.

        This method should add the command to the provided Typer application
        using Typer's decorator syntax or app.command() method.

        Args:
            app: The Typer application instance to register this command with.

        Example:
            ```python
            def register(self, app: typer.Typer) -> None:
                @app.command(name=self.name, help=self.help)
                def command_impl():
                    # Command implementation here
                    pass
            ```
        """
        pass

    def __repr__(self) -> str:
        """
        Return a string representation of the command for debugging.

        Returns:
            String representation showing the command class and name.
        """
        return f"{self.__class__.__name__}(name={self.name!r})"
