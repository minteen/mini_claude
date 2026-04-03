"""Command base class for CLI commands."""

from abc import ABC, abstractmethod
from typing import Any, Optional

import typer


class Command(ABC):
    """Abstract base class for CLI commands."""

    name: str
    help: str

    @abstractmethod
    def register(self, app: typer.Typer) -> None:
        """
        Register this command with the Typer app.

        Args:
            app: The Typer application to register with
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
