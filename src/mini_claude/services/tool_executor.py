"""Execute tool calls from LLM responses."""

import asyncio
import json
import traceback
from typing import Any, Dict, List, Optional

from mini_claude.services.conversation import Conversation, ToolResultContent
from mini_claude.services.models import ToolCall
from mini_claude.services.tool_schema_generator import get_tool_class_by_name
from mini_claude.tools.base import ToolResult


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""

    pass


class ToolExecutor:
    """Execute tool calls from LLM responses."""

    def __init__(self, timeout: float = 30.0, max_output_length: int = 10000):
        """
        Initialize tool executor.

        Args:
            timeout: Maximum time to wait for tool execution (seconds).
            max_output_length: Maximum length of tool output (characters).
        """
        self.timeout = timeout
        self.max_output_length = max_output_length

    async def execute_single_tool_call(
        self,
        tool_call: ToolCall,
        conversation: Optional[Conversation] = None,
    ) -> ToolResultContent:
        """
        Execute a single tool call.

        Args:
            tool_call: Tool call to execute.
            conversation: Optional conversation for context.

        Returns:
            ToolResultContent with the result.
        """
        tool_name = tool_call.function.name
        tool_class = get_tool_class_by_name(tool_name)

        if not tool_class:
            error_msg = f"Tool not found: {tool_name}"
            return ToolResultContent(
                type="tool_result",
                tool_call_id=tool_call.id,
                content=error_msg,
                is_error=True,
            )

        try:
            # Parse arguments from JSON string
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON arguments: {e}"
                return ToolResultContent(
                    type="tool_result",
                    tool_call_id=tool_call.id,
                    content=error_msg,
                    is_error=True,
                )

            # Validate required parameters
            sig = tool_class.execute.__annotations__
            required_params = [
                name for name, param in tool_class.execute.__code__.co_varnames[:tool_class.execute.__code__.co_argcount]
                if name != "self" and param.default == inspect.Parameter.empty
            ]

            missing_params = [param for param in required_params if param not in args]
            if missing_params:
                error_msg = f"Missing required parameters: {', '.join(missing_params)}"
                return ToolResultContent(
                    type="tool_result",
                    tool_call_id=tool_call.id,
                    content=error_msg,
                    is_error=True,
                )

            # Instantiate tool and execute
            tool = tool_class()

            # Execute with timeout
            try:
                if asyncio.iscoroutinefunction(tool.execute):
                    result: ToolResult = await asyncio.wait_for(
                        tool.execute(**args),
                        timeout=self.timeout,
                    )
                else:
                    # For sync methods, run in thread pool
                    loop = asyncio.get_event_loop()
                    result: ToolResult = await loop.run_in_executor(
                        None,
                        lambda: asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, tool.execute, **args),
                            timeout=self.timeout,
                        )
                    )
            except asyncio.TimeoutError:
                error_msg = f"Tool execution timed out after {self.timeout} seconds"
                return ToolResultContent(
                    type="tool_result",
                    tool_call_id=tool_call.id,
                    content=error_msg,
                    is_error=True,
                )

            # Process result
            if result.success:
                # Truncate output if too long
                content = str(result.content) if result.content is not None else ""
                if len(content) > self.max_output_length:
                    content = content[:self.max_output_length] + f"\n... (truncated, {len(content) - self.max_output_length} more characters)"

                return ToolResultContent(
                    type="tool_result",
                    tool_call_id=tool_call.id,
                    content=content,
                    is_error=False,
                )
            else:
                return ToolResultContent(
                    type="tool_result",
                    tool_call_id=tool_call.id,
                    content=str(result.error),
                    is_error=True,
                )

        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}\n{traceback.format_exc()}"
            return ToolResultContent(
                type="tool_result",
                tool_call_id=tool_call.id,
                content=error_msg,
                is_error=True,
            )

    async def execute_tool_calls(
        self,
        tool_calls: List[ToolCall],
        conversation: Optional[Conversation] = None,
    ) -> List[ToolResultContent]:
        """
        Execute multiple tool calls in parallel.

        Args:
            tool_calls: List of tool calls to execute.
            conversation: Optional conversation for context.

        Returns:
            List of ToolResultContent objects.
        """
        if not tool_calls:
            return []

        # Execute all tool calls in parallel
        tasks = [
            self.execute_single_tool_call(tool_call, conversation)
            for tool_call in tool_calls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    ToolResultContent(
                        type="tool_result",
                        tool_call_id=tool_calls[i].id,
                        content=f"Execution failed: {result}",
                        is_error=True,
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def add_tool_results_to_conversation(
        self,
        tool_calls: List[ToolCall],
        conversation: Conversation,
    ) -> None:
        """
        Execute tool calls and add results to conversation.

        Args:
            tool_calls: List of tool calls to execute.
            conversation: Conversation to add results to.
        """
        # Execute tool calls
        results = await self.execute_tool_calls(tool_calls, conversation)

        # Add results to conversation
        for result in results:
            conversation.add_tool_result(
                tool_call_id=result.tool_call_id,
                content=result.content,
                is_error=result.is_error,
            )


# Global executor instance
_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """Get the global tool executor instance."""
    global _executor
    if _executor is None:
        _executor = ToolExecutor()
    return _executor
