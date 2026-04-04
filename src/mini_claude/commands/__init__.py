"""
Command implementations for MiniClaude.

This package contains all the CLI command implementations for MiniClaude.
Commands are organized into logical groups and can be automatically
discovered and registered using the CommandRegistry.

Available Commands:
    - Help: Show available commands and help information
    - Chat: Interactive AI chat with tool support
    - Config: Manage application configuration settings
    - Auth: Manage API authentication
    - Tool: Directly invoke built-in tools

Example:
    ```python
    from mini_claude.commands import ChatCommand, CommandRegistry

    # Use a specific command
    chat_cmd = ChatCommand()

    # Discover and register all commands
    registry = CommandRegistry()
    registry.register(ChatCommand())
    ```
"""

from mini_claude.commands.base import Command, CommandGroup
from mini_claude.commands.chat import ChatCommand
from mini_claude.commands.config import (
    AuthCommandGroup,
    AuthStatusCommand,
    AuthLoginCommand,
    AuthLogoutCommand,
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
    "ChatCommand",
    "ConfigCommandGroup",
    "ConfigListCommand",
    "ConfigGetCommand",
    "ConfigSetCommand",
    "ConfigUnsetCommand",
    "ConfigEditCommand",
    "AuthCommandGroup",
    "AuthStatusCommand",
    "AuthLoginCommand",
    "AuthLogoutCommand",
    "ToolCommandGroup",
    "ToolReadCommand",
    "ToolWriteCommand",
    "ToolEditCommand",
    "ToolGlobCommand",
    "ToolGrepCommand",
    "ToolBashCommand",
]
