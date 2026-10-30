"""Utility functions for resource preset repository."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


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
        if log_level >= logging.ERROR:
            log.error("exception suppressed", failure_reason=message, exc_info=e)
        elif log_level >= logging.WARNING:
            log.warning("exception suppressed", failure_reason=message, exc_info=e)
        else:
            log.debug("exception suppressed: {}", e, failure_reason=message)
