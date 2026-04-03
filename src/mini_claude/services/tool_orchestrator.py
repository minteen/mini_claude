"""Main orchestrator for tool execution in MiniClaude."""

from typing import List, Optional

from mini_claude.services.conversation import Conversation
from mini_claude.services.execution_loop import ExecutionLoop, get_execution_loop
from mini_claude.services.models import ToolDefinition
from mini_claude.services.tool_executor import ToolExecutor, get_tool_executor
from mini_claude.services.tool_schema_generator import (
    ToolDefinition as SchemaToolDefinition,
    generate_all_tool_schemas,
    get_tool_class_by_name,
)


class ToolOrchestrator:
    """Main orchestrator for tool execution."""

    def __init__(self):
        self.execution_loop = get_execution_loop()
        self.tool_executor = get_tool_executor()

    def get_available_tools(self) -> List[SchemaToolDefinition]:
        """
        Get all available tools.

        Returns:
            List of tool definitions.
        """
        return generate_all_tool_schemas()

    def get_tool_by_name(self, name: str) -> Optional[SchemaToolDefinition]:
        """
        Get a specific tool by name.

        Args:
            name: Name of the tool.

        Returns:
            Tool definition if found, None otherwise.
        """
        tools = self.get_available_tools()
        for tool in tools:
            if tool.function.name == name:
                return tool
        return None

    async def run_conversation_with_tools(
        self,
        conversation: Conversation,
        tools: Optional[List[SchemaToolDefinition]] = None,
        max_tool_calls: int = 10,
        max_tokens: int = 128000,
    ) -> Conversation:
        """
        Run a conversation with automatic tool execution.

        Args:
            conversation: Conversation to run.
            tools: List of tools to make available. If None, uses all tools.
            max_tool_calls: Maximum number of tool calls in the conversation.
            max_tokens: Maximum tokens to keep in conversation.

        Returns:
            Final conversation with all messages.
        """
        # Configure execution loop
        self.execution_loop.max_tool_calls = max_tool_calls
        self.execution_loop.max_tokens = max_tokens

        # Run the conversation loop
        return await self.execution_loop.run_conversation(
            conversation=conversation,
            tools=tools,
        )

    async def execute_tool_calls(
        self,
        tool_calls,
        conversation: Conversation,
    ):
        """
        Execute tool calls and add results to conversation.

        Args:
            tool_calls: List of tool calls to execute.
            conversation: Conversation to add results to.
        """
        await self.tool_executor.add_tool_results_to_conversation(
            tool_calls=tool_calls,
            conversation=conversation,
        )


# Global orchestrator instance
_orchestrator: Optional[ToolOrchestrator] = None


def get_tool_orchestrator() -> ToolOrchestrator:
    """Get the global tool orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ToolOrchestrator()
    return _orchestrator
