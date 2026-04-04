"""
Configuration management for MiniClaude.

This module provides access to application settings through a global
`settings` instance. Settings can be configured via environment variables,
.env files, or programmatically.

Environment Variables:
    MINICLAUDE_API_KEY: API key for authentication
    MINICLAUDE_API_BASE_URL: Base URL for the API endpoint
    MINICLAUDE_MODEL: Default model to use
    MINICLAUDE_CONFIG_DIR: Directory for configuration files
    MINICLAUDE_DATA_DIR: Directory for data storage

Example:
    ```python
    from mini_claude.config import settings

    # Access settings
    print(settings.model)
    print(settings.config_dir)

    # Settings are automatically created
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    ```
"""

from mini_claude.config.settings import settings, Settings

__all__ = ["settings", "Settings"]
