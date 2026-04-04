"""
Tool base class and result model.

This module defines the abstract base class for all tools in MiniClaude,
along with the ToolResult model for returning execution results.

All tools should inherit from the Tool base class and implement the
`execute` method. Tools can be automatically discovered by the framework
and made available to the AI assistant for execution.

Example:
    ```python
    from mini_claude.tools.base import Tool, ToolResult

    class MyTool(Tool):
        name = "my_tool"
        description = "Does something useful"

        async def execute(self, param: str, **kwargs) -> ToolResult:
            try:
                result = do_something(param)
                return ToolResult.ok(content=f"Result: {result}")
            except Exception as e:
                return ToolResult.err(error=str(e))
    ```
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class ToolResult(BaseModel):
    """
    Result of a tool execution.

    This model encapsulates the result of executing a tool, including
    whether the execution succeeded, the output content or error message,
    and optional structured data.

    Use the factory methods `ok()` and `err()` for convenient creation
    of success and error results respectively.

    Example:
        ```python
        # Success result
        result = ToolResult.ok("Operation completed", data={"count": 5})

        # Error result
        result = ToolResult.err("File not found", data={"path": "/missing.txt"})
        ```
    """

    success: bool = Field(..., description="Whether the tool execution succeeded")
    content: Optional[str] = Field(None, description="Output content if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional structured data")

    @classmethod
    def ok(cls, content: str, data: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """
        Create a successful tool execution result.

        Args:
            content: The output content from the successful execution.
            data: Optional structured data to include with the result.

        Returns:
            ToolResult instance with success=True and the provided content.
        """
        return cls(success=True, content=content, data=data)

    @classmethod
    def err(cls, error: str, data: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """
        Create a failed tool execution result.

        Args:
            error: The error message describing what went wrong.
            data: Optional structured data to include with the result.

        Returns:
            ToolResult instance with success=False and the provided error message.
        """
        return cls(success=False, error=error, data=data)


class Tool(ABC):
    """
    Abstract base class for tools.

    All tools in MiniClaude must inherit from this class and implement
    the `execute` method. The class should also define `name` and
    `description` class attributes that are used by the framework to
    discover and document the tool.

    The `execute` method should be async and accept keyword arguments
    corresponding to the parameters the tool needs. It should return
    a ToolResult indicating success or failure.

    Attributes:
        name: The unique name of the tool (used for identification).
        description: A human-readable description of what the tool does.

    Example:
        ```python
        class ReadTool(Tool):
            name = "Read"
            description = "Read contents from a file"

            async def execute(self, file_path: str, offset: Optional[int] = None, **kwargs) -> ToolResult:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    return ToolResult.ok(content=content)
                except Exception as e:
                    return ToolResult.err(error=str(e))
        ```
    """

    name: str
    """The unique name of the tool, used for identification and invocation."""

    description: str
    """A human-readable description of what the tool does."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with the given arguments.

        This method must be implemented by subclasses to perform the
        actual tool logic. It should be async and accept keyword arguments
        corresponding to the tool's parameters.

        Args:
            **kwargs: Tool-specific keyword arguments. The parameters should
                be explicitly defined in the method signature for proper
                schema generation.

        Returns:
            ToolResult containing the execution result. Use ToolResult.ok()
            for successful executions and ToolResult.err() for failures.

        Note:
            Always include **kwargs in the signature to handle any additional
            parameters that may be passed, even if unused.
        """
        pass

    def __repr__(self) -> str:
        """
        Return a string representation of the tool for debugging.

        Returns:
            String showing the tool class and name.
        """
        return f"{self.__class__.__name__}(name={self.name!r})"
