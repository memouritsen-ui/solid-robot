"""LiteLLM Router implementation for model routing with fallback support."""

from collections.abc import AsyncIterator
from typing import Any

from litellm import Router  # type: ignore[attr-defined]

from research_tool.core.config import settings
from research_tool.core.exceptions import ModelUnavailableError
from research_tool.core.logging import get_logger

logger = get_logger(__name__)


# Model configuration - maps logical names to LiteLLM model specs
# Updated to match actually installed Ollama models
MODEL_CONFIG: list[dict[str, Any]] = [
    {
        "model_name": "local-fast",
        "litellm_params": {
            "model": "ollama/llama3.1:8b",  # Your installed model
            "api_base": settings.ollama_base_url,
        },
        "model_info": {
            "context_window": 128000,
            "is_local": True,
        },
    },
    {
        "model_name": "local-powerful",
        "litellm_params": {
            "model": "ollama/qwen2.5-coder:32b",  # Your installed model
            "api_base": settings.ollama_base_url,
        },
        "model_info": {
            "context_window": 128000,
            "is_local": True,
        },
    },
    {
        "model_name": "cloud-best",
        "litellm_params": {
            "model": "claude-3-5-sonnet-20241022",
            "api_key": settings.anthropic_api_key,
        },
        "model_info": {
            "context_window": 200000,
            "is_local": False,
        },
    },
]

# Fallback chains - if primary fails, try secondary
FALLBACK_CONFIG: list[dict[str, list[str]]] = [
    {"local-powerful": ["local-fast"]},
    {"cloud-best": ["local-powerful"]},
]


class LLMRouter:
    """LiteLLM-based model router with fallback support.

    Provides unified interface for routing requests to local (Ollama) or
    cloud (Claude) models with automatic fallback on failures.
    """

    def __init__(self) -> None:
        """Initialize the router with model configuration."""
        self._router: Any = Router(
            model_list=MODEL_CONFIG,
            fallbacks=FALLBACK_CONFIG,
            set_verbose=False,
        )
        self._model_info: dict[str, dict[str, Any]] = {
            cfg["model_name"]: cfg.get("model_info", {}) for cfg in MODEL_CONFIG
        }

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str = "local-fast",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate completion using specified model.

        Args:
            messages: Chat messages in OpenAI format
            model: Model name (local-fast, local-powerful, cloud-best)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response

        Returns:
            Generated text or async iterator of tokens if streaming

        Raises:
            ModelUnavailableError: If model fails and no fallback succeeds
        """
        try:
            if stream:
                return self._stream_completion(messages, model, temperature, max_tokens)

            response: Any = await self._router.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content: str = response.choices[0].message.content or ""
            usage = getattr(response, "usage", None)
            logger.info(
                "completion_success",
                model=model,
                input_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
                output_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            )
            return content

        except Exception as e:
            logger.error("completion_failed", model=model, error=str(e))
            raise ModelUnavailableError(f"Failed to get completion from {model}: {e}") from e

    async def _stream_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        """Stream completion tokens.

        Args:
            messages: Chat messages
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            Individual tokens as they're generated
        """
        try:
            response: Any = await self._router.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("stream_completion_failed", model=model, error=str(e))
            raise ModelUnavailableError(f"Failed to stream from {model}: {e}") from e

    async def is_model_available(self, model: str) -> bool:
        """Check if a model is available and responding.

        Args:
            model: Model name to check

        Returns:
            True if model responds to a minimal test request
        """
        try:
            await self._router.acompletion(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False

    def get_context_window(self, model: str) -> int:
        """Get context window size for a model.

        Args:
            model: Model name

        Returns:
            Maximum context length in tokens
        """
        info = self._model_info.get(model, {})
        context_window = info.get("context_window", 4096)
        return int(context_window)

    def is_local_model(self, model: str) -> bool:
        """Check if model runs locally.

        Args:
            model: Model name

        Returns:
            True if model is local (privacy-safe)
        """
        info = self._model_info.get(model, {})
        is_local = info.get("is_local", False)
        return bool(is_local)

    def get_available_models(self) -> list[str]:
        """Get list of configured model names.

        Returns:
            List of model names (e.g., ['local-fast', 'local-powerful', 'cloud-best'])
        """
        return list(self._model_info.keys())


# Global singleton
_llm_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter | None:
    """Get global LLM router instance.

    Returns:
        LLMRouter instance or None if not initialized
    """
    return _llm_router


def init_llm_router() -> LLMRouter:
    """Initialize global LLM router.

    Returns:
        Initialized LLMRouter instance
    """
    global _llm_router
    _llm_router = LLMRouter()
    return _llm_router
