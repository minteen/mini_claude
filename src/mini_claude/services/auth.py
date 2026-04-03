"""Authentication and authorization module for API key management."""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from mini_claude.config.settings import settings
from mini_claude.services.api_client import OpenAIClient


class APIKeyManager:
    """Manager for API key storage, validation, and masking."""

    # Cache for validation results
    _validation_cache: Optional[Tuple[bool, datetime]] = None
    _validation_cache_duration = timedelta(minutes=5)

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """
        Get API key from environment or config file.

        Priority:
            1. Environment variable MINICLAUDE_API_KEY
            2. Settings (config file)

        Returns:
            API key if found, None otherwise.
        """
        # Check environment variable first
        env_key = os.environ.get("MINICLAUDE_API_KEY")
        if env_key:
            return env_key

        # Check settings
        if settings.api_key:
            return settings.api_key

        return None

    @classmethod
    def get_api_key_source(cls) -> str:
        """
        Get the source of the current API key.

        Returns:
            String describing where the API key is coming from.
        """
        if os.environ.get("MINICLAUDE_API_KEY"):
            return "environment variable"
        if settings.api_key:
            return "config file"
        return "not configured"

    @classmethod
    def mask_api_key(cls, api_key: Optional[str]) -> str:
        """
        Mask an API key for safe display.

        Args:
            api_key: The API key to mask.

        Returns:
            Masked version of the API key.
        """
        if not api_key:
            return "(not set)"

        key_length = len(api_key)

        # Handle known formats
        if api_key.startswith("sk-ant-"):
            # Anthropic format: sk-ant-...xxxx
            if key_length > 12:
                return f"sk-ant-...{api_key[-4:]}"
            return "sk-ant-..."

        if api_key.startswith("sk-"):
            # OpenAI format: sk-...xxxx
            if key_length > 8:
                return f"sk-...{api_key[-4:]}"
            return "sk-..."

        # Generic format: ...xxxx or ****xxxx
        if key_length > 8:
            return f"****{api_key[-4:]}"
        elif key_length > 4:
            return f"****{api_key[-2:]}"
        return "****"

    @classmethod
    async def validate_api_key(
        cls,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        force_refresh: bool = False,
    ) -> bool:
        """
        Validate an API key by making a lightweight request.

        Args:
            api_key: API key to validate. If None, uses get_api_key().
            api_base_url: API base URL. If None, uses settings.api_base_url.
            force_refresh: Force revalidation even if cached.

        Returns:
            True if the API key is valid, False otherwise.
        """
        key_to_validate = api_key or cls.get_api_key()
        if not key_to_validate:
            return False

        # Check cache first
        if not force_refresh and cls._validation_cache:
            is_valid, timestamp = cls._validation_cache
            if datetime.now() - timestamp < cls._validation_cache_duration:
                return is_valid

        try:
            # Make a lightweight validation request (max_tokens=1)
            async with OpenAIClient(
                api_key=key_to_validate,
                api_base_url=api_base_url,
            ) as client:
                await client.create_chat_completion(
                    model=settings.model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=1,
                )

            # Cache successful validation
            cls._validation_cache = (True, datetime.now())
            return True

        except Exception:
            # Cache failed validation for shorter duration
            cls._validation_cache = (False, datetime.now())
            return False

    @classmethod
    def clear_validation_cache(cls) -> None:
        """Clear the validation cache."""
        cls._validation_cache = None

    @classmethod
    def save_api_key(cls, api_key: str) -> Path:
        """
        Save API key to config file.

        Args:
            api_key: API key to save.

        Returns:
            Path to the config file.
        """
        from pathlib import Path

        # Ensure config directory exists
        config_dir = Path(settings.config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.env"

        # Read existing config
        lines = []
        if config_file.exists():
            lines = config_file.read_text(encoding="utf-8").splitlines()

        # Find and replace or append
        key_upper = "MINICLAUDE_API_KEY"
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key_upper}=") or line.startswith(f"#{key_upper}="):
                lines[i] = f"{key_upper}={api_key}"
                found = True
                break

        if not found:
            lines.append(f"{key_upper}={api_key}")

        # Write back
        config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Set file permissions on Unix
        if sys.platform != "win32":
            try:
                os.chmod(config_file, 0o600)
                os.chmod(config_dir, 0o700)
            except OSError:
                pass  # Ignore if we can't set permissions

        # Clear cache
        cls.clear_validation_cache()

        return config_file

    @classmethod
    def delete_api_key(cls) -> bool:
        """
        Delete API key from config file.

        Returns:
            True if a key was deleted, False otherwise.
        """
        from pathlib import Path

        config_dir = Path(settings.config_dir)
        config_file = config_dir / "config.env"

        if not config_file.exists():
            return False

        # Read existing config
        lines = config_file.read_text(encoding="utf-8").splitlines()

        # Remove the key
        key_upper = "MINICLAUDE_API_KEY"
        new_lines = []
        removed = False
        for line in lines:
            if line.startswith(f"{key_upper}=") or line.startswith(f"#{key_upper}="):
                removed = True
            else:
                new_lines.append(line)

        if removed:
            config_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            cls.clear_validation_cache()

        return removed


# Convenience functions
def get_api_key() -> Optional[str]:
    """Get API key (convenience wrapper)."""
    return APIKeyManager.get_api_key()


def mask_api_key(api_key: Optional[str]) -> str:
    """Mask API key (convenience wrapper)."""
    return APIKeyManager.mask_api_key(api_key)


async def validate_api_key(
    api_key: Optional[str] = None,
    api_base_url: Optional[str] = None,
    force_refresh: bool = False,
) -> bool:
    """Validate API key (convenience wrapper)."""
    return await APIKeyManager.validate_api_key(api_key, api_base_url, force_refresh)
