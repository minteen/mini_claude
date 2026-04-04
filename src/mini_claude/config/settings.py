"""
Configuration settings for MiniClaude.

This module defines the application settings using Pydantic Settings for
type-safe configuration management. Settings can be loaded from environment
variables, .env files, or set programmatically.

The settings are automatically validated and directories are created on
initialization to ensure the application can run properly.

Platform-specific Default Paths:
    - Windows:
        - Config: %APPDATA%\\mini-claude
        - Data: %LOCALAPPDATA%\\mini-claude
    - Linux/macOS:
        - Config: ~/.config/mini-claude
        - Data: ~/.local/share/mini-claude

Example:
    ```python
    from mini_claude.config.settings import settings

    # Access API settings
    if settings.api_key:
        print("API key is configured")

    # Use paths
    conversation_file = settings.data_dir / "conversations" / "my-conv.json"
    ```
"""

import os
from pathlib import Path
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_default_config_dir() -> Path:
    """
    Get the default configuration directory based on the operating system.

    Returns:
        Path object pointing to the default configuration directory.

    Platform-specific behavior:
        - Windows: Uses %APPDATA%\\mini-claude or ~\\AppData\\Roaming\\mini-claude
        - Linux/macOS: Uses $XDG_CONFIG_HOME/mini-claude or ~/.config/mini-claude
    """
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "mini-claude"


def get_default_data_dir() -> Path:
    """
    Get the default data directory based on the operating system.

    Returns:
        Path object pointing to the default data directory.

    Platform-specific behavior:
        - Windows: Uses %LOCALAPPDATA%\\mini-claude or ~\\AppData\\Local\\mini-claude
        - Linux/macOS: Uses $XDG_DATA_HOME/mini-claude or ~/.local/share/mini-claude
    """
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "mini-claude"


class Settings(BaseSettings):
    """
    Application settings for MiniClaude.

    This class uses Pydantic Settings to provide type-safe configuration
    with automatic loading from environment variables and .env files.

    All settings can be overridden via environment variables prefixed with
    'MINICLAUDE_'. For example, MINICLAUDE_API_KEY sets the api_key field.

    Attributes:
        api_key: API key for authenticating with the Claude API
        api_base_url: Base URL for API requests
        api_version: API version to use
        model: Default AI model to use for chat completions
        system_prompt: Default system prompt for conversations
        config_dir: Directory for storing configuration files
        data_dir: Directory for storing application data (conversations, etc.)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        default_working_dir: Default working directory for CLI operations
    """

    model_config = SettingsConfigDict(
        env_prefix="MINICLAUDE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API settings
    api_key: Optional[str] = Field(None, description="API key for Claude API authentication")
    api_base_url: str = Field("https://api.anthropic.com", description="Base URL for API endpoints")
    api_version: str = Field("2023-06-01", description="API version identifier")
    model: str = Field("claude-3-opus-20240229", description="Default AI model for chat completions")
    system_prompt: Optional[str] = Field(None, description="Default system prompt for conversations")

    # Paths
    config_dir: Path = Field(default_factory=get_default_config_dir, description="Directory for configuration files")
    data_dir: Path = Field(default_factory=get_default_data_dir, description="Directory for application data storage")

    # Logging
    log_level: str = Field("INFO", description="Logging verbosity level")
    log_file: Optional[Path] = Field(None, description="Path to log file (stdout if None)")

    # CLI
    default_working_dir: Path = Field(default_factory=Path.cwd, description="Default working directory for commands")

    def model_post_init(self, __context: Any) -> None:
        """
        Post-initialization hook to ensure required directories exist.

        This method is automatically called by Pydantic after the model
        is initialized. It creates the config and data directories if
        they don't already exist.

        Args:
            __context: Context passed by Pydantic (unused)
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
"""
Global application settings instance.

This singleton provides access to the application configuration throughout
the codebase. It's lazily initialized on first import and automatically
loads settings from environment variables and .env files.

Example:
    ```python
    from mini_claude.config.settings import settings

    print(f"Using model: {settings.model}")
    print(f"Config directory: {settings.config_dir}")
    ```
"""
