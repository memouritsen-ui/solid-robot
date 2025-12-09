"""Abstract interface for LLM providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class ModelProvider(ABC):
    """Abstract interface for LLM providers.

    All LLM providers (local and cloud) must implement this interface
    to ensure consistent behavior across the routing system.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this provider."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate completion from messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: If True, return async iterator of tokens

        Returns:
            Complete response string, or async iterator of tokens if streaming
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if model is loaded and accessible.

        Returns:
            True if model can accept requests
        """
        ...

    @abstractmethod
    def get_context_window(self) -> int:
        """Return maximum context length in tokens.

        Returns:
            Maximum input + output tokens supported
        """
        ...

    @abstractmethod
    def is_local(self) -> bool:
        """Check if this is a local (privacy-safe) model.

        Returns:
            True if model runs locally and data never leaves device
        """
        ...
