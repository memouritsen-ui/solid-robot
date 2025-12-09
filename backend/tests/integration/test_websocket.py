"""Integration tests for Chat WebSocket endpoint.

Tests WebSocket connection, message flow, and error handling.
Uses mocked LLM router to avoid actual model calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from research_tool.main import app


class TestWebSocketConnection:
    """Tests for WebSocket connection lifecycle."""

    def test_websocket_connects(self) -> None:
        """WebSocket endpoint should accept connections."""
        client = TestClient(app)
        with client.websocket_connect("/ws/chat"):
            # Connection established successfully
            pass

    def test_websocket_rejects_invalid_path(self) -> None:
        """Invalid WebSocket paths should fail."""
        client = TestClient(app)
        with (
            pytest.raises((WebSocketDisconnect, Exception)),
            client.websocket_connect("/ws/invalid"),
        ):
            pass


class TestWebSocketMessageFlow:
    """Tests for message handling flow."""

    def test_send_message_receives_model_info(self) -> None:
        """Sending message should receive model_info response first."""
        client = TestClient(app)

        async def mock_stream():
            yield "Hello"
            yield " world"

        with patch(
            "research_tool.api.websocket.chat_ws.LLMRouter"
        ) as mock_router_class:
            mock_router = MagicMock()
            mock_router.complete = AsyncMock(return_value=mock_stream())
            mock_router_class.return_value = mock_router

            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_json({
                    "message": "Hello",
                    "privacy_mode": "cloud_allowed",
                })

                # First response should be model_info
                response = websocket.receive_json()
                assert response["type"] == "model_info"
                assert "model" in response
                assert "complexity" in response
                assert "privacy_mode" in response

    def test_send_message_receives_streaming_tokens(self) -> None:
        """Message should receive streaming tokens."""
        client = TestClient(app)

        async def mock_stream():
            yield "Hello"
            yield " "
            yield "world"

        with patch(
            "research_tool.api.websocket.chat_ws.LLMRouter"
        ) as mock_router_class:
            mock_router = MagicMock()
            mock_router.complete = AsyncMock(return_value=mock_stream())
            mock_router_class.return_value = mock_router

            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_json({
                    "message": "Test message",
                    "privacy_mode": "local_only",
                })

                # Skip model_info
                websocket.receive_json()

                # Collect tokens
                tokens = []
                while True:
                    response = websocket.receive_json()
                    if response["type"] == "token":
                        tokens.append(response["content"])
                    elif response["type"] == "done":
                        break

                assert tokens == ["Hello", " ", "world"]

    def test_send_message_receives_done_with_model_info(self) -> None:
        """Done message should include model and reasoning."""
        client = TestClient(app)

        async def mock_stream():
            yield "Response"

        with patch(
            "research_tool.api.websocket.chat_ws.LLMRouter"
        ) as mock_router_class:
            mock_router = MagicMock()
            mock_router.complete = AsyncMock(return_value=mock_stream())
            mock_router_class.return_value = mock_router

            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_json({
                    "message": "Test",
                    "privacy_mode": "cloud_allowed",
                })

                # Collect all messages until done
                done_response = None
                while True:
                    response = websocket.receive_json()
                    if response["type"] == "done":
                        done_response = response
                        break

                assert done_response is not None
                assert "model" in done_response
                assert "reasoning" in done_response


class TestWebSocketPrivacyMode:
    """Tests for privacy mode handling."""

    def test_local_only_mode_passed_to_selector(self) -> None:
        """LOCAL_ONLY privacy mode should be respected."""
        client = TestClient(app)

        async def mock_stream():
            yield "Local response"

        with patch(
            "research_tool.api.websocket.chat_ws.LLMRouter"
        ) as mock_router_class:
            mock_router = MagicMock()
            mock_router.complete = AsyncMock(return_value=mock_stream())
            mock_router_class.return_value = mock_router

            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_json({
                    "message": "Test with confidential data",
                    "privacy_mode": "local_only",
                })

                # Check model_info indicates local model
                response = websocket.receive_json()
                assert response["type"] == "model_info"
                assert response["privacy_mode"] == "local_only"
                # Model should be local (not cloud)
                assert "cloud" not in response["model"]

    def test_invalid_privacy_mode_defaults_to_cloud_allowed(self) -> None:
        """Invalid privacy mode should default to cloud_allowed."""
        client = TestClient(app)

        async def mock_stream():
            yield "Response"

        with patch(
            "research_tool.api.websocket.chat_ws.LLMRouter"
        ) as mock_router_class:
            mock_router = MagicMock()
            mock_router.complete = AsyncMock(return_value=mock_stream())
            mock_router_class.return_value = mock_router

            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_json({
                    "message": "Test",
                    "privacy_mode": "invalid_mode",
                })

                response = websocket.receive_json()
                assert response["type"] == "model_info"
                assert response["privacy_mode"] == "cloud_allowed"


class TestWebSocketErrorHandling:
    """Tests for error handling."""

    def test_empty_message_returns_error(self) -> None:
        """Empty message should return error response."""
        client = TestClient(app)

        with client.websocket_connect("/ws/chat") as websocket:
            websocket.send_json({
                "message": "",
                "privacy_mode": "cloud_allowed",
            })

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "empty" in response["message"].lower()

    def test_model_error_returns_error_response(self) -> None:
        """Model failure should return error to client."""
        client = TestClient(app)

        from research_tool.core.exceptions import ModelUnavailableError

        with patch(
            "research_tool.api.websocket.chat_ws.LLMRouter"
        ) as mock_router_class:
            mock_router = MagicMock()
            mock_router.complete = AsyncMock(
                side_effect=ModelUnavailableError("Model failed")
            )
            mock_router_class.return_value = mock_router

            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_json({
                    "message": "Test",
                    "privacy_mode": "cloud_allowed",
                })

                # Skip model_info
                websocket.receive_json()

                # Next should be error
                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "unavailable" in response["message"].lower()


class TestWebSocketConversationHistory:
    """Tests for conversation history management."""

    def test_multiple_messages_maintain_history(self) -> None:
        """Multiple messages should maintain conversation context."""
        client = TestClient(app)

        call_count = 0
        messages_received: list[list[dict]] = []

        async def mock_stream():
            yield "Response"

        async def capture_complete(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            messages_received.append(messages.copy())
            return mock_stream()

        with patch(
            "research_tool.api.websocket.chat_ws.LLMRouter"
        ) as mock_router_class:
            mock_router = MagicMock()
            mock_router.complete = AsyncMock(side_effect=capture_complete)
            mock_router_class.return_value = mock_router

            with client.websocket_connect("/ws/chat") as websocket:
                # First message
                websocket.send_json({"message": "First message"})
                # Drain responses
                while True:
                    resp = websocket.receive_json()
                    if resp["type"] == "done":
                        break

                # Second message
                websocket.send_json({"message": "Second message"})
                while True:
                    resp = websocket.receive_json()
                    if resp["type"] == "done":
                        break

        # Verify history growth
        assert call_count == 2
        # First call should have 1 message (user)
        assert len(messages_received[0]) == 1
        # Second call should have 3 messages (user, assistant, user)
        assert len(messages_received[1]) == 3
        assert messages_received[1][0]["role"] == "user"
        assert messages_received[1][1]["role"] == "assistant"
        assert messages_received[1][2]["role"] == "user"
