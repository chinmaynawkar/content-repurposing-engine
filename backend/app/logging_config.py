"""Structured logging configuration for the Content Repurposing API.

Uses structlog for JSON output in production (log aggregators) and
human-readable colored output in development.
"""

import logging
import sys
from typing import Any

import structlog

from app.config import settings


def _get_log_level() -> int:
    """Resolve log level from config. Defaults to DEBUG when DEBUG=True."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    if settings.DEBUG and level > logging.DEBUG:
        return logging.DEBUG
    return level


def _is_production() -> bool:
    """Use JSON logs in production; pretty console in development."""
    return settings.ENVIRONMENT.lower() in ("production", "prod")


def configure_logging() -> None:
    """Configure structlog and standard library logging. Call once at startup."""
    log_level = _get_log_level()
    use_json = _is_production()

    shared_processors: list[Any] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if use_json:
        processors = shared_processors + [
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root logger to use structlog output
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if root_logger.handlers:
        root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    root_logger.addHandler(handler)

    # Reduce uvicorn/uvloop noise in development
    if not use_json:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a configured structlog logger. Use __name__ for module name."""
    return structlog.get_logger(name)
