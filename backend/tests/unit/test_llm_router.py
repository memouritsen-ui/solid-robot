"""Tests for LLMRouter - model routing with fallback support.

These tests use mocking since actual model calls require running services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_tool.services.llm import LLMRouter


class TestLLMRouterConfiguration:
    """Tests for router configuration and model info."""

    def test_router_initializes(self) -> None:
        """Router should initialize without errors."""
        router = LLMRouter()
        assert router is not None

    def test_get_available_models(self) -> None:
        """Should return configured model names."""
        router = LLMRouter()
        models = router.get_available_models()
        assert "local-fast" in models
        assert "local-powerful" in models
        assert "cloud-best" in models

    def test_get_context_window(self) -> None:
        """Should return context window for known models."""
        router = LLMRouter()
        # Local models have 128k context
        assert router.get_context_window("local-fast") == 128000
        assert router.get_context_window("local-powerful") == 128000
        # Cloud model has 200k context
        assert router.get_context_window("cloud-best") == 200000

    def test_get_context_window_unknown_model(self) -> None:
        """Unknown models should return default context window."""
        router = LLMRouter()
        assert router.get_context_window("unknown-model") == 4096

    def test_is_local_model(self) -> None:
        """Should correctly identify local vs cloud models."""
        router = LLMRouter()
        assert router.is_local_model("local-fast") is True
        assert router.is_local_model("local-powerful") is True
        assert router.is_local_model("cloud-best") is False

    def test_is_local_model_unknown(self) -> None:
        """Unknown models should default to not local (safe default)."""
        router = LLMRouter()
        assert router.is_local_model("unknown-model") is False


class TestLLMRouterComplete:
    """Tests for completion functionality (mocked)."""

    @pytest.mark.asyncio
    async def test_complete_returns_string(self) -> None:
        """Non-streaming complete should return string."""
        router = LLMRouter()

        # Mock the internal router's acompletion
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        with patch.object(router._router, "acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response
            result = await router.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="local-fast",
                stream=False,
            )

            assert result == "Test response"
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_with_custom_params(self) -> None:
        """Complete should pass through temperature and max_tokens."""
        router = LLMRouter()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = None

        with patch.object(router._router, "acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response
            await router.complete(
                messages=[{"role": "user", "content": "Test"}],
                model="local-powerful",
                temperature=0.5,
                max_tokens=1000,
            )

            mock.assert_called_once()
            call_kwargs = mock.call_args[1]
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_tokens"] == 1000
            assert call_kwargs["model"] == "local-powerful"

    @pytest.mark.asyncio
    async def test_complete_handles_model_error(self) -> None:
        """Should raise ModelUnavailableError on failures."""
        from research_tool.core.exceptions import ModelUnavailableError

        router = LLMRouter()

        with patch.object(router._router, "acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Connection refused")

            with pytest.raises(ModelUnavailableError) as exc_info:
                await router.complete(
                    messages=[{"role": "user", "content": "Test"}],
                    model="local-fast",
                )

            assert "Connection refused" in str(exc_info.value)


class TestLLMRouterStreaming:
    """Tests for streaming completion."""

    @pytest.mark.asyncio
    async def test_stream_returns_async_iterator(self) -> None:
        """Streaming should return async iterator of tokens."""
        router = LLMRouter()

        # Create mock async generator
        async def mock_stream():
            chunks = ["Hello", " ", "world", "!"]
            for content in chunks:
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta.content = content
                yield chunk

        with patch.object(router._router, "acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_stream()

            result = await router.complete(
                messages=[{"role": "user", "content": "Test"}],
                model="local-fast",
                stream=True,
            )

            # Collect tokens
            tokens = []
            async for token in result:
                tokens.append(token)

            assert tokens == ["Hello", " ", "world", "!"]


class TestLLMRouterAvailability:
    """Tests for model availability checking."""

    @pytest.mark.asyncio
    async def test_is_model_available_returns_true_on_success(self) -> None:
        """Should return True when model responds."""
        router = LLMRouter()

        with patch.object(router._router, "acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = MagicMock()
            result = await router.is_model_available("local-fast")
            assert result is True

    @pytest.mark.asyncio
    async def test_is_model_available_returns_false_on_failure(self) -> None:
        """Should return False when model fails."""
        router = LLMRouter()

        with patch.object(router._router, "acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Model not loaded")
            result = await router.is_model_available("local-fast")
            assert result is False
