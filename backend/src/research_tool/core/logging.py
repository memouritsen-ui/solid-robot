"""Structured logging configuration."""

import logging
from typing import Any

import structlog


def get_logger(name: str) -> Any:
    """Get a configured structured logger.

    Args:
        name: Logger name, typically __name__.

    Returns:
        Configured structlog logger instance.
    """
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)
