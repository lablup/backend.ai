from __future__ import annotations

import enum
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Optional, ParamSpec, TypeVar

from tenacity import (
    wait_exponential,
    wait_fixed,
)
from tenacity.wait import wait_base

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    UnreachableError,
)
from ai.backend.logging import BraceStyleAdapter

from ..policy import Policy

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

P = ParamSpec("P")
R = TypeVar("R")


class ResilienceRetryError(BackendAIError):
    """Raised when retry logic encounters an unexpected error."""

    error_type = "https://api.backend.ai/probs/resilience-retry-error"
    error_title = "Resilience retry error."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class BackoffStrategy(enum.StrEnum):
    """Backoff strategy for retry policies."""

    FIXED = "fixed"
    EXPONENTIAL = "exponential"


@dataclass
class RetryArgs:
    """Arguments for RetryPolicy."""

    max_retries: int = 3
    retry_delay: float = 0.1
    backoff_strategy: BackoffStrategy = BackoffStrategy.FIXED
    max_delay: float = 10.0
    non_retryable_exceptions: tuple[type[Exception], ...] = ()


class RetryPolicy(Policy):
    """
    Retry policy that automatically retries failed operations.

    Built on top of tenacity library, providing async context manager interface
    for consistent policy composition.

    Retries all exceptions except those specified in non_retryable_exceptions.
    Non-retryable exceptions (e.g., BackendAIError) propagate immediately without retry.

    Supports both fixed delay and exponential backoff strategies.
    """

    _max_retries: int
    _retry_delay: float
    _backoff_strategy: BackoffStrategy
    _max_delay: float
    _non_retryable_exceptions: tuple[type[Exception], ...]

    def __init__(self, args: RetryArgs) -> None:
        """
        Initialize RetryPolicy.

        Args:
            args: Retry arguments
        """
        self._max_retries = args.max_retries
        self._retry_delay = args.retry_delay
        self._backoff_strategy = args.backoff_strategy
        self._max_delay = args.max_delay
        self._non_retryable_exceptions = args.non_retryable_exceptions

    async def execute(
        self,
        next_call: Callable[P, Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        """
        Execute with retry logic using tenacity.

        Automatically retries all exceptions except non-retryable ones.
        Non-retryable exceptions propagate immediately without retry.
        """
        last_exception: Optional[Exception] = None
        for i in range(1, self._max_retries + 1):
            try:
                return await next_call(*args, **kwargs)
            except self._non_retryable_exceptions as e:
                log.debug("non-retryable exception encountered: {}", e)
                raise
            except Exception as e:
                last_exception = e
                log.debug(
                    "retryable exception encountered: {}, attempt {}/{}", e, i, self._max_retries
                )
        if last_exception is not None:
            raise last_exception
        raise UnreachableError("RetryPolicy failed without capturing an exception.")

    def _build_wait_strategy(self) -> wait_base:
        """Build tenacity wait strategy based on backoff configuration."""
        match self._backoff_strategy:
            case BackoffStrategy.EXPONENTIAL:
                return wait_exponential(
                    multiplier=self._retry_delay,
                    min=self._retry_delay,
                    max=self._max_delay,
                )
            case _:
                return wait_fixed(self._retry_delay)
