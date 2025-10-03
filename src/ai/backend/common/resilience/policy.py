from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class Policy(ABC):
    """
    Base abstract class for all resilience policies.

    A policy wraps function execution with additional behavior like
    retry, circuit breaking, timeout, or metrics collection.

    Each policy instance maintains its own state (e.g., circuit breaker state,
    failure counts, metrics) and provides middleware-style function wrapping.

    Policies can be chained together to compose multiple resilience patterns
    using the middleware pattern where each policy wraps the next one.
    """

    @abstractmethod
    async def execute(
        self,
        next_call: Callable[P, Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        """
        Execute the next callable with this policy's behavior.

        This method implements the middleware pattern, where each policy
        can perform actions before/after calling the next policy or the final function.

        Args:
            next_call: The next callable in the chain (policy or final function)
            *args: Positional arguments to pass to next_call
            **kwargs: Keyword arguments to pass to next_call

        Returns:
            Result from next_call

        Example:
            >>> async def execute(self, next_call, *args, **kwargs):
            ...     # Before logic
            ...     result = await next_call(*args, **kwargs)
            ...     # After logic
            ...     return result
        """
        raise NotImplementedError
