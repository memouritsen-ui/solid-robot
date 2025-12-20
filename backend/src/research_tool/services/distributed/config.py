"""Configuration for distributed crawling."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class DistributedConfig(BaseSettings):
    """Distributed crawling configuration."""

    model_config = SettingsConfigDict(env_prefix="CELERY_")

    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    task_rate_limit: str = "10/m"
    task_max_retries: int = 3
    task_retry_backoff: int = 60
    worker_concurrency: int = 1
    worker_prefetch_multiplier: int = 1
