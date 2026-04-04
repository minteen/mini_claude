"""Core abstractions for MiniClaude."""

# Backward compatibility: Tool/ToolResult moved to tools.base
try:
    from mini_claude.tools.base import Tool, ToolResult
except ImportError:
    from mini_claude.core.tool import Tool, ToolResult  # type: ignore

from mini_claude.core.command import Command

__all__ = ["Tool", "ToolResult", "Command"]
