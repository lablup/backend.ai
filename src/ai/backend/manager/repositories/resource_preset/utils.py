"""Utility functions for resource preset repository."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Optional, Type

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@contextmanager
def suppress_with_log(
    exceptions: list[Type[BaseException]],
    message: Optional[str] = None,
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
