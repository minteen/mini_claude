"""Service layer for MiniClaude (OpenAI-compatible)."""

from mini_claude.services.api_client import (
    OpenAIClient,
    OpenAIAPIError,
    OpenAIAuthError,
    OpenAIRateLimitError,
    OpenAIServerError,
    get_client,
)
from mini_claude.services.auth import (
    APIKeyManager,
    get_api_key,
    mask_api_key,
    validate_api_key,
)
from mini_claude.services.conversation import (
    Conversation,
    ConversationManager,
    ContentBlock,
    Message,
    TextContent,
    ToolCallContent,
    ToolResultContent,
    get_conversation_manager,
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
    Message as APIMessage,
    OpenAIChatCompletionChunk,
    OpenAIChatCompletionRequest,
    OpenAIChatCompletionResponse,
    SystemMessage,
    TextContent as APITextContent,
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
    # Auth
    "APIKeyManager",
    "get_api_key",
    "mask_api_key",
    "validate_api_key",
    # Conversation
    "Conversation",
    "ConversationManager",
    "ContentBlock",
    "Message",
    "TextContent",
    "ToolCallContent",
    "ToolResultContent",
    "get_conversation_manager",
    # Models - Messages
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ToolMessage",
    "APIMessage",
    # Models - Content
    "APITextContent",
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
