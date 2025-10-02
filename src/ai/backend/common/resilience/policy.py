from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class Policy(ABC):
    """
    Base abstract class for all resilience policies.

    A policy wraps function execution with additional behavior like
    retry, circuit breaking, timeout, or metrics collection.

    Each policy instance maintains its own state (e.g., circuit breaker state,
    failure counts, metrics) and provides an async context manager for execution.

    Policies can be chained together to compose multiple resilience patterns.
    """

    @abstractmethod
    @asynccontextmanager
    async def execute(self) -> AsyncIterator[None]:
        """
        Execute within this policy's context.

        This is an async context manager that wraps the execution.
        Policies can perform setup before yield and cleanup/error handling after.

        Yields:
            None (context manager protocol)

        Example:
            >>> async with policy.execute():
            ...     result = await some_function()
        """
        yield
