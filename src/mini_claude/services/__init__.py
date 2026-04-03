"""Service layer for MiniClaude (OpenAI-compatible)."""

from mini_claude.services.api_client import (
    OpenAIClient,
    OpenAIAPIError,
    OpenAIAuthError,
    OpenAIRateLimitError,
    OpenAIServerError,
    get_client,
)
from mini_claude.services.models import (
    AssistantMessage,
    Choice,
    ChoiceDelta,
    ChoiceDeltaMessage,
    ChoiceMessage,
    CompletionUsage,
    ContentPart,
    FunctionDefinition,
    FunctionParameters,
    ImageUrlContent,
    Message,
    OpenAIChatCompletionChunk,
    OpenAIChatCompletionRequest,
    OpenAIChatCompletionResponse,
    SystemMessage,
    TextContent,
    ToolCall,
    ToolCallFunction,
    ToolChoice,
    ToolChoiceFunction,
    ToolDefinition,
    ToolMessage,
    UserMessage,
)

__all__ = [
    # API Client
    "OpenAIClient",
    "OpenAIAPIError",
    "OpenAIAuthError",
    "OpenAIRateLimitError",
    "OpenAIServerError",
    "get_client",
    # Models - Messages
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ToolMessage",
    "Message",
    # Models - Content
    "TextContent",
    "ImageUrlContent",
    "ContentPart",
    # Models - Tools
    "ToolCall",
    "ToolCallFunction",
    "FunctionDefinition",
    "FunctionParameters",
    "ToolDefinition",
    "ToolChoice",
    "ToolChoiceFunction",
    # Models - API
    "OpenAIChatCompletionRequest",
    "OpenAIChatCompletionResponse",
    "OpenAIChatCompletionChunk",
    "Choice",
    "ChoiceDelta",
    "ChoiceMessage",
    "ChoiceDeltaMessage",
    "CompletionUsage",
]
