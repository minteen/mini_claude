"""Command implementations for MiniClaude."""

from mini_claude.commands.base import Command, CommandGroup
from mini_claude.commands.config import (
    ConfigCommandGroup,
    ConfigListCommand,
    ConfigGetCommand,
    ConfigSetCommand,
    ConfigUnsetCommand,
    ConfigEditCommand,
)
from mini_claude.commands.help import HelpCommand
from mini_claude.commands.registry import (
    CommandRegistry,
    discover_commands,
    get_registry,
)
from mini_claude.commands.tool import (
    ToolCommandGroup,
    ToolReadCommand,
    ToolWriteCommand,
    ToolEditCommand,
    ToolGlobCommand,
    ToolGrepCommand,
    ToolBashCommand,
)

__all__ = [
    "Command",
    "CommandGroup",
    "CommandRegistry",
    "discover_commands",
    "get_registry",
    "HelpCommand",
    "ConfigCommandGroup",
    "ConfigListCommand",
    "ConfigGetCommand",
    "ConfigSetCommand",
    "ConfigUnsetCommand",
    "ConfigEditCommand",
    "ToolCommandGroup",
    "ToolReadCommand",
    "ToolWriteCommand",
    "ToolEditCommand",
    "ToolGlobCommand",
    "ToolGrepCommand",
    "ToolBashCommand",
]
