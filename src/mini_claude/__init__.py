"""
MiniClaude - A lightweight Claude Code CLI implementation in Python.

MiniClaude is a command-line interface that brings Claude Code's AI-powered
development assistance to your terminal. It provides interactive chat,
tool execution, and conversation management capabilities.

Key Features:
- Interactive chat mode with AI assistant
- Built-in tools for file operations (Read, Write, Edit)
- File searching with Glob and Grep tools
- Shell command execution via Bash tool
- Conversation history persistence
- Configurable API settings
- Multiple command groups for organized functionality

Example:
    ```bash
    # Start interactive chat
    mini-claude chat

    # One-shot question
    mini-claude chat "Explain Python decorators"

    # Configure API key
    mini-claude auth login
    ```
"""

__version__ = "0.1.0"
"""The current version of the MiniClaude package."""
