"""Data models for OpenAI-compatible API."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============== Content Blocks ==============


class TextContent(BaseModel):
    """Text content part."""

    type: Literal["text"] = "text"
    text: str


class ImageUrlContent(BaseModel):
    """Image URL content part."""

    type: Literal["image_url"] = "image_url"
    image_url: Dict[str, str]


ContentPart = TextContent | ImageUrlContent


class ToolCallFunction(BaseModel):
    """Function call in tool call."""

    name: str
    arguments: str


class ToolCall(BaseModel):
    """Tool call in assistant message."""

    id: str
    type: Literal["function"] = "function"
    function: ToolCallFunction


# ============== Messages ==============


class UserMessage(BaseModel):
    """User message in the conversation."""

    role: Literal["user"] = "user"
    content: str | List[ContentPart]
    name: Optional[str] = None


class AssistantMessage(BaseModel):
    """Assistant message in the conversation."""

    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    name: Optional[str] = None


class SystemMessage(BaseModel):
    """System message in the conversation."""

    role: Literal["system"] = "system"
    content: str
    name: Optional[str] = None


class ToolMessage(BaseModel):
    """Tool result message."""

    role: Literal["tool"] = "tool"
    content: str
    tool_call_id: str


Message = UserMessage | AssistantMessage | SystemMessage | ToolMessage


# ============== Tool Definitions ==============


class FunctionParameters(BaseModel):
    """JSON Schema for function parameters."""

    type: Literal["object"] = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class FunctionDefinition(BaseModel):
    """Function definition."""

    name: str
    description: str
    parameters: FunctionParameters


class ToolDefinition(BaseModel):
    """Tool definition that can be called by the model."""

    type: Literal["function"] = "function"
    function: FunctionDefinition


class ToolChoiceFunction(BaseModel):
    """Function specification for tool choice."""

    name: str


class ToolChoice(BaseModel):
    """Tool choice configuration."""

    type: Literal["none", "auto", "required", "function"]
    function: Optional[ToolChoiceFunction] = None


# ============== API Request ==============


class OpenAIChatCompletionRequest(BaseModel):
    """Request to OpenAI Chat Completions API."""

    model: str
    messages: List[Dict[str, Any]]
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[ToolChoice | str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop: Optional[str | List[str]] = None
    stream: bool = False
    stream_options: Optional[Dict[str, Any]] = None
    n: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


# ============== API Response ==============


class CompletionUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    # Optional for OpenRouter/other providers
    prompt_tokens_details: Optional[Dict[str, int]] = None
    completion_tokens_details: Optional[Dict[str, int]] = None


class ChoiceMessage(BaseModel):
    """Message in a choice."""

    role: Literal["assistant"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class Choice(BaseModel):
    """A single completion choice."""

    index: int
    message: ChoiceMessage
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None


class OpenAIChatCompletionResponse(BaseModel):
    """Response from OpenAI Chat Completions API."""

    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: CompletionUsage
    system_fingerprint: Optional[str] = None


# ============== Streaming Events ==============


class ChoiceDeltaMessage(BaseModel):
    """Delta message in streaming."""

    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class ChoiceDelta(BaseModel):
    """A single completion choice delta."""

    index: int
    delta: ChoiceDeltaMessage
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None


class OpenAIChatCompletionChunk(BaseModel):
    """Streaming chunk from OpenAI API."""

    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChoiceDelta]
    usage: Optional[CompletionUsage] = None
    system_fingerprint: Optional[str] = None
