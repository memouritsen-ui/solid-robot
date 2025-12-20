"""Celery application configuration."""

from celery import Celery

from research_tool.services.distributed.config import DistributedConfig

config = DistributedConfig()

app = Celery(
    "solid_robot",
    broker=config.broker_url,
    backend=config.result_backend,
    include=["research_tool.services.distributed.tasks"],
)

# Task configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=config.worker_prefetch_multiplier,
)
