"""Utility functions for resource preset repository."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@contextmanager
def suppress_with_log(
    exceptions: list[type[BaseException]],
    message: str | None = None,
    log_level: int = logging.WARNING,
) -> Generator[None, None, None]:
    """
    Context manager that suppresses specified exceptions and logs them.

    Args:
        exceptions: List of exception types to suppress
        message: Optional custom message to log with the exception
        log_level: Logging level to use (default: WARNING)
    """
    try:
        yield
    except tuple(exceptions) as e:
        if message:
            log.log(log_level, "{}: {}", message, e)
        else:
            log.log(log_level, "Suppressed exception: {}", e)
