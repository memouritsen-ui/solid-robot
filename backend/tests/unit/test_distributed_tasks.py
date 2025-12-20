"""Tests for distributed crawl tasks."""

from unittest.mock import MagicMock, patch

import pytest


class TestCrawlUrlTask:
    """Test crawl_url task."""

    def test_task_exists(self) -> None:
        """crawl_url task can be imported."""
        from research_tool.services.distributed.tasks import crawl_url

        assert crawl_url is not None
        assert hasattr(crawl_url, "delay")

    def test_task_returns_success_dict(self) -> None:
        """Task returns success dict with required fields."""
        from research_tool.services.distributed.tasks import crawl_url

        with patch(
            "research_tool.services.distributed.tasks._fetch_url"
        ) as mock_fetch:
            mock_fetch.return_value = {
                "content": "Test content",
                "title": "Test Title",
            }

            result = crawl_url.run(
                url="https://example.com",
                session_id="test-123",
                options={},
            )

            assert result["status"] == "success"
            assert result["url"] == "https://example.com"
            assert "content" in result

    def test_task_returns_failure_on_error(self) -> None:
        """Task returns failure dict on exception."""
        from research_tool.services.distributed.tasks import crawl_url

        with patch(
            "research_tool.services.distributed.tasks._fetch_url"
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")

            result = crawl_url.run(
                url="https://example.com",
                session_id="test-123",
                options={},
            )

            assert result["status"] == "failed"
            assert "error" in result
