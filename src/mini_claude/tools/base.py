"""Tool base class and result model."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class ToolResult(BaseModel):
    """Result of a tool execution."""

    success: bool = Field(..., description="Whether the tool execution succeeded")
    content: Optional[str] = Field(None, description="Output content if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional structured data")

    @classmethod
    def ok(cls, content: str, data: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, content=content, data=data)

    @classmethod
    def err(cls, error: str, data: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, error=error, data=data)


class Tool(ABC):
    """Abstract base class for tools."""

    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with the given arguments.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult containing the execution result
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
