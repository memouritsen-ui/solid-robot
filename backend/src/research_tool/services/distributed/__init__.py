"""Distributed crawling with Celery + Redis."""

from research_tool.services.distributed.config import DistributedConfig

_config: DistributedConfig | None = None


def get_distributed_config() -> DistributedConfig:
    """Get distributed configuration singleton."""
    global _config
    if _config is None:
        _config = DistributedConfig()
    return _config


def is_distributed_available() -> bool:
    """Check if Redis is reachable."""
    try:
        import redis

        config = get_distributed_config()
        client = redis.from_url(config.broker_url)
        client.ping()
        return True
    except Exception:
        return False


__all__ = [
    "DistributedConfig",
    "get_distributed_config",
    "is_distributed_available",
]
