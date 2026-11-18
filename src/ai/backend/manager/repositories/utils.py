"""Shared utility functions for repositories."""

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
<<<<<<< HEAD
        if message:
            log.log(log_level, "{}: {}", message, e)
=======
        if log_level >= logging.ERROR:
            log.exception("exception suppressed", failure_reason=message)
        elif log_level >= logging.WARNING:
            log.warning("exception suppressed", failure_reason=message, exc_info=e)
>>>>>>> 6e1df398 (fix(BAI-780): enable ruff TRY400 and TRY401 and log caught exceptions with logging.exception (#17180))
        else:
            log.log(log_level, "Suppressed exception: {}", e)
