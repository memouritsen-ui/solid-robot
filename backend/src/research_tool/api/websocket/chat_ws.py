"""Chat WebSocket handler with streaming LLM responses.

Provides real-time bidirectional communication for chat interactions
with streaming token delivery and conversation history management.
"""

import contextlib
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from research_tool.core.exceptions import ModelUnavailableError
from research_tool.core.logging import get_logger
from research_tool.services.llm import (
    LLMRouter,
    ModelSelector,
    PrivacyMode,
)

logger = get_logger(__name__)


class ChatWebSocketHandler:
    """Handles chat WebSocket connections with streaming LLM responses.

    Features:
    - Streaming token delivery for responsive UX
    - Privacy mode enforcement via ModelSelector
    - Conversation history tracking within session
    - Graceful error handling with client notifications
    """

    def __init__(self) -> None:
        """Initialize handler with router and selector."""
        self._router = LLMRouter()
        self._selector = ModelSelector()
        self._conversation_history: list[dict[str, str]] = []

    async def handle(self, websocket: WebSocket) -> None:
        """Handle WebSocket connection lifecycle.

        Args:
            websocket: FastAPI WebSocket connection
        """
        await websocket.accept()
        logger.info("websocket_connected", client=websocket.client)

        try:
            while True:
                data = await websocket.receive_json()
                await self._process_message(websocket, data)

        except WebSocketDisconnect:
            logger.info("websocket_disconnected", client=websocket.client)
        except Exception as e:
            logger.error("websocket_error", error=str(e))
            await self._send_error(websocket, str(e))

    async def _process_message(
        self, websocket: WebSocket, data: dict[str, Any]
    ) -> None:
        """Process incoming chat message.

        Args:
            websocket: WebSocket connection
            data: Message payload with 'message' and optional 'privacy_mode'
        """
        message = data.get("message", "")
        if not message:
            await self._send_error(websocket, "Empty message received")
            return

        # Parse privacy mode from client
        privacy_mode_str = data.get("privacy_mode", "cloud_allowed")
        try:
            privacy_mode = PrivacyMode(privacy_mode_str)
        except ValueError:
            privacy_mode = PrivacyMode.CLOUD_ALLOWED

        # Add user message to history
        self._conversation_history.append({"role": "user", "content": message})

        # Estimate complexity and select model
        complexity = self._selector.estimate_complexity(
            message,
            context_length=sum(len(m["content"]) for m in self._conversation_history),
        )
        recommendation = self._selector.select(
            task_complexity=complexity,
            privacy_mode=privacy_mode,
        )

        logger.info(
            "model_selected",
            model=recommendation.model,
            complexity=complexity.value,
            privacy_mode=privacy_mode.value,
            reasoning=recommendation.reasoning,
        )

        # Notify client of model selection
        await websocket.send_json({
            "type": "model_info",
            "model": recommendation.model,
            "complexity": complexity.value,
            "privacy_mode": privacy_mode.value,
        })

        # Stream response
        try:
            full_response = await self._stream_response(
                websocket,
                recommendation.model,
            )

            # Add assistant response to history
            self._conversation_history.append({
                "role": "assistant",
                "content": full_response,
            })

            # Signal completion
            await websocket.send_json({
                "type": "done",
                "model": recommendation.model,
                "reasoning": recommendation.reasoning,
            })

        except ModelUnavailableError as e:
            logger.error("model_unavailable", model=recommendation.model, error=str(e))
            await self._send_error(websocket, f"Model unavailable: {e}")
            # Remove failed user message from history
            if self._conversation_history and self._conversation_history[-1]["role"] == "user":
                self._conversation_history.pop()

    async def _stream_response(self, websocket: WebSocket, model: str) -> str:
        """Stream LLM response tokens to client.

        Args:
            websocket: WebSocket connection
            model: Model name to use

        Returns:
            Complete response text
        """
        full_response = ""

        result = await self._router.complete(
            messages=self._conversation_history,
            model=model,
            stream=True,
        )

        # When stream=True, result is always AsyncIterator[str]
        if isinstance(result, str):
            # Should not happen with stream=True, but handle for type safety
            return result

        async for token in result:
            full_response += token
            await websocket.send_json({
                "type": "token",
                "content": token,
            })

        return full_response

    async def _send_error(self, websocket: WebSocket, message: str) -> None:
        """Send error message to client.

        Args:
            websocket: WebSocket connection
            message: Error description
        """
        with contextlib.suppress(Exception):
            await websocket.send_json({
                "type": "error",
                "message": message,
            })

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history.clear()

    def get_history(self) -> list[dict[str, str]]:
        """Get current conversation history.

        Returns:
            List of message dicts with 'role' and 'content'
        """
        return self._conversation_history.copy()


async def chat_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint handler for chat.

    This function is registered as a WebSocket route in main.py.

    Args:
        websocket: FastAPI WebSocket connection
    """
    handler = ChatWebSocketHandler()
    await handler.handle(websocket)
