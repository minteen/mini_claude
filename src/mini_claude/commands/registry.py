"""Command registry for automatic discovery and registration."""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type

import typer

from mini_claude.commands.base import Command


class CommandRegistry:
    """Registry for discovering and managing CLI commands."""

    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._commands_by_alias: Dict[str, Command] = {}
        self._commands_by_group: Dict[str, List[Command]] = {}

    def register(self, command: Command) -> None:
        """Register a command with the registry."""
        self._commands[command.name] = command

        for alias in command.aliases:
            self._commands_by_alias[alias] = command

        if command.group:
            if command.group not in self._commands_by_group:
                self._commands_by_group[command.group] = []
            self._commands_by_group[command.group].append(command)

    def get(self, name: str) -> Optional[Command]:
        """Get a command by name or alias."""
        if name in self._commands:
            return self._commands[name]
        return self._commands_by_alias.get(name)

    def list_commands(self, include_hidden: bool = False) -> List[Command]:
        """List all registered commands."""
        return [
            cmd for cmd in self._commands.values()
            if include_hidden or not cmd.hidden
        ]

    def list_by_group(self, group: str) -> List[Command]:
        """List commands in a specific group."""
        return self._commands_by_group.get(group, [])

    def list_groups(self) -> List[str]:
        """List all command groups."""
        return list(self._commands_by_group.keys())

    def register_all(self, app: typer.Typer, include_hidden: bool = False) -> None:
        """Register all commands with the Typer app."""
        for command in self.list_commands(include_hidden=include_hidden):
            command.register(app)


def discover_commands(package_path: Optional[str] = None) -> CommandRegistry:
    """
    Automatically discover and register all Command subclasses.

    Args:
        package_path: Optional path to the commands package.
            If None, uses mini_claude.commands.

    Returns:
        CommandRegistry with all discovered commands.
    """
    registry = CommandRegistry()

    if package_path is None:
        import mini_claude.commands
        package = mini_claude.commands
        package_path = str(Path(mini_claude.commands.__file__).parent)
    else:
        package_name = "mini_claude.commands"
        package = importlib.import_module(package_name)

    # Discover all modules in the commands package
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        if module_name.startswith("_"):
            continue

        try:
            module = importlib.import_module(f"{package.__name__}.{module_name}")

            # Find all Command subclasses in the module
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Command)
                    and obj is not Command
                    and not inspect.isabstract(obj)
                ):
                    # Instantiate and register the command
                    command = obj()
                    registry.register(command)
        except Exception as e:
            # Skip modules that fail to import
            pass

    return registry


# Global registry instance
_registry: Optional[CommandRegistry] = None


def get_registry() -> CommandRegistry:
    """Get the global command registry (lazy initialized)."""
    global _registry
    if _registry is None:
        _registry = discover_commands()
    return _registry
