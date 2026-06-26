"""
Centralized logging configuration.

Provides a factory function that returns consistently formatted loggers
for use across all application modules. Logging level is driven by the
application settings, allowing runtime control via environment variable.
"""

import logging
import sys
from functools import lru_cache

from config.settings import get_settings


def _configure_root_logger() -> None:
    """
    Configure the root logger exactly once.

    Sets up a single StreamHandler writing to stdout with a structured
    format. Stdout is preferred over stderr for container environments
    (Docker, ECS, Lambda) where stdout is captured by the log driver.
    """
    settings = get_settings()

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()

    # Guard: do not add handlers if already configured (e.g., during testing).
    if root_logger.handlers:
        return

    root_logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


@lru_cache(maxsize=None)
def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger, ensuring root configuration is applied first.

    Results are cached so repeated calls with the same name return the
    identical Logger instance without re-running configuration logic.

    Args:
        name: Typically the module's ``__name__``, e.g. ``"api.routes"``.

    Returns:
        logging.Logger: A configured logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Service started")
    """
    _configure_root_logger()
    return logging.getLogger(name)