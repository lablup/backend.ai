from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.logging import BraceStyleAdapter

from ..policy import Policy

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResilienceTimeoutError(BackendAIError):
    """Raised when an operation exceeds its timeout in resilience policy."""

    error_type = "https://api.backend.ai/probs/resilience-timeout"
    error_title = "Resilience timeout exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.TIMEOUT,
        )


@dataclass
class TimeoutArgs:
    """Arguments for TimeoutPolicy."""

    timeout: float


class TimeoutPolicy(Policy):
    """
    Timeout policy that enforces execution time limits.

    Uses asyncio.timeout to cancel operations that exceed the specified duration.
    """

    _timeout: float

    def __init__(self, args: TimeoutArgs) -> None:
        """
        Initialize TimeoutPolicy.

        Args:
            args: Timeout arguments
        """
        self._timeout = args.timeout

    @asynccontextmanager
    async def execute(self) -> AsyncIterator[None]:
        """
        Execute with timeout enforcement.

        Raises:
            ResilienceTimeoutError: If operation exceeds timeout duration
        """
        try:
            async with asyncio.timeout(self._timeout):
                yield
        except TimeoutError as e:
            log.warning("Operation exceeded timeout of {:.3f}s", self._timeout)
            raise ResilienceTimeoutError(f"Operation exceeded timeout of {self._timeout}s") from e
