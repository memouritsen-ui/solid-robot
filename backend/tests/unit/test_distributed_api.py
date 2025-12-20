"""Tests for distributed crawl API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestCrawlBatchEndpoint:
    """Test /api/crawl/batch endpoint."""

    def test_crawl_batch_requires_urls(self) -> None:
        """Batch endpoint requires urls list."""
        from research_tool.main import app

        client = TestClient(app)
        response = client.post("/api/crawl/batch", json={})

        assert response.status_code == 422  # Validation error

    def test_crawl_batch_empty_urls_returns_empty(self) -> None:
        """Batch endpoint with empty urls returns empty results."""
        from research_tool.main import app

        client = TestClient(app)
        response = client.post(
            "/api/crawl/batch",
            json={"urls": [], "distributed": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []

    def test_crawl_batch_distributed_false_uses_local(self) -> None:
        """Batch endpoint with distributed=False uses local crawler."""
        from research_tool.main import app

        with patch(
            "research_tool.api.routes.crawl.PlaywrightCrawler"
        ) as mock_crawler:
            mock_instance = MagicMock()
            mock_instance.fetch_url.return_value = {
                "content": "Test content",
                "title": "Test",
            }
            mock_crawler.return_value = mock_instance

            client = TestClient(app)
            response = client.post(
                "/api/crawl/batch",
                json={"urls": ["https://example.com"], "distributed": False}
            )

            assert response.status_code == 200
            mock_instance.fetch_url.assert_called_once()

    def test_crawl_batch_distributed_true_uses_coordinator(self) -> None:
        """Batch endpoint with distributed=True uses CrawlCoordinator."""
        from research_tool.main import app

        with patch(
            "research_tool.api.routes.crawl.is_distributed_available"
        ) as mock_available, patch(
            "research_tool.api.routes.crawl.CrawlCoordinator"
        ) as mock_coord:
            mock_available.return_value = True
            mock_instance = MagicMock()
            mock_instance.crawl_many_sync.return_value = [
                {"status": "success", "url": "https://example.com"}
            ]
            mock_instance.get_stats.return_value = {
                "total": 1, "success": 1, "failed": 0, "workers_used": 1
            }
            mock_coord.return_value = mock_instance

            client = TestClient(app)
            response = client.post(
                "/api/crawl/batch",
                json={"urls": ["https://example.com"], "distributed": True}
            )

            assert response.status_code == 200
            mock_coord.assert_called_once()
            mock_instance.crawl_many_sync.assert_called_once()

    def test_crawl_batch_returns_stats(self) -> None:
        """Batch endpoint returns stats with distributed=True."""
        from research_tool.main import app

        with patch(
            "research_tool.api.routes.crawl.is_distributed_available"
        ) as mock_available, patch(
            "research_tool.api.routes.crawl.CrawlCoordinator"
        ) as mock_coord:
            mock_available.return_value = True
            mock_instance = MagicMock()
            mock_instance.crawl_many_sync.return_value = [
                {"status": "success", "url": "https://example.com"}
            ]
            mock_instance.get_stats.return_value = {
                "total": 1, "success": 1, "failed": 0, "workers_used": 1
            }
            mock_coord.return_value = mock_instance

            client = TestClient(app)
            response = client.post(
                "/api/crawl/batch",
                json={"urls": ["https://example.com"], "distributed": True}
            )

            assert response.status_code == 200
            data = response.json()
            assert "stats" in data
            assert data["stats"]["total"] == 1
