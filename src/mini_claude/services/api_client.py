"""API client for OpenAI-compatible API."""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from mini_claude.config.settings import settings
from mini_claude.services.models import (
    OpenAIChatCompletionRequest,
    OpenAIChatCompletionResponse,
    OpenAIChatCompletionChunk,
    ToolDefinition,
)


class OpenAIAPIError(Exception):
    """Base exception for OpenAI API errors."""

    pass


class OpenAIAuthError(OpenAIAPIError):
    """Authentication error (invalid API key)."""

    pass


class OpenAIRateLimitError(OpenAIAPIError):
    """Rate limit exceeded."""

    pass


class OpenAIServerError(OpenAIAPIError):
    """Server-side error."""

    pass


class OpenAIClient:
    """Async client for OpenAI-compatible API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """
        Initialize the OpenAI-compatible API client.

        Args:
            api_key: API key. If None, uses settings.api_key.
            api_base_url: API base URL. If None, uses settings.api_base_url.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for retryable errors.
        """
        self.api_key = api_key or settings.api_key
        self.api_base_url = api_base_url or settings.api_base_url
        self.timeout = timeout
        self.max_retries = max_retries

        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "OpenAIClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Create the HTTP client connection."""
        if not self.api_key:
            raise OpenAIAuthError("No API key provided")

        # Normalize base URL (remove trailing slash)
        base_url = self.api_base_url.rstrip("/")

        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout=self.timeout, connect=5.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_connected(self) -> None:
        """Ensure the client is connected."""
        if not self._client:
            raise RuntimeError("Client not connected. Call 'connect()' first or use async context manager.")

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make a request with automatic retries for retryable errors.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            **kwargs: Additional arguments for httpx request.

        Returns:
            httpx.Response: The response object.

        Raises:
            OpenAIAuthError: If authentication fails.
            OpenAIRateLimitError: If rate limit is exceeded.
            OpenAIServerError: If server returns 5xx error.
            OpenAIAPIError: For other API errors.
        """
        self._ensure_connected()

        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=endpoint,
                    **kwargs,
                )

                if response.status_code == 200:
                    return response

                # Handle error responses
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    pass

                # Extract error message
                error_msg = f"HTTP {response.status_code}"
                if "error" in error_data:
                    err = error_data["error"]
                    if isinstance(err, dict):
                        error_msg = err.get("message", error_msg)
                    else:
                        error_msg = str(err)

                if response.status_code == 401:
                    raise OpenAIAuthError(error_msg)
                elif response.status_code == 429:
                    if attempt < self.max_retries:
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                        last_exception = OpenAIRateLimitError(error_msg)
                        continue
                    raise OpenAIRateLimitError(error_msg)
                elif 500 <= response.status_code < 600:
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                        last_exception = OpenAIServerError(error_msg)
                        continue
                    raise OpenAIServerError(error_msg)
                else:
                    raise OpenAIAPIError(error_msg)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    last_exception = e
                    continue
                raise OpenAIAPIError(f"Network error: {e}") from e

        if last_exception:
            raise last_exception
        raise OpenAIAPIError("Request failed after retries")

    async def create_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: Optional[ToolDefinition | str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[str | List[str]] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> OpenAIChatCompletionResponse:
        """
        Create a chat completion using the OpenAI-compatible API.

        Args:
            model: Model to use (e.g., "gpt-4", "claude-3-opus").
            messages: List of messages in the conversation.
            max_tokens: Maximum tokens to generate (legacy).
            max_completion_tokens: Maximum tokens to generate (preferred).
            tools: List of tools available to the model.
            tool_choice: Tool choice configuration.
            temperature: Sampling temperature.
            top_p: Top-p sampling.
            stop: Stop sequences.
            stream: Whether to stream the response.
            **kwargs: Additional API parameters.

        Returns:
            OpenAIChatCompletionResponse: The API response.
        """
        request = OpenAIChatCompletionRequest(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
            tools=tools,
            tool_choice=tool_choice,  # type: ignore
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            stream=stream,
            **kwargs,
        )

        response = await self._request_with_retry(
            method="POST",
            endpoint="/chat/completions",
            json=request.model_dump(exclude_none=True),
        )

        return OpenAIChatCompletionResponse(**response.json())

    async def create_chat_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: Optional[ToolDefinition | str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[str | List[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[OpenAIChatCompletionChunk, None]:
        """
        Create a chat completion with streaming response.

        Args:
            model: Model to use.
            messages: List of messages in the conversation.
            max_tokens: Maximum tokens to generate (legacy).
            max_completion_tokens: Maximum tokens to generate (preferred).
            tools: List of tools available to the model.
            tool_choice: Tool choice configuration.
            temperature: Sampling temperature.
            top_p: Top-p sampling.
            stop: Stop sequences.
            **kwargs: Additional API parameters.

        Yields:
            OpenAIChatCompletionChunk: Streaming chunks from the API.
        """
        self._ensure_connected()

        request = OpenAIChatCompletionRequest(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
            tools=tools,
            tool_choice=tool_choice,  # type: ignore
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            stream=True,
            stream_options={"include_usage": True},
            **kwargs,
        )

        async with self._client.stream(
            method="POST",
            url="/chat/completions",
            json=request.model_dump(exclude_none=True),
        ) as response:
            if response.status_code != 200:
                # Read the error response
                error_text = await response.aread()
                error_data = {}
                try:
                    error_data = json.loads(error_text)
                except json.JSONDecodeError:
                    pass

                error_msg = f"HTTP {response.status_code}"
                if "error" in error_data:
                    err = error_data["error"]
                    if isinstance(err, dict):
                        error_msg = err.get("message", error_msg)
                    else:
                        error_msg = str(err)

                if response.status_code == 401:
                    raise OpenAIAuthError(error_msg)
                elif response.status_code == 429:
                    raise OpenAIRateLimitError(error_msg)
                else:
                    raise OpenAIAPIError(error_msg)

            # Parse SSE stream
            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                lines = buffer.split("\n")
                buffer = lines.pop()

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            return

                        try:
                            data = json.loads(data_str)
                            yield OpenAIChatCompletionChunk(**data)
                        except (json.JSONDecodeError, ValueError):
                            # Skip malformed events
                            pass

            # Process any remaining data in buffer
            if buffer.strip():
                line = buffer.strip()
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str != "[DONE]":
                        try:
                            data = json.loads(data_str)
                            yield OpenAIChatCompletionChunk(**data)
                        except (json.JSONDecodeError, ValueError):
                            pass


# Global client instance
_client: Optional[OpenAIClient] = None


def get_client() -> OpenAIClient:
    """Get the global OpenAI-compatible API client instance."""
    global _client
    if _client is None:
        _client = OpenAIClient()
    return _client
