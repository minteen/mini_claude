"""Conversation management for multi-turn dialogues."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from mini_claude.config.settings import settings


# ============== Content Blocks ==============


class TextContent(BaseModel):
    """Text content block."""

    type: Literal["text"] = "text"
    text: str


class ToolCallContent(BaseModel):
    """Tool call content block (request from assistant)."""

    type: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResultContent(BaseModel):
    """Tool result content block (response to assistant)."""

    type: Literal["tool_result"] = "tool_result"
    tool_call_id: str
    content: str
    is_error: bool = False


ContentBlock = TextContent | ToolCallContent | ToolResultContent


# ============== Messages ==============


class Message(BaseModel):
    """A single message in the conversation."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str | List[ContentBlock]
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============== Conversation ==============


class Conversation(BaseModel):
    """A conversation with message history."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: List[Message] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model: Optional[str] = None

    def add_message(
        self,
        role: Literal["user", "assistant", "system", "tool"],
        content: str | List[ContentBlock],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        Add a message to the conversation.

        Args:
            role: Message role.
            content: Message content (string or list of content blocks).
            metadata: Optional metadata for the message.

        Returns:
            The created Message object.
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message

    def add_user_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Add a user message."""
        return self.add_message("user", content, metadata)

    def add_assistant_message(
        self,
        content: str | List[ContentBlock],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Add an assistant message."""
        return self.add_message("assistant", content, metadata)

    def add_system_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Add a system message."""
        return self.add_message("system", content, metadata)

    def add_tool_result(
        self,
        tool_call_id: str,
        content: str,
        is_error: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Add a tool result message."""
        tool_result = ToolResultContent(
            tool_call_id=tool_call_id,
            content=content,
            is_error=is_error,
        )
        return self.add_message("tool", [tool_result], metadata)

    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """
        Convert conversation to OpenAI-compatible message format for API.

        Returns:
            List of messages in OpenAI format.
        """
        api_messages: List[Dict[str, Any]] = []

        for msg in self.messages:
            if msg.role == "system":
                # System message in OpenAI format
                api_messages.append({
                    "role": "system",
                    "content": msg.content if isinstance(msg.content, str) else "",
                })
            elif msg.role == "user":
                # User message
                if isinstance(msg.content, str):
                    api_messages.append({
                        "role": "user",
                        "content": msg.content,
                    })
                else:
                    # Handle multi-part content
                    parts = []
                    for block in msg.content:
                        if isinstance(block, TextContent):
                            parts.append({"type": "text", "text": block.text})
                    if parts:
                        api_messages.append({
                            "role": "user",
                            "content": parts,
                        })
            elif msg.role == "assistant":
                # Assistant message
                if isinstance(msg.content, str):
                    api_messages.append({
                        "role": "assistant",
                        "content": msg.content,
                    })
                else:
                    # Handle multi-part content with tool calls
                    content_str = ""
                    tool_calls = []
                    for block in msg.content:
                        if isinstance(block, TextContent):
                            content_str += block.text
                        elif isinstance(block, ToolCallContent):
                            tool_calls.append({
                                "id": block.id,
                                "type": "function",
                                "function": {
                                    "name": block.name,
                                    "arguments": json.dumps(block.arguments, ensure_ascii=False),
                                },
                            })
                    msg_dict: Dict[str, Any] = {"role": "assistant"}
                    if content_str:
                        msg_dict["content"] = content_str
                    if tool_calls:
                        msg_dict["tool_calls"] = tool_calls
                    api_messages.append(msg_dict)
            elif msg.role == "tool":
                # Tool result message
                if isinstance(msg.content, list) and len(msg.content) > 0:
                    block = msg.content[0]
                    if isinstance(block, ToolResultContent):
                        api_messages.append({
                            "role": "tool",
                            "tool_call_id": block.tool_call_id,
                            "content": block.content,
                        })

        return api_messages

    def clear(self) -> None:
        """Clear all messages except system prompt."""
        if self.system_prompt:
            self.messages = [
                Message(role="system", content=self.system_prompt)
            ]
        else:
            self.messages = []
        self.updated_at = datetime.now()

    def estimate_tokens(self) -> int:
        """
        Estimate the number of tokens in the conversation.

        This is a rough estimate. For accurate counting, use tiktoken.

        Returns:
            Estimated token count.
        """
        total = 0
        for msg in self.messages:
            if isinstance(msg.content, str):
                # Rough estimate: ~1.3 tokens per English word, ~2 tokens per Chinese character
                text = msg.content
                # Count Chinese characters
                chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
                # Count other characters as words (split by whitespace)
                other_words = len([w for w in text.split() if not any("\u4e00" <= c <= "\u9fff" for c in w)])
                total += chinese_chars * 2 + other_words * 1.3
            else:
                # Estimate from content blocks
                for block in msg.content:
                    if isinstance(block, TextContent):
                        text = block.text
                        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
                        other_words = len([w for w in text.split() if not any("\u4e00" <= c <= "\u9fff" for c in w)])
                        total += chinese_chars * 2 + other_words * 1.3
                    elif isinstance(block, ToolCallContent):
                        # Add tokens for tool call
                        total += 10  # Base overhead
                        total += len(block.name) * 0.5
                        total += len(json.dumps(block.arguments)) * 0.5

        return int(total)

    def truncate(self, max_tokens: int = 128000, keep_system: bool = True) -> None:
        """
        Truncate conversation to fit within token limit.

        Args:
            max_tokens: Maximum token count to keep.
            keep_system: Whether to always keep system messages at the beginning.
        """
        if self.estimate_tokens() <= max_tokens:
            return

        # Separate system messages and others
        system_messages: List[Message] = []
        other_messages: List[Message] = []

        for msg in self.messages:
            if msg.role == "system" and keep_system:
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # Start with system messages
        truncated = system_messages.copy()

        # Add messages from newest to oldest until we hit the limit
        for msg in reversed(other_messages):
            truncated.append(msg)
            # Create temp conversation to estimate tokens
            temp_conv = Conversation(
                messages=truncated,
                system_prompt=self.system_prompt,
            )
            if temp_conv.estimate_tokens() > max_tokens:
                truncated.pop()
                break

        # Restore original order (system first, then others in chronological order)
        final_messages = system_messages.copy()
        # Add other messages in order, excluding those after the cutoff
        cutoff_index = len(other_messages) - (len(truncated) - len(system_messages))
        final_messages.extend(other_messages[cutoff_index:])

        self.messages = final_messages
        self.updated_at = datetime.now()


# ============== Conversation Manager ==============


class ConversationManager:
    """Manager for saving and loading conversations."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize conversation manager.

        Args:
            storage_dir: Directory to store conversations. Defaults to settings.data_dir / "conversations".
        """
        if storage_dir is None:
            storage_dir = Path(settings.data_dir) / "conversations"
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, conversation: Conversation) -> Path:
        """
        Save a conversation to disk.

        Args:
            conversation: Conversation to save.

        Returns:
            Path to the saved file.
        """
        file_path = self.storage_dir / f"{conversation.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(conversation.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        return file_path

    def load(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from disk.

        Args:
            conversation_id: ID of conversation to load.

        Returns:
            Conversation if found, None otherwise.
        """
        file_path = self.storage_dir / f"{conversation_id}.json"
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Parse datetime strings
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        for msg in data.get("messages", []):
            if "timestamp" in msg and isinstance(msg["timestamp"], str):
                msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
        return Conversation(**data)

    def list(self) -> List[Dict[str, Any]]:
        """
        List all saved conversations.

        Returns:
            List of conversation metadata (id, created_at, updated_at, first message snippet).
        """
        conversations: List[Dict[str, Any]] = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Get first user message as snippet
                snippet = ""
                for msg in data.get("messages", []):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            snippet = content[:50] + ("..." if len(content) > 50 else "")
                            break
                conversations.append({
                    "id": data.get("id", file_path.stem),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "snippet": snippet,
                })
            except (json.JSONDecodeError, KeyError):
                continue
        # Sort by updated_at, newest first
        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return conversations

    def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: ID of conversation to delete.

        Returns:
            True if deleted, False if not found.
        """
        file_path = self.storage_dir / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# Global manager instance
_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    global _manager
    if _manager is None:
        _manager = ConversationManager()
    return _manager
