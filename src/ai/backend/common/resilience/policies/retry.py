from __future__ import annotations

import enum
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from ai.backend.logging import BraceStyleAdapter

from ..policy import Policy

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)


class RetryPolicy(Policy):
    """
    Retry policy that automatically retries failed operations.

    Built on top of tenacity library, providing async context manager interface
    for consistent policy composition.

    Only retries exceptions that match the specified retryable exception types.
    All other exceptions propagate immediately without retry.

    Supports both fixed delay and exponential backoff strategies.
    """

    _max_retries: int
    _retry_delay: float
    _backoff_strategy: BackoffStrategy
    _max_delay: float
    _retryable_exceptions: tuple[type[Exception], ...]

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
        self._retryable_exceptions = args.retryable_exceptions

    @asynccontextmanager
    async def execute(self) -> AsyncIterator[None]:
        """
        Execute with retry logic using tenacity.

        Automatically retries on retryable exceptions up to max_retries times.
        Non-retryable exceptions propagate immediately.
        """
        # Build tenacity retry configuration
        if self._backoff_strategy == BackoffStrategy.EXPONENTIAL:
            wait_strategy = wait_exponential(
                multiplier=self._retry_delay,
                min=self._retry_delay,
                max=self._max_delay,
            )
        else:
            wait_strategy = wait_fixed(self._retry_delay)

        stop_strategy = stop_after_attempt(self._max_retries)
        retry_strategy = retry_if_exception_type(self._retryable_exceptions)

        # Use tenacity's AsyncRetrying
        async for attempt in AsyncRetrying(
            wait=wait_strategy,
            stop=stop_strategy,
            retry=retry_strategy,
            reraise=True,
        ):
            with attempt:
                if attempt.retry_state.attempt_number > 1:
                    log.debug(
                        "Retry attempt {}/{}",
                        attempt.retry_state.attempt_number,
                        self._max_retries,
                    )
                yield
