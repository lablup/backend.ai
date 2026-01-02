from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar

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

P = ParamSpec("P")
R = TypeVar("R")


class ResilienceTimeoutError(BackendAIError):
    """Raised when an operation exceeds its timeout in resilience policy."""

    error_type = "https://api.backend.ai/probs/resilience-timeout"
    error_title = "Resilience timeout exceeded."

    def error_code(self) -> ErrorCode:
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

    async def execute(
        self,
        next_call: Callable[P, Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        """
        Execute with timeout enforcement.

        Raises:
            ResilienceTimeoutError: If operation exceeds timeout duration
        """
        try:
            async with asyncio.timeout(self._timeout):
                return await next_call(*args, **kwargs)
        except TimeoutError as e:
            log.warning("Operation exceeded timeout of {:.3f}s", self._timeout)
            raise ResilienceTimeoutError(f"Operation exceeded timeout of {self._timeout}s") from e
