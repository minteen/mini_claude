"""Execution loop for managing conversation with tool calls."""

import asyncio
from typing import List, Optional

from mini_claude.config.settings import settings
from mini_claude.services.api_client import OpenAIClient, OpenAIAPIError
from mini_claude.services.conversation import Conversation
from mini_claude.services.models import ToolDefinition
from mini_claude.services.tool_executor import ToolExecutor
from mini_claude.services.tool_schema_generator import generate_all_tool_schemas


class ExecutionLoopError(Exception):
    """Exception raised when execution loop fails."""

    pass


class ExecutionLoop:
    """Manage the conversation loop with tool calls."""

    def __init__(
        self,
        max_tool_calls: int = 10,
        max_tokens: int = 128000,
        keep_system_messages: bool = True,
    ):
        """
        Initialize execution loop.

        Args:
            max_tool_calls: Maximum number of tool calls in a single conversation.
            max_tokens: Maximum tokens to keep in conversation history.
            keep_system_messages: Whether to keep system messages when truncating.
        """
        self.max_tool_calls = max_tool_calls
        self.max_tokens = max_tokens
        self.keep_system_messages = keep_system_messages

    async def _send_to_llm(
        self,
        conversation: Conversation,
        client: OpenAIClient,
        tools: Optional[List[ToolDefinition]] = None,
        stream: bool = False,
    ):
        """
        Send conversation to LLM.

        Args:
            conversation: Conversation to send.
            client: OpenAI client.
            tools: List of tools to make available.
            stream: Whether to stream the response.

        Returns:
            LLM response.
        """
        # Truncate conversation if needed
        if conversation.estimate_tokens() > self.max_tokens:
            conversation.truncate(self.max_tokens, self.keep_system_messages)

        messages = conversation.get_messages_for_api()

        try:
            if stream:
                # For streaming, we need to handle it differently
                # This is a simplified version
                response = await client.create_chat_completion(
                    model=conversation.model or settings.model,
                    messages=messages,
                    tools=tools,
                    max_tokens=1024,
                    stream=False,  # Simplified for now
                )
            else:
                response = await client.create_chat_completion(
                    model=conversation.model or settings.model,
                    messages=messages,
                    tools=tools,
                    max_tokens=1024,
                )
            return response

        except OpenAIAPIError as e:
            raise ExecutionLoopError(f"LLM API error: {e}")

    async def run_conversation(
        self,
        conversation: Conversation,
        client: Optional[OpenAIClient] = None,
        tools: Optional[List[ToolDefinition]] = None,
        stream: bool = False,
    ) -> Conversation:
        """
        Run a complete conversation loop until LLM stops calling tools.

        Args:
            conversation: Conversation to run.
            client: OpenAI client. If None, creates a new one.
            tools: List of tools to make available. If None, uses all discovered tools.
            stream: Whether to stream responses.

        Returns:
            Final conversation with all messages.
        """
        if tools is None:
            tools = generate_all_tool_schemas()

        executor = ToolExecutor()
        tool_call_count = 0

        # Use provided client or create a new one
        should_close_client = False
        if client is None:
            client = OpenAIClient()
            should_close_client = True

        try:
            async with client if should_close_client else client:
                while tool_call_count < self.max_tool_calls:
                    # Send conversation to LLM
                    response = await self._send_to_llm(
                        conversation=conversation,
                        client=client,
                        tools=tools,
                        stream=stream,
                    )

                    # Extract message from response
                    if not response.choices:
                        raise ExecutionLoopError("No choices in LLM response")

                    message = response.choices[0].message

                    # Add assistant message to conversation
                    if isinstance(message.content, str):
                        conversation.add_assistant_message(message.content)
                    else:
                        # Handle content as list of content blocks (shouldn't happen with current API)
                        conversation.add_assistant_message(str(message.content))

                    # Check if LLM wants to call tools
                    if not message.tool_calls:
                        # No more tool calls, conversation is complete
                        break

                    # Execute tool calls
                    await executor.add_tool_results_to_conversation(
                        tool_calls=message.tool_calls,
                        conversation=conversation,
                    )

                    tool_call_count += len(message.tool_calls)

                    # Continue loop to send tool results back to LLM

                else:
                    # Max tool calls reached
                    conversation.add_assistant_message(
                        f"[System] Maximum tool calls ({self.max_tool_calls}) reached. Please continue the conversation."
                    )

        finally:
            if should_close_client and hasattr(client, 'close'):
                await client.close()

        return conversation

    async def run_single_turn(
        self,
        conversation: Conversation,
        client: Optional[OpenAIClient] = None,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> Conversation:
        """
        Run a single turn of conversation (send to LLM, execute tools, return).

        Args:
            conversation: Conversation to run.
            client: OpenAI client. If None, creates a new one.
            tools: List of tools to make available. If None, uses all discovered tools.

        Returns:
            Conversation with assistant response and tool results.
        """
        if tools is None:
            tools = generate_all_tool_schemas()

        executor = ToolExecutor()

        # Use provided client or create a new one
        should_close_client = False
        if client is None:
            client = OpenAIClient()
            should_close_client = True

        try:
            async with client if should_close_client else client:
                # Send conversation to LLM
                response = await self._send_to_llm(
                    conversation=conversation,
                    client=client,
                    tools=tools,
                    stream=False,
                )

                # Extract message from response
                if not response.choices:
                    raise ExecutionLoopError("No choices in LLM response")

                message = response.choices[0].message

                # Add assistant message to conversation
                if isinstance(message.content, str):
                    conversation.add_assistant_message(message.content)
                else:
                    conversation.add_assistant_message(str(message.content))

                # Execute tool calls if any
                if message.tool_calls:
                    await executor.add_tool_results_to_conversation(
                        tool_calls=message.tool_calls,
                        conversation=conversation,
                    )

        finally:
            if should_close_client and hasattr(client, 'close'):
                await client.close()

        return conversation


# Global execution loop instance
_loop: Optional[ExecutionLoop] = None


def get_execution_loop() -> ExecutionLoop:
    """Get the global execution loop instance."""
    global _loop
    if _loop is None:
        _loop = ExecutionLoop()
    return _loop
