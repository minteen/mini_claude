"""Configuration settings for MiniClaude."""

import os
from pathlib import Path
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_default_config_dir() -> Path:
    """Get the default configuration directory."""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "mini-claude"


def get_default_data_dir() -> Path:
    """Get the default data directory."""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "mini-claude"


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix="MINICLAUDE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API settings
    api_key: Optional[str] = Field(None, description="API key for Claude API")
    api_base_url: str = Field("https://api.anthropic.com", description="API base URL")
    api_version: str = Field("2023-06-01", description="API version")
    model: str = Field("claude-3-opus-20240229", description="Default model to use")

    # Paths
    config_dir: Path = Field(default_factory=get_default_config_dir)
    data_dir: Path = Field(default_factory=get_default_data_dir)

    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_file: Optional[Path] = Field(None, description="Log file path")

    # CLI
    default_working_dir: Path = Field(default_factory=Path.cwd)

    def model_post_init(self, __context: Any) -> None:
        """Ensure directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
