"""Utility functions for login session repository."""

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
    """
    try:
        yield
    except tuple(exceptions) as e:
        if message:
            log.log(log_level, "{}: {}", message, e)
        else:
            log.log(log_level, "Suppressed exception: {}", e)
