"""WebSocket handler for research progress updates."""

from typing import Any

from fastapi import WebSocket

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


class ProgressWebSocketHandler:
    """Handle WebSocket connections for research progress streaming.

    Sends real-time progress updates during research workflow:
    - Phase transitions (clarify → plan → collect → etc.)
    - Source query results
    - Entity/fact extraction updates
    - Saturation metrics
    - Final report availability
    """

    def __init__(self) -> None:
        """Initialize progress handler."""
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Accept WebSocket connection for a research session.

        Args:
            session_id: Research session ID to monitor
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket

        logger.info(
            "progress_ws_connected",
            session_id=session_id
        )

        # Send initial connection confirmation
        await self.send_update(
            session_id,
            {
                "type": "connected",
                "session_id": session_id,
                "message": "Connected to research progress stream"
            }
        )

    async def disconnect(self, session_id: str) -> None:
        """Close WebSocket connection.

        Args:
            session_id: Research session ID
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(
                "progress_ws_disconnected",
                session_id=session_id
            )

    async def send_update(self, session_id: str, data: dict[str, Any]) -> None:
        """Send progress update to connected client.

        Args:
            session_id: Research session ID
            data: Progress data to send
        """
        if session_id not in self.active_connections:
            return

        websocket = self.active_connections[session_id]

        try:
            await websocket.send_json(data)

            logger.debug(
                "progress_ws_update_sent",
                session_id=session_id,
                update_type=data.get("type")
            )

        except Exception as e:
            logger.error(
                "progress_ws_send_failed",
                session_id=session_id,
                error=str(e)
            )
            # Remove broken connection
            await self.disconnect(session_id)

    async def send_phase_update(
        self,
        session_id: str,
        phase: str,
        description: str
    ) -> None:
        """Send phase transition update.

        Args:
            session_id: Research session ID
            phase: New phase name
            description: Human-readable phase description
        """
        await self.send_update(
            session_id,
            {
                "type": "phase",
                "phase": phase,
                "description": description
            }
        )

    async def send_source_update(
        self,
        session_id: str,
        source: str,
        result_count: int
    ) -> None:
        """Send source query result update.

        Args:
            session_id: Research session ID
            source: Source name
            result_count: Number of results found
        """
        await self.send_update(
            session_id,
            {
                "type": "source",
                "source": source,
                "result_count": result_count
            }
        )

    async def send_metrics_update(
        self,
        session_id: str,
        metrics: dict[str, Any]
    ) -> None:
        """Send saturation metrics update.

        Args:
            session_id: Research session ID
            metrics: Saturation metrics
        """
        await self.send_update(
            session_id,
            {
                "type": "metrics",
                "metrics": metrics
            }
        )

    async def send_completion(
        self,
        session_id: str,
        report_available: bool
    ) -> None:
        """Send research completion notification.

        Args:
            session_id: Research session ID
            report_available: Whether final report is ready
        """
        await self.send_update(
            session_id,
            {
                "type": "complete",
                "report_available": report_available
            }
        )

    async def send_error(
        self,
        session_id: str,
        error_message: str
    ) -> None:
        """Send error notification.

        Args:
            session_id: Research session ID
            error_message: Error description
        """
        await self.send_update(
            session_id,
            {
                "type": "error",
                "error": error_message
            }
        )


# Global progress handler instance
progress_handler = ProgressWebSocketHandler()
