"""Tests for Celery app configuration."""

import pytest


class TestCeleryApp:
    """Test Celery application setup."""

    def test_celery_app_exists(self) -> None:
        """Celery app can be imported."""
        from research_tool.services.distributed.celery_app import app

        assert app is not None
        assert app.main == "solid_robot"

    def test_celery_app_has_broker_configured(self) -> None:
        """Celery app has broker URL configured."""
        from research_tool.services.distributed.celery_app import app

        assert "redis://" in app.conf.broker_url

    def test_celery_app_has_result_backend(self) -> None:
        """Celery app has result backend configured."""
        from research_tool.services.distributed.celery_app import app

        assert "redis://" in app.conf.result_backend
